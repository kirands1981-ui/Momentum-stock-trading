"""
Examples - Demonstrating how to use the momentum scanner system
Run examples: python examples.py
"""

import logging
from datetime import datetime
import pandas as pd

# Import modules
from config import (
    PRICE_INCREASE_THRESHOLD,
    VOLUME_MULTIPLIER,
    ALERT_DEDUPLICATION_WINDOW
)
from data_fetcher import StockDataFetcher, NewsAnalyzer
from analyzer import (
    VolumeAnalyzer,
    PriceAnalyzer,
    MomentumDetector,
    BuyingPatternAnalyzer
)
from alert_system import AlertManager, AlertFormatter, AlertLogger
from utils import WebUllLinkGenerator, DataFormatter
from scanner import MomentumScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_scan():
    """Example 1: Run a basic scan on specific stocks"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Stock Scan")
    print("="*60)

    scanner = MomentumScanner()
    test_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "AMD"]

    for ticker in test_tickers:
        print(f"\nScanning {ticker}...")
        result = scanner.scan_stock(ticker)
        
        if result:
            print(f"✓ Data retrieved for {ticker}")
            print(f"  Buy Type: {result.get('buy_type', 'NONE')}")
            print(f"  Score: {result.get('score', 0):.1f}/100")
        else:
            print(f"✗ No momentum signal for {ticker}")


def example_2_volume_analysis():
    """Example 2: Analyze volume patterns"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Volume Analysis")
    print("="*60)

    fetcher = StockDataFetcher()
    ticker = "NVDA"

    # Get data
    hourly_data = fetcher.get_stock_data(ticker, period="5d")
    avg_volume = fetcher.get_30day_avg_volume(ticker)

    if hourly_data is not None and not hourly_data.empty:
        print(f"\n{ticker} Volume Analysis:")
        print(f"Average 30-day volume: {DataFormatter.format_volume(avg_volume)}")

        # Check each recent hour
        for i in range(min(3, len(hourly_data))):
            idx = -(i + 1)
            timestamp = hourly_data.index[idx]
            volume = hourly_data['Volume'].iloc[idx]
            relative = volume / avg_volume if avg_volume > 0 else 0

            print(f"\n{timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Volume: {DataFormatter.format_volume(volume)}")
            print(f"  Relative: {DataFormatter.format_relative_volume(relative)}")
            print(f"  Is spike (5x+)? {'YES' if relative >= 5 else 'NO'}")


def example_3_price_analysis():
    """Example 3: Analyze price changes"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Price Change Analysis")
    print("="*60)

    fetcher = StockDataFetcher()
    ticker = "TSLA"

    hourly_data = fetcher.get_stock_data(ticker, period="5d")
    previous_close = fetcher.get_previous_close(ticker)

    if hourly_data is not None and not hourly_data.empty and previous_close:
        print(f"\n{ticker} Price Analysis:")
        print(f"Previous close: {DataFormatter.format_price(previous_close)}")

        latest_close = hourly_data['Close'].iloc[-1]
        percent_change = PriceAnalyzer.get_price_change_percent(latest_close, previous_close)

        print(f"Latest price: {DataFormatter.format_price(latest_close)}")
        print(f"Change: {DataFormatter.format_percent(percent_change)}")
        print(f"Meets 10% threshold? {'YES' if percent_change >= 10 else 'NO'}")


def example_4_buy_type_classification():
    """Example 4: Classify buy types"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Buy Type Classification")
    print("="*60)

    # Scenario 1: Institutional buy (high volume, high price, NO news)
    print("\nScenario 1: Potential Institutional Buy")
    print("- Volume spike: Yes (7.2x average)")
    print("- Price increase: 12%")
    print("- Has news: No")

    buy_type, analysis = BuyingPatternAnalyzer.classify_buy_type(
        volume_spike=True,
        relative_volume=7.2,
        price_increase=12.0,
        has_positive_news=False,
        recent_pr_link=None
    )
    print(f"Classification: {buy_type}")

    # Scenario 2: Retail buy (high volume, high price, WITH news)
    print("\nScenario 2: Potential Retail Buy")
    print("- Volume spike: Yes (6.5x average)")
    print("- Price increase: 15%")
    print("- Has news: Yes (positive PR)")

    buy_type, analysis = BuyingPatternAnalyzer.classify_buy_type(
        volume_spike=True,
        relative_volume=6.5,
        price_increase=15.0,
        has_positive_news=True,
        recent_pr_link="https://example.com/pr"
    )
    print(f"Classification: {buy_type}")


def example_5_webull_links():
    """Example 5: Generate WebUull links"""
    print("\n" + "="*60)
    print("EXAMPLE 5: WebUull Links")
    print("="*60)

    tickers = ["AAPL", "TSLA", "NVDA"]

    for ticker in tickers:
        print(f"\n{ticker}:")
        
        app_link = WebUllLinkGenerator.get_app_link(ticker)
        web_link = WebUllLinkGenerator.get_web_link(ticker)
        
        print(f"  App link: {app_link}")
        print(f"  Web link: {web_link}")


def example_6_alert_deduplication():
    """Example 6: Test alert deduplication"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Alert Deduplication")
    print("="*60)

    manager = AlertManager()

    tickers = ["TEST1", "TEST2", "TEST3"]

    for ticker in tickers:
        can_alert = manager.should_alert(ticker, dedup_window_hours=24)
        print(f"\n{ticker}:")
        print(f"  Can alert: {can_alert}")

        if can_alert:
            # Record alert
            alert_data = {
                'buy_type': 'INSTITUTIONAL_BUY',
                'details': {
                    'current_price': 150.0,
                    'price_increase_percent': 12.5,
                    'relative_volume': 6.5
                },
                'score': 75.0
            }
            manager.record_alert(ticker, alert_data)
            print(f"  Alert recorded at {datetime.now().isoformat()}")

        # Try to alert again
        can_alert = manager.should_alert(ticker, dedup_window_hours=24)
        print(f"  Can alert (immediately after): {can_alert}")


def example_7_news_analysis():
    """Example 7: Analyze news for positive sentiment"""
    print("\n" + "="*60)
    print("EXAMPLE 7: News Analysis")
    print("="*60)

    fetcher = StockDataFetcher()
    ticker = "AAPL"

    news = fetcher.search_news(ticker, hours=24)
    
    print(f"\nRecent news for {ticker}:")
    if news:
        for i, item in enumerate(news[:3], 1):
            print(f"\n{i}. {item.get('title', 'No title')}")
            print(f"   Provider: {item.get('provider', 'Unknown')}")
            print(f"   URL: {item.get('url', 'No link')}")

        has_positive, title, url = NewsAnalyzer.has_positive_news(news)
        print(f"\nPositive news sentiment: {'YES' if has_positive else 'NO'}")
    else:
        print("No recent news found")


def example_8_momentum_detector():
    """Example 8: Full momentum detection"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Full Momentum Detection")
    print("="*60)

    detector = MomentumDetector(
        volume_multiplier=VOLUME_MULTIPLIER,
        price_threshold=PRICE_INCREASE_THRESHOLD
    )

    ticker = "NVDA"
    print(f"\nDetecting momentum for {ticker}...")

    try:
        fetcher = StockDataFetcher()

        hourly_data = fetcher.get_stock_data(ticker, period="5d")
        previous_close = fetcher.get_previous_close(ticker)
        avg_volume = fetcher.get_30day_avg_volume(ticker)
        news = fetcher.search_news(ticker)

        has_news, _, _ = NewsAnalyzer.has_positive_news(news)

        result = detector.detect_momentum(
            ticker=ticker,
            hourly_data=hourly_data,
            previous_close=previous_close,
            avg_30day_volume=avg_volume,
            has_positive_news=has_news
        )

        print(f"\n✓ Momentum Detection Complete:")
        print(f"  Momentum detected: {result.get('momentum_detected', False)}")
        print(f"  Buy type: {result.get('buy_type', 'NONE')}")
        print(f"  Score: {result.get('score', 0):.1f}/100")

        if result.get('momentum_detected'):
            details = result.get('details', {})
            print(f"\n  Details:")
            print(f"    Price change: {details.get('price_increase_percent', 0):.2f}%")
            print(f"    Relative volume: {details.get('relative_volume', 0):.1f}x")
            print(f"    Current price: ${details.get('current_price', 0):.2f}")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_9_alert_formatting():
    """Example 9: Format alerts for different outputs"""
    print("\n" + "="*60)
    print("EXAMPLE 9: Alert Formatting")
    print("="*60)

    # Sample alert data
    sample_alert = {
        'ticker': 'NVDA',
        'buy_type': 'INSTITUTIONAL_BUY',
        'score': 78.5,
        'momentum_detected': True,
        'volume_spike': True,
        'details': {
            'current_price': 892.50,
            'previous_close': 805.30,
            'price_increase_percent': 10.82,
            'relative_volume': 7.3,
            'latest_volume': 45230000,
            'avg_30day_volume': 6200000,
            'has_positive_news': False,
            'pr_link': None,
            'pr_summary': None,
            'price_action': {
                'open': 810.0,
                'close': 892.50,
                'high': 900.0,
                'low': 805.0,
                'intra_hour_change': 10.17
            },
            'volume_spike': True
        }
    }

    # Console format
    print("\n1. CONSOLE FORMAT:")
    console_alert = AlertFormatter.format_console_alert(sample_alert)
    print(console_alert)

    # JSON format
    print("\n2. JSON FORMAT:")
    webull_app = WebUllLinkGenerator.get_app_link("NVDA")
    webull_web = WebUllLinkGenerator.get_web_link("NVDA")
    json_alert = AlertFormatter.format_json_alert(sample_alert, webull_web, webull_app)
    
    import json
    print(json.dumps(json_alert, indent=2))


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MOMENTUM SCANNER - USAGE EXAMPLES")
    print("="*60)

    examples = [
        ("Basic Scan", example_1_basic_scan),
        ("Volume Analysis", example_2_volume_analysis),
        ("Price Analysis", example_3_price_analysis),
        ("Buy Type Classification", example_4_buy_type_classification),
        ("WebUull Links", example_5_webull_links),
        ("Alert Deduplication", example_6_alert_deduplication),
        ("News Analysis", example_7_news_analysis),
        ("Momentum Detection", example_8_momentum_detector),
        ("Alert Formatting", example_9_alert_formatting),
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n[Example {i}/{len(examples)}] Running: {name}")
            func()
        except Exception as e:
            print(f"\n✗ Example {i} error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
