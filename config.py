"""
Configuration settings for the Momentum Stock Alert System
"""

import os

from dotenv import load_dotenv

load_dotenv()

# API Keys (set these in environment variables)
YAHOO_FINANCE_API = True  # Using yfinance
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Scanner Settings
PRICE_INCREASE_THRESHOLD = 10  # Minimum 10% price increase
VOLUME_MULTIPLIER = 5  # High relative volume = 5x 30-day average
TIME_FRAME = "1h"  # 1-hour candle (we'll fetch intraday data)

# Stock Exchange Lists
EXCHANGES = {
    "NASDAQ": "^IXIC",
    "NYSE": "^NYA",
    "AMEX": "^XAX"
}

# Market hours (US Eastern Time)
MARKET_OPEN_HOUR = 9  # 9:30 AM ET
MARKET_CLOSE_HOUR = 16  # 4:00 PM ET

# Alert System Settings
ALERT_DEDUPLICATION_WINDOW = 24  # Don't alert same stock within 24 hours
CHECK_INTERVAL_SECONDS = 300  # Scan every 5 minutes during market hours

# Data Storage
ALERT_HISTORY_FILE = "data/alert_history.json"
LOG_FILE = "logs/momentum_alerts.log"

# Stock Filter Settings
MIN_PRICE = 1.0  # Minimum stock price
MAX_PRICE = 10000.0  # Maximum stock price
MIN_MARKET_CAP = 100_000_000  # Minimum $100M market cap

# PR/News Settings
PR_CHECK_ENABLED = True
NEWS_LOOKBACK_HOURS = 24  # Check for news in last 24 hours

# WebUll Settings
WEBULL_APP_SCHEME = "webull://quote/{ticker}"  # WebUll app link scheme
WEBULL_WEB_URL = "https://www.webull.com/quote/{ticker}"  # WebUll web link

# Alerts Output
ALERT_CHANNELS = ["console", "file", "json"]  # Where to send alerts
OUTPUT_ALERT_FILE = "data/alerts.json"
