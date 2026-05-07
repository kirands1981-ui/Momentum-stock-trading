# Quick Start Guide - Momentum Stock Alert System

## 5-Minute Setup

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Directories
```bash
mkdir -p data logs
```

### Step 3: Run Your First Scan
```bash
python scanner.py
```

That's it! The system will scan NASDAQ, NYSE, and AMEX stocks and alert you to momentum signals.

---

## Understanding the Alerts

### Alert Types

#### 🚀 INSTITUTIONAL_BUY
- **Pattern**: High volume + price spike WITHOUT PR/news
- **Meaning**: Silent institutional accumulation, strong bullish signal
- **What it means**: Institutions are accumulating shares without public announcement
- **Trade idea**: Likely continuation, usually more reliable

Example:
```
🚀 MOMENTUM ALERT: NVDA - INSTITUTIONAL_BUY
Momentum Score: 78.5/100
Price Change: +10.82%
Relative Volume: 7.3x average
Pattern: Silent institutional accumulation (no PR)
```

#### 📊 RETAIL_BUY
- **Pattern**: High volume + price spike WITH positive PR/news
- **Meaning**: Retail/trader momentum based on news catalyst
- **What it means**: Stock is getting retail buying interest due to news
- **Trade idea**: Short-term momentum, may be more volatile

Example:
```
📊 MOMENTUM ALERT: TSLA - RETAIL_BUY
Momentum Score: 65.3/100
Price Change: +12.45%
Relative Volume: 6.2x average
News: "Tesla achieves record quarterly profit"
PR Link: [link to full article]
```

---

## Output Files

After running a scan, you'll find:

### 1. `data/alert_history.json`
Tracks when each stock was alerted to prevent duplicates:
```json
{
  "NVDA": {
    "timestamp": "2026-05-07T14:35:22",
    "buy_type": "INSTITUTIONAL_BUY",
    "price": 892.50,
    "score": 78.5
  }
}
```

### 2. `data/alerts.json`
Complete alert data with WebUul links:
```json
[
  {
    "timestamp": "2026-05-07T14:35:22",
    "ticker": "NVDA",
    "buy_type": "INSTITUTIONAL_BUY",
    "momentum_score": 78.5,
    "links": {
      "webull_app": "webull://quote/NVDA",
      "webull_web": "https://www.webull.com/quote/NVDA"
    }
  }
]
```

### 3. `logs/momentum_alerts.log`
Detailed log file:
```
2026-05-07 14:35:22 | NVDA | INSTITUTIONAL_BUY | Score: 78.5 | Price: $892.50 | Volume: 7.3x
2026-05-07 14:42:15 | TSLA | RETAIL_BUY | Score: 65.3 | Price: $245.80 | Volume: 6.2x
```

---

## Using the WebUull Links

Each alert includes two WebUull links:

### 1. App Link: `webull://quote/NVDA`
- Copy and paste into iPhone Safari
- WebUull app will open directly to that stock
- See 1-hour chart showing the momentum

### 2. Web Link: `https://www.webull.com/quote/NVDA`
- Click to open WebUull website
- View charts, fundamentals, news all in one place

---

## Customizing the Scanner

Edit `config.py` to change:

```python
# Alert thresholds
PRICE_INCREASE_THRESHOLD = 10   # Change to 5% or 15%
VOLUME_MULTIPLIER = 5           # Change to 3x or 10x

# Deduplication (don't alert same stock within X hours)
ALERT_DEDUPLICATION_WINDOW = 24 # Change to 6, 12, 48 hours

# Stock filters
MIN_PRICE = 1.0                 # Skip penny stocks
MAX_PRICE = 10000.0             # Skip very expensive stocks
MIN_MARKET_CAP = 100_000_000    # Minimum $100M market cap
```

---

## Common Questions

### Q: Why no alerts found?
A: This means no stocks met ALL criteria:
- Volume spike: 5x+ (30-day average)
- Price increase: 10%+
- For Institutional: NO news/PR
- For Retail: Positive news/PR found

Try adjusting thresholds in `config.py`.

### Q: Can I stop duplicate alerts?
A: Yes! Deduplication is automatic within 24 hours.
Change `ALERT_DEDUPLICATION_WINDOW` in `config.py` to adjust.

### Q: Where's the PR summary?
A: Only included for RETAIL_BUY alerts.
INSTITUTIONAL_BUY alerts have NO PR (that's the point!).

### Q: How accurate are these alerts?
A: This is a technical indicator tool, not a trading signal.
- Institutional buys are more reliable (institutions usually know)
- Retail buys can be volatile (FOMO-driven)
- Always do your own research

### Q: How often should I run the scan?
A: During market hours: Every 5-30 minutes
Before market: Not useful
After hours: May catch after-hours momentum (risky)

---

## Advanced Usage

### Run Scan for Specific Exchange
```python
scanner = MomentumScanner()
results = scanner.scan_exchange(["AAPL", "MSFT", "NVDA"])
```

### Check Deduplication
```python
manager = AlertManager()
if manager.should_alert("AAPL", dedup_window_hours=24):
    print("Can alert for AAPL")
else:
    print("Already alerted within 24 hours")
```

### Analyze Single Stock
```python
analyzer = MomentumDetector()
result = analyzer.detect_momentum(
    ticker="AAPL",
    hourly_data=hourly_df,
    previous_close=150.0,
    avg_30day_volume=50000000,
    has_positive_news=False
)
```

---

## Troubleshooting

### Error: "No module named 'yfinance'"
```bash
pip install yfinance
```

### Error: "Connection refused"
- Check internet connection
- Yahoo Finance may be temporarily down

### Error: "Permission denied: 'data/alerts.json'"
```bash
chmod 755 data/
chmod 666 data/*.json logs/*
```

### No stocks showing momentum
- Normal! Momentum signals are rare
- Try lowering thresholds in `config.py`
- Check if market is closed

---

## Signal Quality by Market Conditions

### Best Conditions (Best signals)
- Market-wide momentum / FOMC meetings
- Earnings season (high volatility)
- Post market-open (10-11 AM ET)
- End of week (tactical accumulation)

### Worst Conditions (Most false positives)
- Low volume days
- Market holidays
- Pre-earnings (strange patterns)
- after-hours trading

---

## Next Steps

1. ✅ Run first scan: `python scanner.py`
2. 📱 Save WebUul app link to phone
3. 📊 Track alerts in `data/alerts.json`
4. 🎯 Test with a small position
5. 📈 Refine thresholds based on results

---

## Support Resources

- **Website**: https://www.webull.com/
- **Charts**: https://www.tradingview.com/
- **Financial Data**: https://finance.yahoo.com/
- **News Search**: https://www.google.com/news

---

## Disclaimer ⚠️

- **Not Financial Advice**: Do not trade with real money without understanding the risks
- **Past Performance**: This tool shows technical signals, not predictions
- **Volatility**: These stocks often move 20%+ - use stop losses
- **Risk Management**: Never risk more than you can afford to lose

---

**Version**: 1.0  
**Updated**: May 2026  
**Status**: Production Ready
