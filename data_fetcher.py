"""
Data Fetcher Module - Retrieves stock data and news information
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data from Yahoo Finance and news data"""

    def __init__(self):
        self.session = requests.Session()
        self.cache = {}  # Simple cache for stock lists

    def get_nasdaq_stocks(self) -> List[str]:
        """Get list of NASDAQ stocks (top 500 by market cap)"""
        try:
            # Get NASDAQ 100 stocks as representative sample
            # In production, you'd pull full list from a data source
            url = "https://finance.yahoo.com/quote/%5ENDX/components"
            # Using hardcoded list for now - in production use an API
            nasdaq_stocks = self._get_nasdaq_list_fallback()
            return nasdaq_stocks
        except Exception as e:
            logger.error(f"Error fetching NASDAQ stocks: {e}")
            return self._get_nasdaq_list_fallback()

    def get_nyse_stocks(self) -> List[str]:
        """Get list of NYSE stocks (sample)"""
        try:
            nyse_stocks = self._get_nyse_list_fallback()
            return nyse_stocks
        except Exception as e:
            logger.error(f"Error fetching NYSE stocks: {e}")
            return self._get_nyse_list_fallback()

    def get_amex_stocks(self) -> List[str]:
        """Get list of AMEX stocks (sample)"""
        try:
            amex_stocks = self._get_amex_list_fallback()
            return amex_stocks
        except Exception as e:
            logger.error(f"Error fetching AMEX stocks: {e}")
            return self._get_amex_list_fallback()

    def _get_nasdaq_list_fallback(self) -> List[str]:
        """Fallback list of popular NASDAQ stocks"""
        return [
            "AAPL", "MSFT", "NVDA", "TSLA", "META", "AMZN", "GOOGL", "GOOG",
            "NFLX", "AMD", "PYPL", "NFLX", "INTC", "CSCO", "ADBE", "QCOM",
            "ASML", "AVGO", "CMCSA", "COST", "CRWD", "CRM", "ABNB", "ANET",
            "ANSS", "ALTR", "MU", "INTU", "FOXA", "LRCX", "VRSK", "SNPS",
            "CDNS", "ODFL", "PCAR", "MNST", "PEP", "KLAC", "PANW", "NETS",
            "TEAM", "MSTR", "ZS", "DDOG", "SNOW", "OKTA", "UPST", "RBLX",
            "SQ", "ROKU", "HOOD", "RIVN", "MELI", "TTD", "ETSY", "SHOP",
            "UBER", "LYFT", "ZG", "W", "MARA", "RIOT", "CLSK", "COIN",
            "GME", "AMC", "NIO", "XPV", "PLTR", "ARKK", "SOFI", "LCID"
        ]

    def _get_nyse_list_fallback(self) -> List[str]:
        """Fallback list of popular NYSE stocks"""
        return [
            "JPM", "BAC", "GS", "MS", "WFC", "USB", "BLK", "SCHW", "AXP",
            "COF", "F", "GM", "LMT", "BA", "GE", "MMM", "CAT", "APA", "MPC",
            "PSX", "COP", "SLB", "OKE", "MRO", "EOG", "PXD", "CVX", "XOM",
            "CL", "PG", "KO", "MO", "PM", "DEO", "UL", "NWL", "EL", "CLX",
            "T", "VZ", "VOD", "IBM", "HPE", "SGY", "MCD", "KFC", "YUM",
            "PK", "X", "CLF", "MT", "FCX", "NEM", "GLD", "DBC", "EFA"
        ]

    def _get_amex_list_fallback(self) -> List[str]:
        """Fallback list of AMEX/smaller stocks"""
        return [
            "GDX", "GDXJ", "AGQ", "DBC", "EEM", "EWZ", "GUSH", "DRIP",
            "DRV", "UUP", "SLV", "USO", "TLT", "IEF", "HYG", "LQD",
            "VCIT", "VGIT", "PCY", "PHB", "ANGL", "EMB", "RDIV", "VIG"
        ]

    def get_stock_data(self, ticker: str, period: str = "5d") -> Optional[pd.DataFrame]:
        """
        Get historical stock data
        period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', '10y', 'max'
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval="1h")
            
            if hist.empty:
                return None
            
            return hist
        except Exception as e:
            logger.debug(f"Error fetching data for {ticker}: {e}")
            return None

    def get_previous_close(self, ticker: str) -> Optional[float]:
        """Get previous day's closing price"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if hist.empty or len(hist) < 2:
                return None
            
            return float(hist['Close'].iloc[-2])  # Previous day close
        except Exception as e:
            logger.debug(f"Error fetching previous close for {ticker}: {e}")
            return None

    def get_30day_avg_volume(self, ticker: str) -> Optional[float]:
        """Get 30-day average volume"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            
            if hist.empty:
                return None
            
            return float(hist['Volume'].mean())
        except Exception as e:
            logger.debug(f"Error fetching avg volume for {ticker}: {e}")
            return None

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Get basic stock information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info
        except Exception as e:
            logger.debug(f"Error fetching info for {ticker}: {e}")
            return None

    def search_news(self, ticker: str, hours: int = 24) -> List[Dict]:
        """
        Search for recent news about a stock
        Returns list of news items with title, description, and URL
        """
        try:
            # Using NewsAPI (requires API key) or yfinance news
            stock = yf.Ticker(ticker)
            news = stock.info.get('news', [])
            
            recent_news = []
            for item in news[:10]:  # Get top 10
                recent_news.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'provider': item.get('publisher', ''),
                    'published': item.get('publishedAt', ''),
                    'summary': item.get('title', '')  # Title as summary
                })
            
            return recent_news
        except Exception as e:
            logger.debug(f"Error fetching news for {ticker}: {e}")
            return []

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current stock price"""
        try:
            stock = yf.Ticker(ticker)
            return float(stock.info.get('currentPrice') or stock.info.get('regularMarketPrice', None))
        except Exception as e:
            logger.debug(f"Error fetching current price for {ticker}: {e}")
            return None

    def check_stock_exists(self, ticker: str) -> bool:
        """Check if stock ticker exists and has data"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            return not hist.empty
        except Exception as e:
            return False


class NewsAnalyzer:
    """Analyzes news and PR to determine if it's positive/negative"""

    POSITIVE_KEYWORDS = [
        'positive', 'strong', 'beat', 'upgrade', 'buy', 'bullish',
        'growth', 'profit', 'revenue', 'expanded', 'partnership',
        'acquisition', 'approved', 'launch', 'success', 'surge',
        'gain', 'jump', 'rally', 'momentum', 'record', 'high'
    ]

    NEGATIVE_KEYWORDS = [
        'negative', 'weak', 'miss', 'downgrade', 'sell', 'bearish',
        'loss', 'decline', 'cut', 'delay', 'recall', 'investigation',
        'bankruptcy', 'lawsuit', 'failure', 'drop', 'crash'
    ]

    @staticmethod
    def has_positive_news(news_items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if there's positive news
        Returns: (has_positive_news, news_title, news_url)
        """
        if not news_items:
            return False, None, None

        for news in news_items:
            title = (news.get('title') or '').lower()
            
            # Check for positive indicators
            positive_count = sum(1 for keyword in NewsAnalyzer.POSITIVE_KEYWORDS if keyword in title)
            negative_count = sum(1 for keyword in NewsAnalyzer.NEGATIVE_KEYWORDS if keyword in title)
            
            if positive_count > negative_count and positive_count > 0:
                return True, news.get('title'), news.get('url')
        
        return False, None, None

    @staticmethod
    def summarize_news(news_items: List[Dict], max_length: int = 200) -> Optional[str]:
        """Create a brief summary of the news"""
        if not news_items:
            return None
        
        title = news_items[0].get('title', '')
        if len(title) > max_length:
            return title[:max_length] + "..."
        return title
