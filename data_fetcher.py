"""
Data Fetcher Module - Retrieves stock data and news information
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import UTC, datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple

from config import FINNHUB_API_KEY

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data from Yahoo Finance and news data"""

    def __init__(self):
        self.session = requests.Session()
        self.cache = {}  # Cache Yahoo ticker objects and quote metadata
        self.finnhub_api_key = FINNHUB_API_KEY.strip()

    def _get_ticker(self, ticker: str) -> yf.Ticker:
        """Return a cached yfinance ticker object."""
        if ticker not in self.cache:
            self.cache[ticker] = yf.Ticker(ticker)
        return self.cache[ticker]

    def _get_fast_info(self, ticker: str) -> Dict:
        """Fetch fast quote data without using the heavier info endpoint."""
        try:
            info = self._get_ticker(ticker).fast_info
            return dict(info.items()) if info else {}
        except Exception as e:
            logger.debug(f"Error fetching fast info for {ticker}: {e}")
            return {}

    def _has_finnhub(self) -> bool:
        """Return True when a Finnhub API key is configured."""
        return bool(self.finnhub_api_key)

    def _finnhub_get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Fetch JSON from Finnhub when a fallback API key is configured."""
        if not self._has_finnhub():
            return None

        try:
            response = self.session.get(
                f"https://finnhub.io/api/v1/{endpoint}",
                params={**params, 'token': self.finnhub_api_key},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Finnhub request failed for {endpoint}: {e}")
            return None

    def _get_finnhub_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch a realtime quote from Finnhub."""
        quote = self._finnhub_get("quote", {'symbol': ticker})
        if not quote or not quote.get('c'):
            return None
        return quote

    def _get_finnhub_history(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch historical candles from Finnhub and normalize to yfinance-like columns."""
        resolution_map = {
            ('5d', '1h'): ('60', 5),
            ('30d', '1d'): ('D', 30),
            ('5d', '1d'): ('D', 5),
            ('2d', '1d'): ('D', 2),
            ('1d', '1d'): ('D', 1),
        }
        resolution, days = resolution_map.get((period, interval), (None, None))
        if not resolution:
            return None

        now_utc = datetime.now(UTC)
        end_time = int(now_utc.timestamp())
        start_time = int((now_utc - timedelta(days=days)).timestamp())
        candles = self._finnhub_get(
            "stock/candle",
            {
                'symbol': ticker,
                'resolution': resolution,
                'from': start_time,
                'to': end_time,
            },
        )
        if not candles or candles.get('s') != 'ok':
            return None

        frame = pd.DataFrame(
            {
                'Open': candles.get('o', []),
                'High': candles.get('h', []),
                'Low': candles.get('l', []),
                'Close': candles.get('c', []),
                'Volume': candles.get('v', []),
            },
            index=pd.to_datetime(candles.get('t', []), unit='s'),
        )
        if frame.empty:
            return None
        return frame

    def _get_finnhub_news(self, ticker: str, hours: int) -> List[Dict]:
        """Fetch recent company news from Finnhub."""
        now_utc = datetime.now(UTC)
        end_date = now_utc.date()
        start_date = (now_utc - timedelta(hours=hours)).date()
        news = self._finnhub_get(
            "company-news",
            {
                'symbol': ticker,
                'from': start_date.isoformat(),
                'to': end_date.isoformat(),
            },
        )
        if not isinstance(news, list):
            return []

        recent_news = []
        for item in news[:10]:
            recent_news.append({
                'title': item.get('headline', ''),
                'url': item.get('url', ''),
                'provider': item.get('source', ''),
                'published': item.get('datetime', ''),
                'summary': item.get('summary') or item.get('headline', ''),
            })
        return recent_news

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
            stock = self._get_ticker(ticker)
            hist = stock.history(period=period, interval="1h")
            if not hist.empty:
                return hist
        except Exception as e:
            logger.debug(f"Error fetching Yahoo data for {ticker}: {e}")

        fallback = self._get_finnhub_history(ticker, period=period, interval="1h")
        if fallback is not None:
            logger.info(f"Using Finnhub candle fallback for {ticker}")
        return fallback

    def get_previous_close(self, ticker: str) -> Optional[float]:
        """Get previous day's closing price"""
        try:
            fast_info = self._get_fast_info(ticker)
            previous_close = (
                fast_info.get('previousClose')
                or fast_info.get('regularMarketPreviousClose')
            )
            if previous_close:
                return float(previous_close)

            stock = self._get_ticker(ticker)
            hist = stock.history(period="5d", interval="1d")
            if not hist.empty:
                if len(hist) >= 2:
                    return float(hist['Close'].iloc[-2])
                return float(hist['Close'].iloc[-1])
        except Exception as e:
            logger.debug(f"Error fetching previous close for {ticker}: {e}")

        quote = self._get_finnhub_quote(ticker)
        if quote and quote.get('pc'):
            logger.info(f"Using Finnhub previous-close fallback for {ticker}")
            return float(quote['pc'])
        return None

    def get_30day_avg_volume(self, ticker: str) -> Optional[float]:
        """Get 30-day average volume"""
        try:
            fast_info = self._get_fast_info(ticker)
            avg_volume = fast_info.get('threeMonthAverageVolume') or fast_info.get('tenDayAverageVolume')
            if avg_volume:
                return float(avg_volume)

            stock = self._get_ticker(ticker)
            hist = stock.history(period="30d", interval="1d")
            if not hist.empty:
                return float(hist['Volume'].mean())
        except Exception as e:
            logger.debug(f"Error fetching avg volume for {ticker}: {e}")

        fallback = self._get_finnhub_history(ticker, period="30d", interval="1d")
        if fallback is not None:
            logger.info(f"Using Finnhub average-volume fallback for {ticker}")
            return float(fallback['Volume'].mean())
        return None

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Get basic stock information"""
        try:
            info = self._get_fast_info(ticker)
            if info:
                return info
        except Exception as e:
            logger.debug(f"Error fetching info for {ticker}: {e}")

        quote = self._get_finnhub_quote(ticker)
        if not quote:
            return None
        logger.info(f"Using Finnhub stock-info fallback for {ticker}")
        return {
            'currentPrice': quote.get('c'),
            'regularMarketPrice': quote.get('c'),
            'previousClose': quote.get('pc'),
            'regularMarketPreviousClose': quote.get('pc'),
        }

    def search_news(self, ticker: str, hours: int = 24) -> List[Dict]:
        """
        Search for recent news about a stock
        Returns list of news items with title, description, and URL
        """
        try:
            stock = self._get_ticker(ticker)
            news = stock.news or []

            recent_news = []
            for item in news[:10]:  # Get top 10
                recent_news.append({
                    'title': item.get('title', ''),
                    'url': item.get('link') or item.get('url', ''),
                    'provider': item.get('publisher', ''),
                    'published': item.get('providerPublishTime') or item.get('publishedAt', ''),
                    'summary': item.get('title', '')
                })

            return recent_news
        except Exception as e:
            logger.debug(f"Error fetching Yahoo news for {ticker}: {e}")

        fallback = self._get_finnhub_news(ticker, hours)
        if fallback:
            logger.info(f"Using Finnhub news fallback for {ticker}")
        return fallback

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current stock price"""
        try:
            fast_info = self._get_fast_info(ticker)
            current_price = fast_info.get('lastPrice') or fast_info.get('regularMarketPrice')
            if current_price is not None:
                return float(current_price)
        except Exception as e:
            logger.debug(f"Error fetching current price for {ticker}: {e}")

        quote = self._get_finnhub_quote(ticker)
        if quote and quote.get('c'):
            logger.info(f"Using Finnhub current-price fallback for {ticker}")
            return float(quote['c'])
        return None

    def check_stock_exists(self, ticker: str) -> bool:
        """Check if stock ticker exists and has data"""
        try:
            stock = self._get_ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                return True
        except Exception:
            pass

        quote = self._get_finnhub_quote(ticker)
        return bool(quote and quote.get('c'))


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
