"""
Alert System Module - Manages alerts and deduplication
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alerts with deduplication logic"""

    def __init__(self, history_file: str = "data/alert_history.json"):
        self.history_file = history_file
        self.alert_history = self._load_history()

    def _load_history(self) -> Dict:
        """Load alert history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading alert history: {e}")
        
        return {}

    def _save_history(self) -> None:
        """Save alert history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file) or '.', exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")

    def should_alert(self, ticker: str, dedup_window_hours: int = 24) -> bool:
        """
        Check if we should alert for this ticker
        Returns False if already alerted within dedup_window_hours
        """
        if ticker not in self.alert_history:
            return True

        last_alert_time = self.alert_history[ticker].get('timestamp')
        if not last_alert_time:
            return True

        try:
            last_alert_dt = datetime.fromisoformat(last_alert_time)
            hours_since = (datetime.now() - last_alert_dt).total_seconds() / 3600

            if hours_since < dedup_window_hours:
                logger.info(f"Skipping {ticker}: already alerted {hours_since:.1f} hours ago")
                return False
        except Exception as e:
            logger.error(f"Error checking dedup for {ticker}: {e}")

        return True

    def record_alert(self, ticker: str, alert_data: Dict) -> None:
        """Record that we've alerted for this ticker"""
        self.alert_history[ticker] = {
            'timestamp': datetime.now().isoformat(),
            'buy_type': alert_data.get('buy_type'),
            'price': alert_data.get('details', {}).get('current_price'),
            'score': alert_data.get('score')
        }
        self._save_history()

    def get_alert_count_today(self) -> int:
        """Get number of alerts today"""
        today = datetime.now().date()
        count = 0

        for ticker, data in self.alert_history.items():
            ts = data.get('timestamp')
            if ts:
                try:
                    alert_date = datetime.fromisoformat(ts).date()
                    if alert_date == today:
                        count += 1
                except:
                    pass

        return count


class AlertFormatter:
    """Formats alerts for different output channels"""

    @staticmethod
    def format_console_alert(alert_data: Dict) -> str:
        """Format alert for console output"""
        ticker = alert_data['ticker']
        buy_type = alert_data['buy_type']
        score = alert_data['score']
        details = alert_data['details']

        title = f"🚀 MOMENTUM ALERT: {ticker} - {buy_type}"
        separator = "=" * 60

        lines = [
            "",
            separator,
            title,
            separator,
            f"Momentum Score: {score:.1f}/100",
            f"Buy Type: {buy_type}",
            f"Current Price: ${details['current_price']:.2f}",
            f"Previous Close: ${details['previous_close']:.2f}",
            f"Price Change: +{details['price_increase_percent']:.2f}%",
            f"Relative Volume: {details['relative_volume']:.1f}x (30-day avg)",
            f"Latest Volume: {details['latest_volume']:,}",
        ]

        if buy_type == "RETAIL_BUY":
            lines.append(f"PR/News: {details.get('pr_summary', 'See link')}")
            if details.get('pr_link'):
                lines.append(f"PR Link: {details['pr_link']}")
        else:
            lines.append("Pattern: Silent Institutional Accumulation (No PR)")

        lines.extend([
            f"Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET",
            separator,
            ""
        ])

        return "\n".join(lines)

    @staticmethod
    def format_json_alert(alert_data: Dict, webull_link: str = "", webull_app_link: str = "") -> Dict:
        """Format alert for JSON output"""
        return {
            'timestamp': datetime.now().isoformat(),
            'ticker': alert_data['ticker'],
            'buy_type': alert_data['buy_type'],
            'momentum_score': alert_data['score'],
            'price': {
                'current': alert_data['details']['current_price'],
                'previous_close': alert_data['details']['previous_close'],
                'change_percent': alert_data['details']['price_increase_percent']
            },
            'volume': {
                'latest': alert_data['details']['latest_volume'],
                'relative_to_30day_avg': alert_data['details']['relative_volume'],
                'threshold_met': alert_data['details']['volume_spike']
            },
            'links': {
                'webull_web': webull_link,
                'webull_app': webull_app_link
            },
            'news': {
                'has_positive_news': alert_data['details']['has_positive_news'],
                'pr_link': alert_data['details'].get('pr_link'),
                'pr_summary': alert_data['details'].get('pr_summary')
            },
            'analysis': {
                'volume_spike': alert_data['details']['volume_spike'],
                'price_increase': alert_data['details']['price_increase_percent'],
                'intra_hour_change': alert_data['details']['price_action'].get('intra_hour_change', 0)
            }
        }

    @staticmethod
    def format_html_alert(alert_data: Dict, webull_link: str = "", webull_app_link: str = "") -> str:
        """Format alert as HTML for email"""
        
        buy_type = alert_data['buy_type']
        details = alert_data['details']
        score = alert_data['score']
        ticker = alert_data['ticker']

        buy_type_color = "#00AA00" if buy_type == "INSTITUTIONAL_BUY" else "#0099FF"
        buy_type_label = "🚀 INSTITUTIONAL BUY" if buy_type == "INSTITUTIONAL_BUY" else "📊 RETAIL BUY"

        pr_section = ""
        if buy_type == "RETAIL_BUY" and details.get('pr_link'):
            pr_section = f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                    <strong>News Summary:</strong><br>
                    {details.get('pr_summary', 'Positive PR detected')}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px;">
                    <a href="{details['pr_link']}" style="color: #0066cc;">View Full PR →</a>
                </td>
            </tr>
            """

        html = f"""
        <div style="background-color: {buy_type_color}; padding: 15px; border-radius: 8px; color: white; font-weight: bold; margin-bottom: 10px;">
            {buy_type_label} - {ticker}
        </div>
        
        <table style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
            <tr>
                <td style="padding: 10px; font-weight: bold; width: 50%;">Momentum Score</td>
                <td style="padding: 10px; font-size: 20px; color: #00AA00;">{score:.1f}/100</td>
            </tr>
            <tr style="background-color: white;">
                <td style="padding: 10px; font-weight: bold;">Current Price</td>
                <td style="padding: 10px;">${details['current_price']:.2f}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold;">Price Change</td>
                <td style="padding: 10px; color: #00AA00;">+{details['price_increase_percent']:.2f}%</td>
            </tr>
            <tr style="background-color: white;">
                <td style="padding: 10px; font-weight: bold;">Relative Volume</td>
                <td style="padding: 10px;">{details['relative_volume']:.1f}x (30-day avg)</td>
            </tr>
            {pr_section}
            <tr style="background-color: white;">
                <td colspan="2" style="padding: 10px; text-align: center;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="padding: 5px;">
                                <a href="{webull_link}" style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                                    Open on WebUll Web
                                </a>
                            </td>
                            <td style="padding: 5px;">
                                <a href="{webull_app_link}" style="background-color: #00AA00; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                                    Open on WebUll App
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

        return html


class AlertLogger:
    """Handles alert logging to file"""

    def __init__(self, log_file: str = "logs/momentum_alerts.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)

    def log_alert(self, alert_data: Dict) -> None:
        """Log alert to file"""
        try:
            with open(self.log_file, 'a') as f:
                line = f"{datetime.now().isoformat()} | {alert_data['ticker']} | {alert_data['buy_type']} | Score: {alert_data['score']:.1f} | Price: ${alert_data['details']['current_price']:.2f} | Volume: {alert_data['details']['relative_volume']:.1f}x\n"
                f.write(line)
        except Exception as e:
            logger.error(f"Error logging alert: {e}")

    def log_scan_summary(self, scanned: int, momentum_found: int, institutional: int, retail: int) -> None:
        """Log scan summary"""
        try:
            with open(self.log_file, 'a') as f:
                line = f"{datetime.now().isoformat()} | SCAN SUMMARY | Scanned: {scanned} | Momentum: {momentum_found} | Institutional: {institutional} | Retail: {retail}\n"
                f.write(line)
        except Exception as e:
            logger.error(f"Error logging summary: {e}")
