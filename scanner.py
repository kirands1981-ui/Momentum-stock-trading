"""
Main Scanner Module - Orchestrates the momentum scanning process
"""

import argparse
import logging
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional

import pandas as pd

from config import (
    PRICE_INCREASE_THRESHOLD,
    VOLUME_MULTIPLIER,
    ALERT_DEDUPLICATION_WINDOW,
    ALERT_HISTORY_FILE,
    LOG_FILE,
    OUTPUT_ALERT_FILE,
    MIN_PRICE,
    MAX_PRICE,
    MIN_MARKET_CAP,
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
)

from data_fetcher import StockDataFetcher, NewsAnalyzer
from analyzer import MomentumDetector
from alert_system import AlertManager, AlertFormatter, AlertLogger
from utils import WebUllLinkGenerator, DataFormatter
from chart_generator import create_momentum_chart
from alert_notifier import AlertNotifier, SystemNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MomentumScanner:
    """Main scanner for momentum stocks"""

    def __init__(self, email_config: Dict = None, webhook_url: str = None, 
                 recipient_email: str = None, enable_desktop_alerts: bool = False):
        self.data_fetcher = StockDataFetcher()
        self.momentum_detector = MomentumDetector(
            volume_multiplier=VOLUME_MULTIPLIER,
            price_threshold=PRICE_INCREASE_THRESHOLD
        )
        self.alert_manager = AlertManager(ALERT_HISTORY_FILE)
        self.alert_logger = AlertLogger(LOG_FILE)
        self.alert_notifier = AlertNotifier(email_config, webhook_url)
        self.recipient_email = recipient_email
        self.enable_desktop_alerts = enable_desktop_alerts
        self.scanned_stocks = 0
        self.momentum_stocks = []
        self._counter_lock = Lock()   # guards scanned_stocks
        self._file_lock = Lock()      # guards alerts JSON file

    @staticmethod
    def create_dry_run_dataset() -> pd.DataFrame:
        """Create deterministic sample candles for exercising the alert pipeline."""
        periods = 40
        timestamps = pd.date_range(end=datetime.now(), periods=periods, freq="h")
        rows = []
        current_price = 100.0

        for index, timestamp in enumerate(timestamps):
            open_price = current_price
            if index == periods - 1:
                close_price = 112.0
                high_price = 113.4
                low_price = 99.8
                volume = 12_500_000
            else:
                step = ((index % 5) - 2) * 0.12
                close_price = round(open_price * (1 + step / 100), 2)
                high_price = max(open_price, close_price) * 1.002
                low_price = min(open_price, close_price) * 0.998
                volume = 1_500_000 + (index % 4) * 125_000

            rows.append({
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': int(volume),
            })
            current_price = close_price

        return pd.DataFrame(rows, index=timestamps)

    def scan_stock(self, ticker: str) -> Optional[Dict]:
        """Scan a single stock for momentum"""
        try:
            # Validate and get basic data
            if not self.data_fetcher.check_stock_exists(ticker):
                return None

            # Get required data
            hourly_data = self.data_fetcher.get_stock_data(ticker, period="5d")
            if hourly_data is None or hourly_data.empty:
                return None

            previous_close = self.data_fetcher.get_previous_close(ticker)
            if previous_close is None or previous_close <= 0:
                return None

            avg_30day_volume = self.data_fetcher.get_30day_avg_volume(ticker)
            if avg_30day_volume is None or avg_30day_volume <= 0:
                return None

            # Check price and volume filters
            stock_info = self.data_fetcher.get_stock_info(ticker)
            if stock_info:
                current_price = stock_info.get('currentPrice') or stock_info.get('regularMarketPrice')
                if current_price and not (MIN_PRICE <= current_price <= MAX_PRICE):
                    return None

            # Get news data
            news = self.data_fetcher.search_news(ticker)
            has_positive_news, news_title, news_url = NewsAnalyzer.has_positive_news(news)
            pr_summary = NewsAnalyzer.summarize_news(news)

            # Detect momentum
            momentum_result = self.momentum_detector.detect_momentum(
                ticker=ticker,
                hourly_data=hourly_data,
                previous_close=previous_close,
                avg_30day_volume=avg_30day_volume,
                has_positive_news=has_positive_news,
                pr_link=news_url,
                pr_summary=pr_summary
            )

            return momentum_result

        except Exception as e:
            logger.debug(f"Error scanning {ticker}: {e}")
            return None

    def process_momentum_signal(
        self,
        momentum_result: Dict,
        hourly_data: Optional[pd.DataFrame] = None,
        skip_deduplication: bool = False,
    ) -> bool:
        """Process a momentum signal and generate alert if needed"""
        
        if not momentum_result or not momentum_result.get('momentum_detected'):
            return False

        ticker = momentum_result['ticker']

        # Check deduplication
        if not skip_deduplication and not self.alert_manager.should_alert(ticker, ALERT_DEDUPLICATION_WINDOW):
            return False

        # Record and alert
        self.alert_manager.record_alert(ticker, momentum_result)
        self.momentum_stocks.append(momentum_result)

        # Log alert
        self.alert_logger.log_alert(momentum_result)

        # Generate and print alert
        self._generate_alert_output(momentum_result, ticker, hourly_data)

        return True

    def _generate_alert_output(
        self,
        momentum_result: Dict,
        ticker: str,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> None:
        """Generate alert output in multiple formats"""

        # Console output
        console_alert = AlertFormatter.format_console_alert(momentum_result)
        print(console_alert)
        logger.info(console_alert)

        # WebUll links
        webull_app = WebUllLinkGenerator.get_app_link(ticker)
        webull_web = WebUllLinkGenerator.get_web_link(ticker)

        # JSON output
        json_alert = AlertFormatter.format_json_alert(momentum_result, webull_web, webull_app)
        self._append_to_alerts_file(json_alert)

        # Generate chart
        chart_path = None
        try:
            chart_data = hourly_data
            if chart_data is None:
                chart_data = self.data_fetcher.get_stock_data(ticker, period="5d")

            if chart_data is not None and not chart_data.empty:
                chart_path = create_momentum_chart(
                    ticker=ticker,
                    hourly_data=chart_data,
                    signal_type=momentum_result['buy_type'],
                    momentum_score=momentum_result['score']
                )
                logger.info(f"Chart generated: {chart_path}")
        except Exception as e:
            logger.warning(f"Could not generate chart for {ticker}: {e}")

        # Send notifications
        self._send_notifications(momentum_result, chart_path, ticker)

        # HTML optional (for email)
        html_alert = AlertFormatter.format_html_alert(momentum_result, webull_web, webull_app)
        logger.debug(f"HTML Alert for {ticker}:\n{html_alert}")

    def _send_notifications(self, momentum_result: Dict, chart_path: Optional[str],
                          ticker: str) -> None:
        """Send real-time alerts via configured channels"""
        
        try:
            # Desktop notification
            if self.enable_desktop_alerts:
                message = (
                    f"{momentum_result['buy_type']}\n"
                    f"Price: +{momentum_result['details']['price_increase_percent']:.2f}%\n"
                    f"Volume: {momentum_result['details']['relative_volume']:.1f}x"
                )
                SystemNotifier.notify_desktop(f"🚀 {ticker}", message)

            # Email/Webhook notifications
            results = self.alert_notifier.send_alert(
                momentum_result,
                recipient_email=self.recipient_email,
                chart_path=chart_path
            )

            channels = [ch for ch, success in results.items() if success]
            if channels:
                logger.info(f"Alert sent via: {', '.join(channels)}")

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    def _append_to_alerts_file(self, alert_json: Dict) -> None:
        """Append alert to JSON alerts file (thread-safe)."""
        try:
            os.makedirs(os.path.dirname(OUTPUT_ALERT_FILE) or '.', exist_ok=True)

            with self._file_lock:
                alerts = []
                if os.path.exists(OUTPUT_ALERT_FILE):
                    with open(OUTPUT_ALERT_FILE, 'r') as f:
                        alerts = json.load(f)

                alerts.append(alert_json)

                with open(OUTPUT_ALERT_FILE, 'w') as f:
                    json.dump(alerts, f, indent=2)

        except Exception as e:
            logger.error(f"Error writing to alerts file: {e}")

    def scan_exchange(self, stock_list: List[str], workers: int = 10) -> List[Dict]:
        """Scan a list of stocks in parallel, process signals serially."""
        total = len(stock_list)
        logger.info(f"Starting scan of {total} stocks ({workers} workers)...")
        self.momentum_stocks = []
        completed = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_ticker = {
                executor.submit(self.scan_stock, ticker): ticker
                for ticker in stock_list
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    momentum_result = future.result()
                    if momentum_result:
                        self.process_momentum_signal(momentum_result)
                except Exception as e:
                    logger.debug(f"Error processing {ticker}: {e}")

                with self._counter_lock:
                    self.scanned_stocks += 1
                    completed += 1

                if completed % 20 == 0 or completed == total:
                    logger.info(f"Progress: {completed}/{total} stocks scanned...")

        return self.momentum_stocks

    def scan_all_exchanges(self, workers: int = 10) -> Dict:
        """Scan all exchanges (NASDAQ, NYSE, AMEX) using parallel workers."""
        logger.info("=" * 60)
        logger.info(f"SCAN START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        results = {
            'nasdaq': [],
            'nyse': [],
            'amex': [],
            'total_scanned': 0,
            'total_momentum': 0,
            'institutional_buys': 0,
            'retail_buys': 0
        }

        # NASDAQ scan
        logger.info("\nScanning NASDAQ...")
        nasdaq_stocks = self.data_fetcher.get_nasdaq_stocks()
        results['nasdaq'] = self.scan_exchange(nasdaq_stocks, workers=workers)

        # NYSE scan
        logger.info("\nScanning NYSE...")
        nyse_stocks = self.data_fetcher.get_nyse_stocks()
        results['nyse'] = self.scan_exchange(nyse_stocks, workers=workers)

        # AMEX scan
        logger.info("\nScanning AMEX...")
        amex_stocks = self.data_fetcher.get_amex_stocks()
        results['amex'] = self.scan_exchange(amex_stocks, workers=workers)

        # Calculate totals
        results['total_scanned'] = self.scanned_stocks
        total_momentum = len(results['nasdaq']) + len(results['nyse']) + len(results['amex'])
        results['total_momentum'] = total_momentum

        for exchange_results in [results['nasdaq'], results['nyse'], results['amex']]:
            for item in exchange_results:
                if item.get('buy_type') == 'INSTITUTIONAL_BUY':
                    results['institutional_buys'] += 1
                elif item.get('buy_type') == 'RETAIL_BUY':
                    results['retail_buys'] += 1

        # Log summary
        self._log_scan_summary(results)

        logger.info("=" * 60)
        logger.info(f"SCAN COMPLETE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        return results

    def run_dry_run(self, ticker: str = "DRYRUN") -> Dict:
        """Exercise the scanner pipeline without live market requests."""
        hourly_data = self.create_dry_run_dataset()
        previous_close = 100.0
        avg_30day_volume = 1_800_000.0

        momentum_result = self.momentum_detector.detect_momentum(
            ticker=ticker,
            hourly_data=hourly_data,
            previous_close=previous_close,
            avg_30day_volume=avg_30day_volume,
            has_positive_news=False,
            pr_link=None,
            pr_summary=None,
        )

        self.process_momentum_signal(
            momentum_result,
            hourly_data=hourly_data,
            skip_deduplication=True,
        )
        return momentum_result

    def _log_scan_summary(self, results: Dict) -> None:
        """Log scan summary"""
        summary_lines = [
            "",
            "=" * 60,
            "SCAN SUMMARY",
            "=" * 60,
            f"Total Stocks Scanned: {results['total_scanned']}",
            f"Total Momentum Found: {results['total_momentum']}",
            f"  - Institutional Buys: {results['institutional_buys']}",
            f"  - Retail Buys: {results['retail_buys']}",
            f"NASDAQ Alerts: {len(results['nasdaq'])}",
            f"NYSE Alerts: {len(results['nyse'])}",
            f"AMEX Alerts: {len(results['amex'])}",
            "=" * 60,
            ""
        ]

        summary = "\n".join(summary_lines)
        print(summary)
        logger.info(summary)

        self.alert_logger.log_scan_summary(
            results['total_scanned'],
            results['total_momentum'],
            results['institutional_buys'],
            results['retail_buys']
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Momentum stock scanner")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the alert pipeline with synthetic data instead of live Yahoo Finance requests.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        metavar="N",
        help="Number of parallel worker threads for scanning (default: 10).",
    )
    parser.add_argument(
        "--email",
        metavar="ADDRESS",
        default=None,
        help="Recipient email for alerts (overrides EMAIL_RECIPIENT env var).",
    )
    args = parser.parse_args()

    recipient = args.email or EMAIL_RECIPIENT or None
    email_cfg = None
    if EMAIL_SENDER and EMAIL_PASSWORD:
        email_cfg = {
            "enabled": True,
            "smtp_server": EMAIL_SMTP_SERVER,
            "smtp_port": EMAIL_SMTP_PORT,
            "sender_email": EMAIL_SENDER,
            "sender_password": EMAIL_PASSWORD,
        }
        if recipient:
            logger.info(f"Email alerts enabled → {recipient}")
        else:
            logger.warning("EMAIL_SENDER/EMAIL_PASSWORD set but no recipient — pass --email or set EMAIL_RECIPIENT in .env")
    else:
        logger.warning("Email not configured. Set EMAIL_SENDER + EMAIL_PASSWORD in .env to receive alerts.")

    scanner = MomentumScanner(email_config=email_cfg, recipient_email=recipient)

    try:
        if args.dry_run:
            result = scanner.run_dry_run()
            print("\nDry run complete!")
            print(f"Momentum detected: {result['momentum_detected']}")
            print(f"Buy type: {result['buy_type']}")
            print(f"Score: {result['score']:.1f}/100")
            return

        # Run full scan
        results = scanner.scan_all_exchanges(workers=args.workers)

        # Print final summary
        print(f"\n✅ Scan complete!")
        print(f"Found {results['total_momentum']} stocks with momentum signals")

    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
