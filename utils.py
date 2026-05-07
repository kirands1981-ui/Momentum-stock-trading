"""
Utilities Module - Helper functions including WebUll link generation
"""

import urllib.parse
from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WebUllLinkGenerator:
    """Generates WebUll links for stocks"""

    # WebUull URL schemes and endpoints
    WEBULL_APP_SCHEME = "webull://quote/{ticker}"
    WEBULL_WEB_URL = "https://www.webull.com/quote/{ticker}"
    
    # Alternative WebUll links for different features
    WEBULL_CHART = "https://www.webull.com/quote/{ticker}?tab=chart"
    WEBULL_NEWS = "https://www.webull.com/quote/{ticker}?tab=news"
    WEBULL_FUNDAMENTALS = "https://www.webull.com/quote/{ticker}?tab=fundamentals"

    @staticmethod
    def get_app_link(ticker: str) -> str:
        """Get WebUull app deep link"""
        return WebUllLinkGenerator.WEBULL_APP_SCHEME.format(ticker=ticker.upper())

    @staticmethod
    def get_web_link(ticker: str) -> str:
        """Get WebUull web link"""
        return WebUllLinkGenerator.WEBULL_WEB_URL.format(ticker=ticker.upper())

    @staticmethod
    def get_chart_link(ticker: str) -> str:
        """Get WebUull chart link"""
        return WebUllLinkGenerator.WEBULL_CHART.format(ticker=ticker.upper())

    @staticmethod
    def get_1hour_chart_link(ticker: str) -> str:
        """Get WebUull 1-hour chart link"""
        # Note: WebUull URL may vary - this is approximate
        return f"https://www.webull.com/quote/{ticker.upper()}?tab=chart&interval=1hour"

    @staticmethod
    def get_all_links(ticker: str) -> Dict[str, str]:
        """Get all relevant WebUull links for a stock"""
        return {
            'app': WebUllLinkGenerator.get_app_link(ticker),
            'web': WebUllLinkGenerator.get_web_link(ticker),
            'chart': WebUllLinkGenerator.get_chart_link(ticker),
            'chart_1h': WebUllLinkGenerator.get_1hour_chart_link(ticker)
        }


class URLBuilder:
    """Build URLs for various platforms"""

    @staticmethod
    def build_robinhood_link(ticker: str) -> str:
        """Build Robinhood link"""
        return f"https://robinhood.com/stocks/{ticker.upper()}"

    @staticmethod
    def build_etrade_link(ticker: str) -> str:
        """Build E*TRADE link"""
        return f"https://us.etrade.com/home"

    @staticmethod
    def build_thinkorswim_link(ticker: str) -> str:
        """Build thinkorswim link (TD Ameritrade)"""
        return f"https://www.thinkorswim.com/login"

    @staticmethod
    def build_tradingview_link(ticker: str, exchange: str = "NASDAQ") -> str:
        """Build TradingView link"""
        symbol = f"{exchange.upper()}:{ticker.upper()}"
        return f"https://www.tradingview.com/chart/?symbol={symbol}"

    @staticmethod
    def build_google_search_link(ticker: str, news: bool = True) -> str:
        """Build Google search link"""
        query = ticker if not news else f"{ticker} news"
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    @staticmethod
    def build_seeking_alpha_link(ticker: str) -> str:
        """Build Seeking Alpha link"""
        return f"https://seekingalpha.com/symbol/{ticker.upper()}"


class TimeHelper:
    """Helper functions for time-related operations"""

    # US Eastern Time offset
    @staticmethod
    def is_market_hours(hour: int = None) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)"""
        if hour is None:
            hour = datetime.now().hour

        # Note: This is simplified. In production, consider timezone handling
        return 9 <= hour < 16

    @staticmethod
    def is_pre_market_hours(hour: int = None) -> bool:
        """Check if current time is pre-market (4:00 AM - 9:30 AM ET)"""
        if hour is None:
            hour = datetime.now().hour

        return 4 <= hour < 10

    @staticmethod
    def is_after_hours(hour: int = None) -> bool:
        """Check if current time is after-hours (4:00 PM - 8:00 PM ET)"""
        if hour is None:
            hour = datetime.now().hour

        return 16 <= hour < 20


class StockValidator:
    """Validates stock information"""

    @staticmethod
    def is_valid_ticker(ticker: str) -> bool:
        """Check if ticker looks valid"""
        if not ticker:
            return False
        
        ticker = ticker.upper().strip()
        
        # Valid tickers are 1-4 letters (or 5 with dot for preferred stock)
        if len(ticker) > 5:
            return False
        
        # Should be alphanumeric with optional dot
        if not all(c.isalpha() or c == '.' for c in ticker):
            return False
        
        return True

    @staticmethod
    def is_valid_price(price: float, min_price: float = 1.0, max_price: float = 10000.0) -> bool:
        """Check if price is within valid range"""
        return min_price <= price <= max_price

    @staticmethod
    def is_valid_volume(volume: float) -> bool:
        """Check if volume is valid"""
        return volume > 0


class DataFormatter:
    """Formats data for display"""

    @staticmethod
    def format_price(price: float, decimals: int = 2) -> str:
        """Format price with currency"""
        return f"${price:.{decimals}f}"

    @staticmethod
    def format_volume(volume: float) -> str:
        """Format volume with commas"""
        return f"{int(volume):,}"

    @staticmethod
    def format_percent(percent: float, decimals: int = 2) -> str:
        """Format percentage"""
        symbol = "+" if percent >= 0 else ""
        return f"{symbol}{percent:.{decimals}f}%"

    @staticmethod
    def format_relative_volume(relative_vol: float, decimals: int = 1) -> str:
        """Format relative volume"""
        return f"{relative_vol:.{decimals}f}x"

    @staticmethod
    def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class NewsHelper:
    """Helper functions for news handling"""

    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """Extract domain from news URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domain = domain.replace('www.', '')
            return domain
        except:
            return "Unknown"

    @staticmethod
    def is_reputable_source(domain: str) -> bool:
        """Check if news source is reputable"""
        reputable_sources = [
            'reuters.com',
            'bloomberg.com',
            'cnbc.com',
            'marketwatch.com',
            'investopedia.com',
            'seekingalpha.com',
            'fool.com',
            'wsj.com',
            'ft.com',
            'businessinsider.com'
        ]
        
        return any(source in domain.lower() for source in reputable_sources)


class AlertMessageBuilder:
    """Builds alert messages"""

    @staticmethod
    def build_momentum_message(alert_data: Dict) -> str:
        """Build a formatted momentum alert message"""
        
        ticker = alert_data['ticker']
        buy_type = alert_data['buy_type']
        score = alert_data['score']
        details = alert_data['details']

        lines = [
            f"🚀 {ticker} - {buy_type}",
            f"Score: {score:.0f}/100",
            f"Price: ${details['current_price']:.2f} (+{details['price_increase_percent']:.2f}%)",
            f"Volume: {DataFormatter.format_relative_volume(details['relative_volume'])} (30-day avg)"
        ]

        if buy_type == "RETAIL_BUY" and details.get('pr_summary'):
            lines.append(f"News: {details['pr_summary'][:100]}")

        return "\n".join(lines)

    @staticmethod
    def build_summary_message(stats: Dict) -> str:
        """Build scan summary message"""
        lines = [
            "📊 SCAN COMPLETE",
            f"Stocks scanned: {stats.get('scanned', 0)}",
            f"Momentum found: {stats.get('found', 0)}",
            f"- Institutional: {stats.get('institutional', 0)}",
            f"- Retail: {stats.get('retail', 0)}"
        ]
        
        return "\n".join(lines)
