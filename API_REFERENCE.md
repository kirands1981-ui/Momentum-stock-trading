# API Reference Guide

Complete API reference for the Momentum Stock Alert System.

## Table of Contents

1. [Data Fetcher API](#data-fetcher-api)
2. [Analyzer API](#analyzer-api)
3. [Alert System API](#alert-system-api)
4. [Scanner API](#scanner-api)
5. [Utilities API](#utilities-api)

---

## Data Fetcher API

### Class: StockDataFetcher

Fetches real-time and historical stock data from Yahoo Finance.

#### Methods

##### `get_nasdaq_stocks() -> List[str]`
Get list of NASDAQ stocks.

**Returns**: List of stock tickers

**Example**:
```python
from data_fetcher import StockDataFetcher
fetcher = StockDataFetcher()
nasdaq_tickers = fetcher.get_nasdaq_stocks()
print(nasdaq_tickers[:5])  # ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META']
```

##### `get_stock_data(ticker: str, period: str = "5d") -> Optional[pd.DataFrame]`
Get historical OHLCV data for a stock.

**Parameters**:
- `ticker` (str): Stock ticker symbol
- `period` (str): Time period - '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', '10y', 'max'

**Returns**: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume'] or None

**Example**:
```python
# Get 5 days of hourly data
data = fetcher.get_stock_data("NVDA", period="5d")
print(data.tail())
#                      Open        High         Low       Close        Volume
# Date
# 2026-05-07 15:00:00  890.00  900.50  885.00  898.75  4500000
```

##### `get_previous_close(ticker: str) -> Optional[float]`
Get previous day's closing price.

**Parameters**:
- `ticker` (str): Stock ticker symbol

**Returns**: Float closing price or None

**Example**:
```python
prev_close = fetcher.get_previous_close("NVDA")
print(f"Previous close: ${prev_close:.2f}")  # Previous close: $805.30
```

##### `get_30day_avg_volume(ticker: str) -> Optional[float]`
Get 30-day average trading volume.

**Parameters**:
- `ticker` (str): Stock ticker symbol

**Returns**: Float average volume or None

**Example**:
```python
avg_vol = fetcher.get_30day_avg_volume("NVDA")
print(f"30-day avg volume: {avg_vol:,.0f}")  # 30-day avg volume: 6,200,000
```

##### `search_news(ticker: str, hours: int = 24) -> List[Dict]`
Search for recent news about a stock.

**Parameters**:
- `ticker` (str): Stock ticker symbol
- `hours` (int): Lookback period in hours

**Returns**: List of news dictionaries with keys: 'title', 'url', 'provider', 'published', 'summary'

**Example**:
```python
news = fetcher.search_news("TSLA", hours=24)
for item in news[:2]:
    print(f"{item['title']}")
    print(f"  Source: {item['provider']}")
```

##### `get_current_price(ticker: str) -> Optional[float]`
Get current stock price.

**Parameters**:
- `ticker` (str): Stock ticker symbol

**Returns**: Float current price or None

**Example**:
```python
price = fetcher.get_current_price("AAPL")
print(f"Current price: ${price:.2f}")  # Current price: $192.50
```

##### `check_stock_exists(ticker: str) -> bool`
Check if stock ticker exists and has data.

**Parameters**:
- `ticker` (str): Stock ticker symbol

**Returns**: Boolean

**Example**:
```python
exists = fetcher.check_stock_exists("NVDA")
print(f"Valid ticker: {exists}")  # Valid ticker: True
```

### Class: NewsAnalyzer

Analyzes news sentiment and extracts PR information.

#### Methods

##### `has_positive_news(news_items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]`
Check if there's positive news among the items.

**Parameters**:
- `news_items` (List[Dict]): List of news items from search_news()

**Returns**: Tuple of (has_positive_news, news_title, news_url)

**Example**:
```python
from data_fetcher import NewsAnalyzer
news = fetcher.search_news("TSLA")
has_positive, title, url = NewsAnalyzer.has_positive_news(news)
if has_positive:
    print(f"Found positive news: {title}")
    print(f"URL: {url}")
```

##### `summarize_news(news_items: List[Dict], max_length: int = 200) -> Optional[str]`
Create brief summary of news headlines.

**Parameters**:
- `news_items` (List[Dict]): List of news items
- `max_length` (int): Maximum summary length

**Returns**: String summary or None

**Example**:
```python
summary = NewsAnalyzer.summarize_news(news)
print(summary)  # "Tesla posts record quarterly profit..."
```

---

## Analyzer API

### Class: VolumeAnalyzer

Analyzes trading volume patterns.

#### Methods

##### `get_relative_volume(current_volume: float, avg_volume: float) -> float`
Calculate relative volume ratio.

**Example**:
```python
from analyzer import VolumeAnalyzer
rel_vol = VolumeAnalyzer.get_relative_volume(12_000_000, 1_000_000)
print(f"Relative volume: {rel_vol:.1f}x")  # Relative volume: 12.0x
```

##### `check_high_volume(current_volume: float, avg_volume: float, multiplier: float = 5.0) -> bool`
Check if volume meets spike threshold.

**Parameters**:
- `current_volume` (float): Current hour volume
- `avg_volume` (float): 30-day average volume
- `multiplier` (float): Spike threshold multiplier (default 5.0)

**Returns**: Boolean

**Example**:
```python
is_spike = VolumeAnalyzer.check_high_volume(12_000_000, 1_000_000, multiplier=5.0)
print(f"Volume spike (5x+): {is_spike}")  # Volume spike (5x+): True

is_larger_spike = VolumeAnalyzer.check_high_volume(12_000_000, 1_000_000, multiplier=10.0)
print(f"Volume spike (10x+): {is_larger_spike}")  # Volume spike (10x+): False
```

##### `analyze_volume_spike(hourly_data: pd.DataFrame, multiplier: float = 5.0) -> Tuple[bool, float, float]`
Analyze volume spike in latest hour.

**Returns**: Tuple of (has_spike, relative_volume, latest_volume)

**Example**:
```python
data = fetcher.get_stock_data("NVDA")
has_spike, rel_vol, volume = VolumeAnalyzer.analyze_volume_spike(data)
print(f"Spike: {has_spike}, Relative: {rel_vol:.1f}x")
```

### Class: PriceAnalyzer

Analyzes price movements.

#### Methods

##### `get_price_change_percent(current_price: float, previous_price: float) -> float`
Calculate percentage price change.

**Example**:
```python
from analyzer import PriceAnalyzer
change = PriceAnalyzer.get_price_change_percent(890, 805)
print(f"Price change: {change:.2f}%")  # Price change: 10.56%
```

##### `check_price_increase(current_price: float, previous_price: float, threshold: float = 10.0) -> bool`
Check if price meets minimum increase threshold.

**Example**:
```python
meets_threshold = PriceAnalyzer.check_price_increase(890, 805, 10.0)
print(f"10%+ increase: {meets_threshold}")  # 10%+ increase: True
```

##### `get_hourly_price_action(hourly_data: pd.DataFrame) -> Dict[str, float]`
Get detailed price action from 1-hour candle.

**Returns**: Dict with keys: 'close', 'open', 'high', 'low', 'intra_hour_change', 'range'

**Example**:
```python
data = fetcher.get_stock_data("NVDA")
action = PriceAnalyzer.get_hourly_price_action(data)
print(f"Close: ${action['close']:.2f}")
print(f"Intra-hour change: {action['intra_hour_change']:.2f}%")
```

### Class: MomentumDetector

Main momentum detection engine.

#### Methods

##### `detect_momentum(**kwargs) -> Dict`
Main detection function for momentum signals.

**Parameters**:
- `ticker` (str): Stock ticker
- `hourly_data` (pd.DataFrame): OHLCV data
- `previous_close` (float): Previous day close
- `avg_30day_volume` (float): 30-day average volume
- `has_positive_news` (bool): Positive news detected
- `pr_link` (Optional[str]): PR URL if found
- `pr_summary` (Optional[str]): PR summary text

**Returns**: Dict with keys:
- 'ticker': Stock symbol
- 'momentum_detected': Boolean
- 'buy_type': 'INSTITUTIONAL_BUY', 'RETAIL_BUY', or 'NONE'
- 'score': Momentum score (0-100)
- 'details': Dict with analysis details

**Example**:
```python
from analyzer import MomentumDetector
detector = MomentumDetector(volume_multiplier=5.0, price_threshold=10.0)

result = detector.detect_momentum(
    ticker="NVDA",
    hourly_data=hour_data,
    previous_close=805.30,
    avg_30day_volume=6_200_000,
    has_positive_news=False
)

if result['momentum_detected']:
    print(f"Signal: {result['buy_type']}")
    print(f"Score: {result['score']:.1f}/100")
```

---

## Alert System API

### Class: AlertManager

Manages alert history and deduplication.

#### Methods

##### `should_alert(ticker: str, dedup_window_hours: int = 24) -> bool`
Check if we should alert for this ticker.

**Example**:
```python
from alert_system import AlertManager
manager = AlertManager()

if manager.should_alert("NVDA", dedup_window_hours=24):
    print("Can alert for NVDA")
else:
    print("Already alerted within 24 hours")
```

##### `record_alert(ticker: str, alert_data: Dict) -> None`
Record that we've alerted for this ticker.

**Example**:
```python
alert_data = {
    'buy_type': 'INSTITUTIONAL_BUY',
    'details': {
        'current_price': 890.0,
        'price_increase_percent': 10.5,
        'relative_volume': 7.3
    },
    'score': 78.5
}
manager.record_alert("NVDA", alert_data)
```

##### `get_alert_count_today() -> int`
Get number of alerts fired today.

**Example**:
```python
count = manager.get_alert_count_today()
print(f"Alerts today: {count}")
```

### Class: AlertFormatter

Formats alerts for different output channels.

#### Methods

##### `format_console_alert(alert_data: Dict) -> str`
Format alert for console output.

**Returns**: Formatted string

**Example**:
```python
from alert_system import AlertFormatter
console_msg = AlertFormatter.format_console_alert(result)
print(console_msg)
```

##### `format_json_alert(alert_data: Dict, webull_link: str, webull_app_link: str) -> Dict`
Format alert as JSON.

**Returns**: Dictionary ready for JSON serialization

**Example**:
```python
json_alert = AlertFormatter.format_json_alert(
    result,
    "https://www.webull.com/quote/NVDA",
    "webull://quote/NVDA"
)
import json
print(json.dumps(json_alert, indent=2))
```

##### `format_html_alert(alert_data: Dict, webull_link: str, webull_app_link: str) -> str`
Format alert as HTML (for email).

**Returns**: HTML string

**Example**:
```python
html = AlertFormatter.format_html_alert(result, web_link, app_link)
# Can be sent via email
```

### Class: AlertLogger

Logs alerts to file.

#### Methods

##### `log_alert(alert_data: Dict) -> None`
Log single alert to file.

**Example**:
```python
from alert_system import AlertLogger
logger = AlertLogger("logs/momentum_alerts.log")
logger.log_alert(result)
```

##### `log_scan_summary(scanned: int, momentum_found: int, institutional: int, retail: int) -> None`
Log scan summary statistics.

**Example**:
```python
logger.log_scan_summary(
    scanned=1500,
    momentum_found=12,
    institutional=8,
    retail=4
)
```

---

## Scanner API

### Class: MomentumScanner

Main scanner orchestrating the full scanning process.

#### Methods

##### `scan_stock(ticker: str) -> Optional[Dict]`
Scan a single stock for momentum.

**Returns**: Momentum result Dict or None if no signal

**Example**:
```python
from scanner import MomentumScanner
scanner = MomentumScanner()
result = scanner.scan_stock("NVDA")
if result and result['momentum_detected']:
    print(f"Found: {result['buy_type']}")
```

##### `scan_exchange(stock_list: List[str]) -> List[Dict]`
Scan a list of stocks.

**Returns**: List of momentum results

**Example**:
```python
tickers = ["AAPL", "MSFT", "NVDA", "TSLA"]
results = scanner.scan_exchange(tickers)
print(f"Found {len(results)} momentum signals")
```

##### `scan_all_exchanges() -> Dict`
Scan all exchanges (NASDAQ, NYSE, AMEX).

**Returns**: Dict with results by exchange and summary stats

**Example**:
```python
results = scanner.scan_all_exchanges()
print(f"NASDAQ alerts: {len(results['nasdaq'])}")
print(f"NYSE alerts: {len(results['nyse'])}")
print(f"AMEX alerts: {len(results['amex'])}")
print(f"Total momentum: {results['total_momentum']}")
```

---

## Utilities API

### Class: WebUllLinkGenerator

Generates WebUll app and web links.

#### Methods

##### `get_app_link(ticker: str) -> str`
Get WebUll app deep link.

**Example**:
```python
from utils import WebUllLinkGenerator
app_link = WebUllLinkGenerator.get_app_link("NVDA")
print(app_link)  # webull://quote/NVDA
```

##### `get_web_link(ticker: str) -> str`
Get WebUll web URL.

**Example**:
```python
web_link = WebUllLinkGenerator.get_web_link("NVDA")
print(web_link)  # https://www.webull.com/quote/NVDA
```

##### `get_1hour_chart_link(ticker: str) -> str`
Get direct link to 1-hour chart.

**Example**:
```python
chart_link = WebUllLinkGenerator.get_1hour_chart_link("NVDA")
print(chart_link)
```

##### `get_all_links(ticker: str) -> Dict[str, str]`
Get all WebUll links for a stock.

### Class: DataFormatter

Formats data for display.

#### Methods

##### `format_price(price: float, decimals: int = 2) -> str`
Format price with currency.

**Example**:
```python
from utils import DataFormatter
formatted = DataFormatter.format_price(890.50)
print(formatted)  # $890.50
```

##### `format_volume(volume: float) -> str`
Format volume with commas.

**Example**:
```python
formatted = DataFormatter.format_volume(12_500_000)
print(formatted)  # 12,500,000
```

##### `format_percent(percent: float, decimals: int = 2) -> str`
Format percentage.

**Example**:
```python
formatted = DataFormatter.format_percent(10.56)
print(formatted)  # +10.56%
```

##### `format_relative_volume(relative_vol: float, decimals: int = 1) -> str`
Format relative volume.

**Example**:
```python
formatted = DataFormatter.format_relative_volume(7.3)
print(formatted)  # 7.3x
```

---

## Configuration API

### config.py

All configuration constants:

```python
from config import (
    PRICE_INCREASE_THRESHOLD,     # 10% default
    VOLUME_MULTIPLIER,             # 5x default
    ALERT_DEDUPLICATION_WINDOW,    # 24 hours
    MIN_PRICE,                     # $1 default
    MAX_PRICE,                     # $10,000 default
    MIN_MARKET_CAP,                # $100M default
)
```

---

## Integration Examples

### Example 1: Scan FAANG stocks only

```python
from scanner import MomentumScanner

scanner = MomentumScanner()
faang = ["AAPL", "MSFT", "GOOG", "NVDA", "META"]
results = scanner.scan_exchange(faang)

for result in results:
    if result['momentum_detected']:
        print(f"{result['ticker']}: {result['buy_type']}")
```

### Example 2: Check specific ticker

```python
from data_fetcher import StockDataFetcher
from analyzer import MomentumDetector

fetcher = StockDataFetcher()
detector = MomentumDetector()

ticker = "NVDA"
data = fetcher.get_stock_data(ticker)
prev_close = fetcher.get_previous_close(ticker)
avg_vol = fetcher.get_30day_avg_volume(ticker)

result = detector.detect_momentum(
    ticker,
    data,
    prev_close,
    avg_vol
)

if result['momentum_detected']:
    print(f"Alert: {result['buy_type']} (Score: {result['score']:.1f})")
```

### Example 3: Custom scoring

```python
from analyzer import BuyingPatternAnalyzer

buy_type, analysis = BuyingPatternAnalyzer.classify_buy_type(
    volume_spike=True,
    relative_volume=8.5,
    price_increase=15.0,
    has_positive_news=False
)

score = BuyingPatternAnalyzer.calculate_momentum_score(
    relative_volume=8.5,
    price_increase=15.0,
    buy_type=buy_type
)

print(f"Score: {score:.1f}/100")
```

---

## Error Handling

All methods are wrapped with try-except blocks. They return None or empty results on error:

```python
# Returns None on error
data = fetcher.get_stock_data("INVALID")  # None

# Returns empty list on error
news = fetcher.search_news("BADTICKER")  # []

# Returns False on error
exists = fetcher.check_stock_exists("XXXXX")  # False
```

Always check for None/empty before using results.

---

**API Version**: 1.0  
**Last Updated**: May 2026
