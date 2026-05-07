"""
Chart and Alert Examples - Demonstrates new visualization and notification features
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from chart_generator import CandleChart, create_momentum_chart
from alert_notifier import EmailNotifier, WebhookNotifier, AlertNotifier, SystemNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_10_generate_sample_chart():
    """Example 10: Generate sample momentum chart"""
    print("\n" + "="*60)
    print("EXAMPLE 10: Generate Sample Momentum Chart")
    print("="*60)

    chart_gen = CandleChart()
    
    # Create sample data
    df, highlight_pos = chart_gen.create_sample_data(hours=40, highlight_position=32)
    
    print(f"\nGenerated {len(df)} hourly candles")
    print(f"Highlight position (institutional buy): {highlight_pos}")
    print(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    # Generate chart
    output_path = chart_gen.generate_chart(
        df,
        highlight_pos,
        ticker="SAMPLE",
        signal_type="INSTITUTIONAL_BUY",
        momentum_score=78.5
    )
    
    print(f"✓ Chart saved to: {output_path}")


def example_11_generate_real_data_chart():
    """Example 11: Generate chart from real stock data"""
    print("\n" + "="*60)
    print("EXAMPLE 11: Generate Chart from Real Data")
    print("="*60)

    from data_fetcher import StockDataFetcher
    
    fetcher = StockDataFetcher()
    ticker = "NVDA"
    
    try:
        # Get data
        hourly_data = fetcher.get_stock_data(ticker, period="5d")
        
        if hourly_data is not None and not hourly_data.empty:
            print(f"\nFetched {len(hourly_data)} hourly candles for {ticker}")
            
            # Generate chart
            chart_path = create_momentum_chart(
                ticker=ticker,
                hourly_data=hourly_data,
                signal_type="INSTITUTIONAL_BUY",
                momentum_score=75.2
            )
            
            print(f"✓ Chart generated: {chart_path}")
        else:
            print(f"No data available for {ticker}")
    
    except Exception as e:
        print(f"Error: {e}")


def example_12_email_alert_setup():
    """Example 12: Setup email alert notifier"""
    print("\n" + "="*60)
    print("EXAMPLE 12: Email Alert Configuration")
    print("="*60)

    # Example email configuration
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'your_email@gmail.com',
        'sender_password': 'your_app_password'  # Use Gmail app password, not regular password
    }

    print("\nEmail Configuration Example:")
    print(f"SMTP Server: {email_config['smtp_server']}")
    print(f"SMTP Port: {email_config['smtp_port']}")
    print(f"Sender: {email_config['sender_email']}")

    print("\n📧 To use Gmail for alerts:")
    print("1. Enable 2-factor authentication on your Google account")
    print("2. Generate an 'App Password': https://myaccount.google.com/apppasswords")
    print("3. Use the App Password (not your regular password) in configuration")
    print("4. Set 'enabled': True in email_config")

    # Create email notifier (won't send without valid credentials)
    print("\n📬 Creating email notifier...")
    notifier = EmailNotifier(
        smtp_server=email_config['smtp_server'],
        smtp_port=email_config['smtp_port'],
        sender_email=email_config['sender_email'],
        sender_password=email_config['sender_password']
    )

    print(f"Email notifier created (enabled: {notifier.enabled})")


def example_13_webhook_setup():
    """Example 13: Setup webhook alerts"""
    print("\n" + "="*60)
    print("EXAMPLE 13: Webhook Alert Configuration")
    print("="*60)

    print("\n🤖 DISCORD WEBHOOKS:")
    print("1. Create a Discord server or use existing")
    print("2. Go to Server Settings > Webhooks")
    print("3. Click 'New Webhook'")
    print("4. Copy the webhook URL")
    print("Example: https://discord.com/api/webhooks/123456789/AbCdEfGhIjKlMnOpQrStUvWxYz")

    print("\n🤖 SLACK WEBHOOKS:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create New App > From scratch")
    print("3. Enable 'Incoming Webhooks'")
    print("4. Click 'Add New Webhook to Workspace'")
    print("5. Copy the webhook URL")
    print("Example: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX")

    webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
    
    print(f"\n📨 Creating webhook notifier...")
    notifier = WebhookNotifier(webhook_url)
    print(f"Webhook notifier created (enabled: {notifier.enabled})")


def example_14_system_notifications():
    """Example 14: System/Desktop notifications"""
    print("\n" + "="*60)
    print("EXAMPLE 14: Desktop Notifications")
    print("="*60)

    print("\n🔔 Desktop notifications work on:")
    print("- macOS: Uses native 'osascript' notifications")
    print("- Linux: Uses 'notify-send'")
    print("- Windows: Uses 'win10toast' library")

    # Send example notification
    print("\nSending example desktop notification...")
    success = SystemNotifier.notify_desktop(
        title="🚀 MOMENTUM ALERT",
        message="NVDA: Institutional Buy Detected\nPrice: +10.82% | Volume: 7.3x"
    )

    if success:
        print("✓ Desktop notification sent!")
    else:
        print("✗ Desktop notification not available on this system")


def example_15_full_alert_pipeline():
    """Example 15: Full alert pipeline"""
    print("\n" + "="*60)
    print("EXAMPLE 15: Complete Alert Pipeline")
    print("="*60)

    # Sample alert data
    alert_data = {
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
            'latest_volume': 45_230_000,
            'avg_30day_volume': 6_200_000,
            'has_positive_news': False,
            'pr_link': None,
            'pr_summary': None,
            'price_action': {
                'open': 810.0,
                'close': 892.50,
                'high': 900.0,
                'low': 805.0,
                'intra_hour_change': 10.17
            }
        }
    }

    print(f"\nSample Alert Data:")
    print(f"  Ticker: {alert_data['ticker']}")
    print(f"  Type: {alert_data['buy_type']}")
    print(f"  Score: {alert_data['score']:.1f}/100")
    print(f"  Price Change: +{alert_data['details']['price_increase_percent']:.2f}%")

    # Initialize notifier with all channels
    print("\nInitializing alert notifier with all channels...")

    email_config = {
        'enabled': False,  # Disable for demo
        'smtp_server': 'smtp.gmail.com',
        'sender_email': 'your_email@gmail.com',
        'sender_password': 'your_password'
    }

    notifier = AlertNotifier(
        email_config=email_config,
        webhook_url=None  # No webhook configured
    )

    print("✓ Notifier initialized")

    # Send alert (will only go to console in this demo)
    print("\nSending alert through all channels...")
    results = notifier.send_alert(alert_data)

    print("\nAlert delivery results:")
    for channel, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {channel.capitalize()}: {success}")


def example_16_async_alerts():
    """Example 16: Asynchronous alert sending"""
    print("\n" + "="*60)
    print("EXAMPLE 16: Asynchronous Alert Sending")
    print("="*60)

    alert_data = {
        'ticker': 'TSLA',
        'buy_type': 'RETAIL_BUY',
        'score': 65.3,
        'momentum_detected': True,
        'volume_spike': True,
        'details': {
            'current_price': 278.50,
            'previous_close': 245.80,
            'price_increase_percent': 13.32,
            'relative_volume': 8.2,
            'latest_volume': 68_500_000,
            'has_positive_news': True,
            'pr_link': 'https://example.com/pr',
            'pr_summary': 'Tesla beats EPS by 25%, raises guidance',
            'price_action': {}
        }
    }

    notifier = AlertNotifier()

    # Send asynchronously (non-blocking)
    print("Sending alert asynchronously...")
    notifier.send_alert_async(alert_data)
    print("✓ Alert sent (non-blocking)")

    # Program continues while alert is being sent
    print("Program continues while alerts are being sent in background...")
    import time
    time.sleep(2)
    print("Done!")


def example_17_chart_with_alerts():
    """Example 17: Generate chart and send as alert"""
    print("\n" + "="*60)
    print("EXAMPLE 17: Chart Generation + Alert Notification")
    print("="*60)

    print("\nThis example shows the complete workflow:")
    print("1. Detect momentum signal")
    print("2. Generate candlestick chart with highlighted candle")
    print("3. Create alert message")
    print("4. Send alert with chart attached")

    from data_fetcher import StockDataFetcher

    fetcher = StockDataFetcher()
    ticker = "AAPL"

    try:
        # Get data
        hourly_data = fetcher.get_stock_data(ticker, period="5d")

        if hourly_data is not None and not hourly_data.empty:
            print(f"\n✓ Fetched data for {ticker}")

            # Generate chart
            chart_path = create_momentum_chart(
                ticker=ticker,
                hourly_data=hourly_data,
                signal_type="INSTITUTIONAL_BUY",
                momentum_score=72.3
            )
            print(f"✓ Chart generated: {chart_path}")

            # Create alert
            alert_data = {
                'ticker': ticker,
                'buy_type': 'INSTITUTIONAL_BUY',
                'score': 72.3,
                'details': {
                    'current_price': 175.43,
                    'previous_close': 160.15,
                    'price_increase_percent': 9.53,
                    'relative_volume': 6.8
                }
            }

            # Would send alert with chart attached
            print(f"✓ Would send alert with chart attached")
            print(f"  Chart: {chart_path}")
            print(f"  Alert: {ticker} - {alert_data['buy_type']}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all new examples"""
    print("\n" + "="*60)
    print("CHART & ALERT SYSTEM - USAGE EXAMPLES")
    print("="*60)

    examples = [
        ("Generate Sample Chart", example_10_generate_sample_chart),
        ("Real Data Chart", example_11_generate_real_data_chart),
        ("Email Setup", example_12_email_alert_setup),
        ("Webhook Setup", example_13_webhook_setup),
        ("System Notifications", example_14_system_notifications),
        ("Full Alert Pipeline", example_15_full_alert_pipeline),
        ("Async Alerts", example_16_async_alerts),
        ("Chart + Alerts", example_17_chart_with_alerts),
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
    print("ALL CHART & ALERT EXAMPLES COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
