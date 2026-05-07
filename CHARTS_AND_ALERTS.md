# Charts & Real-Time Alerts - Quick Start

## 🆕 New Features

### 1. Professional Candlestick Charts (40 × 1-hour)
- Black background with green/red candles
- Volume bars below chart
- **Highlighted institutional buy candle** in yellow
- High-quality PNG output
- Includes momentum score and price info

### 2. Real-Time Alert System
- **Desktop notifications** (Mac/Linux/Windows)
- **Email alerts** with charts attached
- **Webhook support** (Discord, Slack, Telegram)
- Asynchronous sending (non-blocking)
- One-click WebUll links in alerts

---

## 🎨 Generate Charts

### Quick Chart Generation

```python
from chart_generator import create_momentum_chart
from data_fetcher import StockDataFetcher

fetcher = StockDataFetcher()
ticker = "NVDA"

# Get hourly data
hourly_data = fetcher.get_stock_data(ticker, period="5d")

# Generate chart
chart_path = create_momentum_chart(
    ticker=ticker,
    hourly_data=hourly_data,
    signal_type="INSTITUTIONAL_BUY",
    momentum_score=78.5
)

print(f"Chart saved to: {chart_path}")
# Output: data/charts/NVDA_20260507_143522.png
```

### Advanced Chart Options

```python
from chart_generator import CandleChart

chart_gen = CandleChart(width=16, height=9)  # Custom size

# Generate from DataFrame
chart_path = chart_gen.generate_chart(
    df=hourly_data,
    highlight_position=32,  # Which candle to highlight
    ticker="NVDA",
    signal_type="INSTITUTIONAL_BUY",
    momentum_score=78.5,
    output_path="data/charts/my_chart.png"
)
```

### Sample Data Chart (for testing)

```python
chart_gen = CandleChart()

# Generate sample 40-bar data
df, highlight_pos = chart_gen.create_sample_data(
    hours=40,
    start_price=100.0,
    highlight_position=32  # Institutional buy at bar 32
)

# Generate chart
chart_path = chart_gen.generate_chart(df, highlight_pos)
```

---

## 🔔 Real-Time Alerts

### Desktop Notifications

```python
from alert_notifier import SystemNotifier

# macOS, Linux, Windows supported
SystemNotifier.notify_desktop(
    title="🚀 MOMENTUM ALERT",
    message="NVDA: Up 10.82%\nVolume: 7.3x average"
)
```

### Email Alerts (Gmail)

```python
from alert_notifier import EmailNotifier

notifier = EmailNotifier(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender_email="your_email@gmail.com",
    sender_password="your_app_password"  # Use app-specific password!
)

# Send alert with chart attached
notifier.send_alert(
    recipient_email="you@example.com",
    alert_data=momentum_alert,
    chart_path="data/charts/NVDA_20260507_143522.png"
)
```

#### Setup Gmail for Alerts

1. Enable 2-factor authentication: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the generated 16-character password (not your gmail password!)

### Webhook Alerts (Discord/Slack)

#### Discord Setup

1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Create New Webhook
4. Copy the URL
5. Use in code:

```python
from alert_notifier import WebhookNotifier

notifier = WebhookNotifier(
    webhook_url="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
)

notifier.send_alert(alert_data)
```

#### Slack Setup

1. Go to https://api.slack.com/apps
2. Create New App
3. Enable "Incoming Webhooks"
4. Add New Webhook to Workspace
5. Copy the webhook URL

```python
notifier = WebhookNotifier(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)
```

### Full Alert Pipeline

```python
from alert_notifier import AlertNotifier

# Configure all channels
email_config = {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'alerts@example.com',
    'sender_password': 'app_password_here'
}

notifier = AlertNotifier(
    email_config=email_config,
    webhook_url="https://discord.com/api/webhooks/XXX/YYY"
)

# Send alert through all channels
results = notifier.send_alert(
    alert_data=momentum_signal,
    recipient_email="you@example.com",
    chart_path="data/charts/NVDA_chart.png"
)

# Check results
print(results)
# {'email': True, 'webhook': True, 'console': True}
```

### Asynchronous Alerts (Non-Blocking)

```python
# Send alerts in background (doesn't block scanner)
notifier.send_alert_async(
    alert_data=momentum_signal,
    recipient_email="you@example.com",
    chart_path="chart.png"
)

# Scanner continues scanning while alert is being sent
```

---

## 🚀 Integration with Scanner

The scanner now automatically:
1. Detects momentum signals
2. Generates charts with highlighted candles
3. Sends real-time alerts
4. Attaches charts to emails
5. Includes WebUull links in all alerts

### Scan with Alerts

```python
from scanner import MomentumScanner
import os

scanner = MomentumScanner(
    email_config={
        'enabled': True,
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD')
    },
    webhook_url=os.getenv('WEBHOOK_URL'),
    recipient_email=os.getenv('RECIPIENT_EMAIL'),
    enable_desktop_alerts=True
)

# Run scan - alerts sent automatically as signals found
results = scanner.scan_all_exchanges()

# Charts saved to: data/charts/
# Alerts sent via: email, webhook, desktop
```

---

## 📊 Chart Examples

### Example 1: Institutional Buy Signal

Chart shows:
- 40 × 1-hour candles
- **Candle #32 highlighted in yellow** (institutional buy)
- High volume bar below
- Green candle (bullish) with strong body
- Momentum score: 78.5/100
- Black background

### Example 2: Retail Buy Signal

Chart shows:
- 40 × 1-hour candles
- **Candle with news catalyst** highlighted
- Volume spike after news
- Potentially more volatile pattern
- Momentum score: 65.3/100

---

## 🔧 Configuration

Update `.env` file:

```bash
# Email alerts
SENDER_EMAIL=your_gmail@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
RECIPIENT_EMAIL=alerts@example.com

# Discord webhook
WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY

# Optional
WEBULL_API_KEY=your_key_here
```

In `config.py`:

```python
# Alert behavior
ALERT_DEDUPLICATION_WINDOW = 24  # hours
CHECK_INTERVAL_SECONDS = 300     # 5 minutes

# Chart output
CHART_OUTPUT_DIR = "data/charts/"
CHART_DPI = 100  # 100 for quick, 200 for high quality
```

---

## 📁 Output Files

```
data/
├── alerts.json           ← Alert data
├── alert_history.json    ← Deduplication tracking
└── charts/
    ├── NVDA_20260507_143522.png
    ├── TSLA_20260507_144015.png
    └── AAPL_20260507_144530.png

logs/
└── momentum_alerts.log   ← All activity logged
```

---

## 🎯 Typical Workflow

1. **Run scanner with alerts enabled**
   ```bash
   python scanner.py
   ```

2. **Signal detected → Automatic actions**:
   - ✅ Desktop notification pops up
   - ✅ Chart generated (40 hourly candles)
   - ✅ Email sent with chart attached
   - ✅ Discord message posted
   - ✅ Data saved to JSON

3. **Receive email with**:
   - 📊 Momentum chart
   - 🔗 WebUll app link
   - 🔗 WebUll web link
   - 📈 Price/volume details
   - ⭐ Momentum score

4. **Click link in email**:
   - Opens WebUll directly
   - Ready to trade!

---

## 💡 Best Practices

### Email Alerts
- Use Gmail's app passwords, not regular passwords
- Test with yourself first
- Don't share your app password
- Use separate email for alerts (optional but recommended)

### Webhook Alerts
- Discord: 10 messages/min rate limit
- Slack: 1 message/sec rate limit
- Test webhook URL before using in production
- Include your server/workspace name in alerts

### Charts
- Save overnight for backtesting
- Use for analysis and trading journal
- 40-hour chart is standard (1.67 days)
- Charts automatically tagged with timestamp

### Deduplication
- Default: 24-hour no-duplicate window
- Change if you want more frequent alerts
- Tracks by ticker - same stock won't alert twice in 24h
- Prevents alert spam

---

## 🧪 Test It Out

```bash
# 1. Generate sample charts
python -c "from chart_and_alert_examples import example_10_generate_sample_chart; example_10_generate_sample_chart()"

# 2. Run all demo examples
python chart_and_alert_examples.py

# 3. Test real data
python -c "from chart_and_alert_examples import example_11_generate_real_data_chart; example_11_generate_real_data_chart()"
```

---

## 🐛 Troubleshooting

### Chart not generating
- Check if `matplotlib` is installed: `pip install matplotlib`
- Verify data has at least 2 candles
- Check file permissions in `data/charts/` directory

### Email not sending
- Verify Gmail app password (not regular password!)
- Check 2FA is enabled: https://myaccount.google.com/security
- Allow less secure apps might be needed
- Check `logs/momentum_alerts.log` for errors

### Webhook not working
- Test webhook URL independently
- Discord: Check if bot has message permissions
- Slack: Verify webhook URL hasn't expired
- Try simple JSON payload first

### Desktop notifications not showing
- macOS: Check Notification Center settings
- Linux: Verify `notify-send` is installed
- Windows: Check action center settings

---

## 🚀 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Setup email alerts or webhook
3. ✅ Configure `.env` file
4. ✅ Run scanner: `python scanner.py`
5. ✅ Wait for momentum alerts with charts!

---

**Version**: 2.0 (Charts & Real-Time Alerts)  
**Last Updated**: May 2026
