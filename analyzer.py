"""
Analyzer Module - Analyzes stock volume and price movements
Identifies institutional vs retail buying patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VolumeAnalyzer:
    """Analyzes trading volume and relative volume changes"""

    @staticmethod
    def get_relative_volume(
        current_volume: float,
        avg_volume: float
    ) -> float:
        """Calculate relative volume (current / average)"""
        if avg_volume <= 0:
            return 0
        return current_volume / avg_volume

    @staticmethod
    def check_high_volume(
        current_volume: float,
        avg_volume: float,
        multiplier: float = 5.0
    ) -> bool:
        """Check if current volume is 5x (or multiplier) of 30-day average"""
        relative_vol = VolumeAnalyzer.get_relative_volume(current_volume, avg_volume)
        return relative_vol >= multiplier

    @staticmethod
    def analyze_volume_spike(
        hourly_data: pd.DataFrame,
        multiplier: float = 5.0
    ) -> Tuple[bool, float, float]:
        """
        Analyze if there's a volume spike in the latest hour
        Returns: (has_spike, relative_volume, latest_volume)
        """
        if hourly_data.empty or len(hourly_data) < 2:
            return False, 0, 0

        latest_volume = float(hourly_data['Volume'].iloc[-1])
        avg_volume = float(hourly_data['Volume'].mean())

        has_spike = VolumeAnalyzer.check_high_volume(latest_volume, avg_volume, multiplier)
        relative_vol = VolumeAnalyzer.get_relative_volume(latest_volume, avg_volume)

        return has_spike, relative_vol, latest_volume


class PriceAnalyzer:
    """Analyzes price movements and changes"""

    @staticmethod
    def get_price_change_percent(
        current_price: float,
        previous_price: float
    ) -> float:
        """Calculate percentage change from previous price"""
        if previous_price <= 0:
            return 0
        return ((current_price - previous_price) / previous_price) * 100

    @staticmethod
    def check_price_increase(
        current_price: float,
        previous_price: float,
        threshold: float = 10.0
    ) -> bool:
        """Check if price increased by threshold percent"""
        change = PriceAnalyzer.get_price_change_percent(current_price, previous_price)
        return change >= threshold

    @staticmethod
    def get_hourly_price_action(
        hourly_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Get price action details from hourly data"""
        if hourly_data.empty:
            return {}

        latest_close = float(hourly_data['Close'].iloc[-1])
        latest_open = float(hourly_data['Open'].iloc[-1])
        latest_high = float(hourly_data['High'].iloc[-1])
        latest_low = float(hourly_data['Low'].iloc[-1])

        intra_hour_change = ((latest_close - latest_open) / latest_open * 100) if latest_open > 0 else 0

        return {
            'close': latest_close,
            'open': latest_open,
            'high': latest_high,
            'low': latest_low,
            'intra_hour_change': intra_hour_change,
            'range': latest_high - latest_low
        }


class BuyingPatternAnalyzer:
    """Analyzes buying patterns to identify institutional vs retail buying"""

    @staticmethod
    def classify_buy_type(
        volume_spike: bool,
        relative_volume: float,
        price_increase: float,
        has_positive_news: bool,
        recent_pr_link: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Classify the type of buying: INSTITUTIONAL or RETAIL
        
        Returns: (buy_type, analysis_details)
        """

        analysis = {
            'volume_spike': volume_spike,
            'relative_volume': relative_volume,
            'price_increase': price_increase,
            'has_positive_news': has_positive_news,
            'has_pr': recent_pr_link is not None
        }

        # Institutional buying patterns:
        # - High volume + price increase WITHOUT PR (silent accumulation)
        if volume_spike and price_increase >= 10 and not has_positive_news and not recent_pr_link:
            return "INSTITUTIONAL_BUY", analysis

        # Retail buying patterns:
        # - High volume + price increase WITH PR (momentum trading based on news)
        if volume_spike and price_increase >= 10 and (has_positive_news or recent_pr_link):
            return "RETAIL_BUY", analysis

        # No clear pattern
        return "UNCLEAR", analysis

    @staticmethod
    def calculate_momentum_score(
        relative_volume: float,
        price_increase: float,
        buy_type: str
    ) -> float:
        """
        Calculate a momentum score (0-100)
        Higher score = stronger momentum
        """
        if not (relative_volume >= 5 and price_increase >= 10):
            return 0

        # Normalize values
        volume_score = min((relative_volume / 10) * 50, 50)  # Max 50 points
        price_score = min((price_increase / 30) * 50, 50)  # Max 50 points

        # Boost institutional buys slightly (more reliable signal)
        multiplier = 1.15 if buy_type == "INSTITUTIONAL_BUY" else 1.0

        score = (volume_score + price_score) * multiplier
        return min(score, 100)  # Cap at 100


class MomentumDetector:
    """Main detector for momentum signals"""

    def __init__(self, volume_multiplier: float = 5.0, price_threshold: float = 10.0):
        self.volume_multiplier = volume_multiplier
        self.price_threshold = price_threshold

    def detect_momentum(
        self,
        ticker: str,
        hourly_data: pd.DataFrame,
        previous_close: float,
        avg_30day_volume: float,
        has_positive_news: bool = False,
        pr_link: Optional[str] = None,
        pr_summary: Optional[str] = None
    ) -> Dict:
        """
        Main function to detect momentum signal
        Returns a dict with all analysis details
        """

        result = {
            'ticker': ticker,
            'momentum_detected': False,
            'buy_type': 'NONE',
            'score': 0,
            'details': {}
        }

        if hourly_data is None or hourly_data.empty:
            return result

        try:
            # Analyze volume
            has_volume_spike, relative_volume, latest_volume = VolumeAnalyzer.analyze_volume_spike(
                hourly_data,
                self.volume_multiplier
            )

            # Analyze price
            price_action = PriceAnalyzer.get_hourly_price_action(hourly_data)
            current_price = price_action.get('close', 0)

            has_price_increase = PriceAnalyzer.check_price_increase(
                current_price,
                previous_close,
                self.price_threshold
            )

            price_increase = PriceAnalyzer.get_price_change_percent(current_price, previous_close)

            # Classify buying pattern
            buy_type, analysis = BuyingPatternAnalyzer.classify_buy_type(
                has_volume_spike,
                relative_volume,
                price_increase,
                has_positive_news,
                pr_link
            )

            # Calculate momentum score
            momentum_score = BuyingPatternAnalyzer.calculate_momentum_score(
                relative_volume,
                price_increase,
                buy_type
            )

            # Populate result
            momentum_detected = (has_volume_spike and has_price_increase)

            result = {
                'ticker': ticker,
                'momentum_detected': momentum_detected,
                'buy_type': buy_type if momentum_detected else 'NONE',
                'score': momentum_score if momentum_detected else 0,
                'details': {
                    'volume_spike': has_volume_spike,
                    'relative_volume': round(relative_volume, 2),
                    'latest_volume': int(latest_volume),
                    'avg_30day_volume': int(avg_30day_volume),
                    'price_increase_percent': round(price_increase, 2),
                    'current_price': round(current_price, 2),
                    'previous_close': round(previous_close, 2),
                    'price_action': price_action,
                    'has_positive_news': has_positive_news,
                    'pr_link': pr_link,
                    'pr_summary': pr_summary
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error detecting momentum for {ticker}: {e}")
            return result
