# Momentum Stock Trading Alert System

A real-time stock momentum alert system that detects institutional and retail buying patterns on major US exchanges (NASDAQ, NYSE, AMEX) using 1-hour candle data.

## Overview

The system identifies two types of momentum signals:

1. **Institutional Buying (Silent Accumulation)**: High volume + 10%+ price spike WITHOUT any PR/news
2. **Retail Buying (PR-Driven Momentum)**: High volume + 10%+ price spike WITH positive PR/news

This is based on the institutional buying behavior analysis as explained in trading education resources, where silent accumulation indicates strong institutional confidence.

## Key Features

✅ **Real-time Scanning**: Monitors NASDAQ, NYSE, and AMEX stocks  
✅ **Volume Detection**: Identifies spikes 5x+ the 30-day average volume  
✅ **Price Analysis**: Detects 10%+ price increases on 1-hour charts  
✅ **News Integration**: Distinguishes between institutional and retail moves  
✅ **Smart Deduplication**: No duplicate alerts within 24 hours  
✅ **WebUll Integration**: Direct app and web links for each alert  
✅ **Multiple Output Formats**: Console, JSON, and HTML alerts  
✅ **Momentum Scoring**: 0-100 score based on volume and price action  

## System Architecture

```
┌─────────────────────────────────────────────────┐
│         Momentum Scanner (scanner.py)            │
│  Orchestrates scanning and alert generation      │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌────────────┐ ┌─────────┐
│Data    │ │Analyzer    │ │Alert    │
│Fetcher │ │(Volume &   │ │System   │
│(Yahoo  │ │Price)      │ │(Dedup & │
│Finance)│ │            │ │Format)  │
└────────┘ └────────────┘ └─────────┘
```

## Components

### 1. **config.py**
Configuration file with:
- Alert thresholds (pricing, volume)
- API keys and endpoints
- Stock exchange lists
- WebUll link formats
- Alert output settings

### 2. **data_fetcher.py**
Fetches data from Yahoo Finance:
- Stock historical data (OHLCV)
- Previous day close price
- 30-day average volume
- News and PR information
- Stock information (market cap, etc.)

### 3. **analyzer.py**
Analyzes momentum signals:
- `VolumeAnalyzer`: Detects volume spikes
- `PriceAnalyzer`: Calculates price changes
- `BuyingPatternAnalyzer`: Classifies buy type
- `MomentumDetector`: Main detection engine

### 4. **alert_system.py**
Manages alerts:
- `AlertManager`: Handles deduplication and history
- `AlertFormatter`: Formats alerts for console/JSON/HTML
- `AlertLogger`: Logs to file

### 5. **utils.py**
Helper utilities:
- `WebUllLinkGenerator`: Creates WebUll app/web links
- `URLBuilder`: Creates links for other platforms
- `DataFormatter`: Formats prices, volumes, percentages
- `AlertMessageBuilder`: Builds alert messages

### 6. **scanner.py**
Main scanner:
- `MomentumScanner`: Orchestrates the full scanning process
- Scans all exchanges
- Processes momentum signals
- Generates alerts

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/kirands1981-ui/Momentum-stock-trading.git
cd Momentum-stock-trading
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create data directory**
```bash
mkdir -p data logs
```

5. **Configure environment variables** (optional but recommended)
```bash
cp .env.example .env
# Then edit .env and fill in your API keys
```

Key variables in `.env`:

| Variable | Required | Description |
|---|---|---|
| `FINNHUB_API_KEY` | Optional | Enables Finnhub as a live-data fallback when Yahoo Finance rate-limits |
| `NEWS_API_KEY` | Optional | NewsAPI.org key for richer news sentiment |
| `EMAIL_ENABLED` / `SENDER_EMAIL` / `SENDER_PASSWORD` | Optional | SMTP credentials for email alerts |

## Usage

### Basic Scan

Run a full scan of all exchanges:

```bash
python scanner.py
```

### Example Output

```
============================================================
🚀 MOMENTUM ALERT: NVDA - INSTITUTIONAL_BUY
============================================================
Momentum Score: 78.5/100
Buy Type: INSTITUTIONAL_BUY
Current Price: $892.50
Previous Close: $805.30
Price Change: +10.82%
Relative Volume: 7.3x (30-day avg)
Latest Volume: 45,230,000
Pattern: Silent Institutional Accumulation (No PR)
Detected: 2026-05-07 14:35:22 ET
============================================================
```

### Output Files

1. **Alert History**: `data/alert_history.json`
   - Tracks all alerts to prevent duplicates
   
2. **Recent Alerts**: `data/alerts.json`
   - JSON format with full alert details including WebUll links
   
3. **Logs**: `logs/momentum_alerts.log`
   - Detailed log of all scans and alerts

## Alert Details

Each alert includes:

```json
{
  "timestamp": "2026-05-07T14:35:22",
  "ticker": "NVDA",
  "buy_type": "INSTITUTIONAL_BUY",
  "momentum_score": 78.5,
  "price": {
    "current": 892.50,
    "previous_close": 805.30,
    "change_percent": 10.82
  },
  "volume": {
    "latest": 45230000,
    "relative_to_30day_avg": 7.3
  },
  "links": {
    "webull_web": "https://www.webull.com/quote/NVDA",
    "webull_app": "webull://quote/NVDA"
  },
  "news": {
    "has_positive_news": false,
    "pr_link": null,
    "pr_summary": null
  }
}
```

## Configuration

Edit `config.py` to customize:

```python
# Alert thresholds
PRICE_INCREASE_THRESHOLD = 10  # 10% minimum
VOLUME_MULTIPLIER = 5  # 5x average volume

# Deduplication
ALERT_DEDUPLICATION_WINDOW = 24  # hours

# Scan interval (for future scheduler)
CHECK_INTERVAL_SECONDS = 300  # 5 minutes
```

### Data Source & Fallback

The scanner uses **Yahoo Finance** (via `yfinance`) as the primary data source for price history, quote data, and news. Yahoo's public API is free but can return HTTP 429 rate-limit errors, especially from cloud/CI environments.

When Yahoo returns no data, the scanner automatically falls back to **Finnhub** for:

| Data | Yahoo (primary) | Finnhub (fallback) |
|---|---|---|
| Hourly candles | `yfinance.Ticker.history()` | `stock/candle` |
| Previous close | `fast_info.previousClose` | `quote.pc` |
| 30-day avg volume | `fast_info.threeMonthAverageVolume` | `stock/candle` daily mean |
| Current price | `fast_info.lastPrice` | `quote.c` |
| Company news | `yfinance.Ticker.news` | `company-news` |

No code changes are needed — set `FINNHUB_API_KEY` in `.env` and the fallback activates automatically:

```bash
# .env
FINNHUB_API_KEY=your_key_here   # free tier at https://finnhub.io/
```

### Dry Run (no live data)

Run the full alert pipeline using synthetic candle data without hitting any live API:

```bash
python scanner.py --dry-run
```

This exercises the momentum detector, alert formatter, JSON output, deduplication bypass, and chart generator. Useful for verifying a new environment is wired up correctly before market hours.

You can also run the bundled regression tests:

```bash
python -m unittest tests.test_scanner_and_fetcher
```

## Understanding the Trading Logic

### Institutional Buying Pattern
When institutions accumulate shares:
- **High volume** (5x+ average) shows accumulation
- **No PR or news** = "silent buy"
- **Price spike 10%+** = conviction buying
- **Signal**: Strong bullish intent, likely continuation

### Retail Buying Pattern
When retail/traders react to news:
- **High volume** (5x+ average) from retail buying/FOMO
- **Positive PR/news** = catalyst
- **Price spike 10%+** = momentum trade
- **Signal**: Short-term momentum, may lead to volatility

## Integration with WebUll

Each alert includes direct links to WebUll:

### WebUull App Link
- Format: `webull://quote/{TICKER}`
- Click to open WebUull app directly to stock

### WebUll Web Link
- Format: `https://www.webull.com/quote/{TICKER}`
- Click to open WebUull website in browser

## How to Use Alerts

1. **Get Notified**: Run scanner regularly
2. **View Alert**: Check console or `data/alerts.json`
3. **Click WebUull Link**: Open stock in WebUull app/web
4. **Check PR Link**: If retail buy, review the news
5. **Trade**: Use your own strategy based on the signal

## Advanced Features (Future)

- [ ] Scheduled scanning (every 5 minutes during market hours)
- [ ] Email/SMS notifications
- [ ] Telegram/Discord bot integration
- [ ] Historical backtesting
- [ ] Multiple timeframe analysis (5-min, 15-min, 1-hour)
- [ ] Advanced filters (sector, market cap, price range)
- [ ] Portfolio tracking
- [ ] Machine learning for pattern recognition

## Troubleshooting

### No stocks found
- Check internet connection
- Verify Yahoo Finance is accessible
- Check stock ticker formats

### High false positives
- Adjust `PRICE_INCREASE_THRESHOLD` in config.py
- Increase `VOLUME_MULTIPLIER`
- Check 30-day volume calculation

### Alerts not being recorded
- Verify `data/` directory exists
- Check file permissions
- Review logs in `logs/momentum_alerts.log`

## Disclaimer

**For Educational Purposes Only**: This tool is designed to help identify potential momentum trading opportunities based on technical analysis. 

**Not Investment Advice**: Do not use as sole basis for investment decisions. Always:
- Conduct your own due diligence
- Consider your risk tolerance
- Use proper position sizing
- Have an exit strategy
- Consult financial advisors

## Contributing

Contributions welcome! Areas for enhancement:
- Additional data sources (Finnhub, Alpha Vantage)
- Alternative alert channels (Telegram, Discord)
- Performance optimizations
- Enhanced PR/news analysis
- International market support

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `logs/momentum_alerts.log`
3. Check `data/alert_history.json` for dedup issues
4. Open an issue on GitHub

## Resources

- Yahoo Finance API: https://finance.yahoo.com/
- WebUull: https://www.webull.com/
- TradingView: https://www.tradingview.com/
- Institutional Trading Concepts: Study market microstructure

---

**Last Updated**: May 2026  
**Version**: 1.0  
**Status**: Active Development
