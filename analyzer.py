"""
Analyzer Module - Identifies institutional accumulation patterns using
volume, price structure, and candlestick signals.

Seven signals (Wyckoff / smart-money framework):
  1. Absorption candle        – high volume + small real body
  2. Repeated lower wicks     – buyers defending support
  3. Sideways consolidation   – quiet accumulation in a range
  4. Volume breakout          – price breaks resistance with volume
  5. Volume at key support    – volume spike near prior lows
  6. Bullish reversal + vol   – engulfing / hammer with volume
  7. VWAP support             – price above / rebounding from VWAP
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Candle geometry helpers
# ---------------------------------------------------------------------------

def _body(c: pd.Series) -> float:
    return abs(float(c['Close']) - float(c['Open']))


def _range(c: pd.Series) -> float:
    return float(c['High']) - float(c['Low'])


def _lower_wick(c: pd.Series) -> float:
    return min(float(c['Close']), float(c['Open'])) - float(c['Low'])


def _upper_wick(c: pd.Series) -> float:
    return float(c['High']) - max(float(c['Close']), float(c['Open']))


def _vwap(df: pd.DataFrame) -> pd.Series:
    """Cumulative VWAP over the supplied dataframe."""
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    cumvol = df['Volume'].cumsum()
    cumtpv = (typical * df['Volume']).cumsum()
    return cumtpv / cumvol.replace(0, np.nan)


# ---------------------------------------------------------------------------
# Individual signal detectors
# Each returns (triggered: bool, score: float, detail: dict)
# ---------------------------------------------------------------------------

class InstitutionalSignals:
    """Seven institutional-accumulation signal detectors."""

    # Signal 1 – Absorption candle
    @staticmethod
    def absorption_candle(
        df: pd.DataFrame,
        vol_mult: float = 2.0
    ) -> Tuple[bool, float, dict]:
        """High volume + small real body = institutions absorbing sell pressure. Up to 20 pts."""
        if len(df) < 5:
            return False, 0.0, {}
        latest = df.iloc[-1]
        avg_vol = df['Volume'].iloc[:-1].mean()
        rel_vol = float(latest['Volume']) / avg_vol if avg_vol > 0 else 0.0
        rng = _range(latest)
        body_ratio = _body(latest) / rng if rng > 0 else 1.0
        triggered = rel_vol >= vol_mult and body_ratio <= 0.35
        score = 0.0
        if triggered:
            score = min(20.0, 10.0 + (rel_vol - vol_mult) * 2.0 + (0.35 - body_ratio) * 25.0)
        return triggered, round(score, 1), {
            'rel_vol': round(rel_vol, 2),
            'body_ratio': round(body_ratio, 2),
        }

    # Signal 2 – Repeated lower wicks
    @staticmethod
    def repeated_lower_wicks(
        df: pd.DataFrame,
        lookback: int = 10,
        min_count: int = 3
    ) -> Tuple[bool, float, dict]:
        """Multiple candles with long lower wicks = buyers defending support. Up to 15 pts."""
        if len(df) < lookback:
            return False, 0.0, {}
        window = df.iloc[-lookback:]
        count = 0
        for _, row in window.iterrows():
            rng = _range(row)
            if rng <= 0:
                continue
            lw = _lower_wick(row)
            body = _body(row)
            if lw > 0.5 * rng and lw >= 2.0 * max(body, 1e-8):
                count += 1
        triggered = count >= min_count
        score = min(15.0, count * 3.0) if triggered else 0.0
        return triggered, score, {'lower_wick_candles': count}

    # Signal 3 – Sideways consolidation
    @staticmethod
    def sideways_consolidation(
        df: pd.DataFrame,
        lookback: int = 20,
        max_range_pct: float = 4.0
    ) -> Tuple[bool, float, dict]:
        """Tight price range with rising volume = quiet accumulation. Up to 15 pts."""
        if len(df) < lookback:
            return False, 0.0, {}
        window = df.iloc[-lookback:]
        hi = float(window['High'].max())
        lo = float(window['Low'].min())
        range_pct = (hi - lo) / lo * 100.0 if lo > 0 else 999.0
        vol_slope = float(np.polyfit(range(len(window)), window['Volume'].values, 1)[0])
        triggered = range_pct <= max_range_pct
        score = 0.0
        if triggered:
            score = min(15.0, (max_range_pct - range_pct) * 3.0 + (5.0 if vol_slope > 0 else 0.0))
        return triggered, round(score, 1), {
            'range_pct': round(range_pct, 2),
            'vol_trend': 'rising' if vol_slope > 0 else 'flat/falling',
        }

    # Signal 4 – Volume breakout
    @staticmethod
    def volume_breakout(
        df: pd.DataFrame,
        lookback: int = 20,
        vol_mult: float = 2.0
    ) -> Tuple[bool, float, dict]:
        """Close breaks above prior-N-bar resistance on elevated volume. Up to 25 pts."""
        if len(df) < lookback + 1:
            return False, 0.0, {}
        prior = df.iloc[-(lookback + 1):-1]
        latest = df.iloc[-1]
        resistance = float(prior['High'].max())
        avg_vol = float(prior['Volume'].mean())
        rel_vol = float(latest['Volume']) / avg_vol if avg_vol > 0 else 0.0
        latest_close = float(latest['Close'])
        triggered = latest_close > resistance and rel_vol >= vol_mult
        score = 0.0
        if triggered:
            breakout_pct = (latest_close - resistance) / resistance * 100.0
            score = min(25.0, 15.0 + breakout_pct * 2.0 + (rel_vol - vol_mult) * 2.0)
        return triggered, round(score, 1), {
            'resistance': round(resistance, 2),
            'breakout_pct': round((latest_close - resistance) / resistance * 100.0, 2),
            'rel_vol': round(rel_vol, 2),
        }

    # Signal 5 – Volume at key support
    @staticmethod
    def volume_at_support(
        df: pd.DataFrame,
        lookback: int = 20,
        proximity_pct: float = 2.0,
        vol_mult: float = 2.0
    ) -> Tuple[bool, float, dict]:
        """Volume spike while price is near a key support / demand zone. Up to 15 pts."""
        if len(df) < lookback + 1:
            return False, 0.0, {}
        prior = df.iloc[-(lookback + 1):-1]
        latest = df.iloc[-1]
        support = float(prior['Low'].min())
        avg_vol = float(prior['Volume'].mean())
        rel_vol = float(latest['Volume']) / avg_vol if avg_vol > 0 else 0.0
        latest_close = float(latest['Close'])
        dist_pct = (latest_close - support) / support * 100.0 if support > 0 else 999.0
        near_support = dist_pct <= proximity_pct
        triggered = near_support and rel_vol >= vol_mult
        score = min(15.0, 8.0 + rel_vol * 2.0) if triggered else 0.0
        return triggered, round(score, 1), {
            'support': round(support, 2),
            'distance_pct': round(dist_pct, 2),
            'rel_vol': round(rel_vol, 2),
        }

    # Signal 6 – Bullish engulfing / hammer with volume
    @staticmethod
    def bullish_reversal_with_volume(
        df: pd.DataFrame,
        vol_mult: float = 1.5
    ) -> Tuple[bool, float, dict]:
        """Bullish engulfing or hammer candle with above-average volume. Up to 20 pts."""
        if len(df) < 3:
            return False, 0.0, {}
        prev = df.iloc[-2]
        latest = df.iloc[-1]
        avg_vol = df['Volume'].iloc[:-1].mean()
        rel_vol = float(latest['Volume']) / avg_vol if avg_vol > 0 else 0.0
        high_vol = rel_vol >= vol_mult

        prev_bearish = float(prev['Close']) < float(prev['Open'])
        latest_bullish = float(latest['Close']) > float(latest['Open'])
        engulfing = (
            prev_bearish and latest_bullish
            and float(latest['Open']) <= float(prev['Close'])
            and float(latest['Close']) >= float(prev['Open'])
        )

        rng = _range(latest)
        body = _body(latest)
        lw = _lower_wick(latest)
        hammer = rng > 0 and lw >= 2.0 * max(body, 1e-8) and body <= 0.35 * rng

        triggered = high_vol and (engulfing or hammer)
        pattern = ('engulfing' if engulfing else 'hammer') if triggered else None
        score = min(20.0, 12.0 + rel_vol * 2.0) if triggered else 0.0

        return triggered, round(score, 1), {
            'pattern': pattern,
            'rel_vol': round(rel_vol, 2),
        }

    # Signal 7 – VWAP support
    @staticmethod
    def vwap_support(df: pd.DataFrame) -> Tuple[bool, float, dict]:
        """Price above VWAP and/or rebounding from VWAP. Up to 15 pts."""
        if len(df) < 5:
            return False, 0.0, {}
        vwap_s = _vwap(df)
        latest_close = float(df['Close'].iloc[-1])
        latest_vwap = float(vwap_s.iloc[-1])
        if latest_vwap <= 0 or np.isnan(latest_vwap):
            return False, 0.0, {}
        above_vwap = latest_close > latest_vwap
        prev_close = float(df['Close'].iloc[-2])
        prev_vwap = float(vwap_s.iloc[-2])
        rebound = (not np.isnan(prev_vwap)) and prev_close <= prev_vwap and latest_close > latest_vwap
        triggered = above_vwap
        score = (10.0 + (5.0 if rebound else 0.0)) if triggered else 0.0
        return triggered, score, {
            'vwap': round(latest_vwap, 2),
            'price': round(latest_close, 2),
            'rebound_from_vwap': rebound,
        }


# ---------------------------------------------------------------------------
# Backward-compat wrappers (used by scanner.py / tests)
# ---------------------------------------------------------------------------

class VolumeAnalyzer:
    @staticmethod
    def get_relative_volume(current_volume: float, avg_volume: float) -> float:
        if avg_volume <= 0:
            return 0.0
        return current_volume / avg_volume

    @staticmethod
    def analyze_volume_spike(
        hourly_data: pd.DataFrame,
        multiplier: float = 2.0
    ) -> Tuple[bool, float, float]:
        if hourly_data is None or hourly_data.empty or len(hourly_data) < 2:
            return False, 0.0, 0.0
        latest_vol = float(hourly_data['Volume'].iloc[-1])
        avg_vol = float(hourly_data['Volume'].mean())
        rel_vol = VolumeAnalyzer.get_relative_volume(latest_vol, avg_vol)
        return rel_vol >= multiplier, rel_vol, latest_vol


class PriceAnalyzer:
    @staticmethod
    def get_price_change_percent(current_price: float, previous_price: float) -> float:
        if previous_price <= 0:
            return 0.0
        return ((current_price - previous_price) / previous_price) * 100.0

    @staticmethod
    def get_hourly_price_action(hourly_data: pd.DataFrame) -> Dict[str, float]:
        if hourly_data is None or hourly_data.empty:
            return {}
        c = hourly_data.iloc[-1]
        open_ = float(c['Open'])
        close_ = float(c['Close'])
        return {
            'close': close_,
            'open': open_,
            'high': float(c['High']),
            'low': float(c['Low']),
            'intra_hour_change': ((close_ - open_) / open_ * 100.0) if open_ > 0 else 0.0,
            'range': float(c['High']) - float(c['Low']),
        }


# ---------------------------------------------------------------------------
# MomentumDetector  (public API – signature unchanged)
# ---------------------------------------------------------------------------

class MomentumDetector:
    """
    Detects institutional accumulation using seven price/volume signals.

    Composite score (max 100 pts):
      Volume breakout          <= 25 pts  (strongest – phase-change confirmed)
      Absorption candle        <= 20 pts
      Bullish reversal + vol   <= 20 pts
      Sideways consolidation   <= 15 pts
      Repeated lower wicks     <= 15 pts
      Volume at support        <= 15 pts
      VWAP support             <= 15 pts

    momentum_detected = score >= min_score  AND  >= 2 signals fired
    """

    def __init__(
        self,
        volume_multiplier: float = 2.0,
        price_threshold: float = 3.0,   # kept for API compat; used in reporting only
        min_score: float = 30.0,
    ):
        self.volume_multiplier = volume_multiplier
        self.price_threshold = price_threshold
        self.min_score = min_score

    def detect_momentum(
        self,
        ticker: str,
        hourly_data: pd.DataFrame,
        previous_close: float,
        avg_30day_volume: float,
        has_positive_news: bool = False,
        pr_link: Optional[str] = None,
        pr_summary: Optional[str] = None,
    ) -> Dict:
        result = {
            'ticker': ticker,
            'momentum_detected': False,
            'buy_type': 'NONE',
            'score': 0,
            'details': {},
        }

        if hourly_data is None or hourly_data.empty or len(hourly_data) < 5:
            return result

        try:
            sig = InstitutionalSignals
            vm = self.volume_multiplier

            s1, sc1, d1 = sig.absorption_candle(hourly_data, vm)
            s2, sc2, d2 = sig.repeated_lower_wicks(hourly_data)
            s3, sc3, d3 = sig.sideways_consolidation(hourly_data)
            s4, sc4, d4 = sig.volume_breakout(hourly_data, vol_mult=vm)
            s5, sc5, d5 = sig.volume_at_support(hourly_data, vol_mult=vm)
            s6, sc6, d6 = sig.bullish_reversal_with_volume(hourly_data, vm)
            s7, sc7, d7 = sig.vwap_support(hourly_data)

            total_score = min(sc1 + sc2 + sc3 + sc4 + sc5 + sc6 + sc7, 100.0)
            signals_fired = sum([s1, s2, s3, s4, s5, s6, s7])
            momentum_detected = total_score >= self.min_score and signals_fired >= 2

            if not momentum_detected:
                buy_type = 'NONE'
            elif s4:
                buy_type = 'BREAKOUT_BUY'
            elif has_positive_news or pr_link:
                buy_type = 'RETAIL_BUY'
            else:
                buy_type = 'INSTITUTIONAL_ACCUMULATION'

            price_action = PriceAnalyzer.get_hourly_price_action(hourly_data)
            current_price = price_action.get('close', 0.0)
            price_change = PriceAnalyzer.get_price_change_percent(current_price, previous_close)
            _, rel_vol, latest_vol = VolumeAnalyzer.analyze_volume_spike(hourly_data, vm)

            result = {
                'ticker': ticker,
                'momentum_detected': momentum_detected,
                'buy_type': buy_type,
                'score': round(total_score, 1),
                'details': {
                    'signals_fired': signals_fired,
                    'volume_spike': s1 or s4 or s5,          # backward compat key
                    'relative_volume': round(rel_vol, 2),
                    'latest_volume': int(latest_vol),
                    'avg_30day_volume': int(avg_30day_volume),
                    'price_increase_percent': round(price_change, 2),
                    'current_price': round(current_price, 2),
                    'previous_close': round(previous_close, 2),
                    'price_action': price_action,
                    'has_positive_news': has_positive_news,
                    'pr_link': pr_link,
                    'pr_summary': pr_summary,
                    'signal_breakdown': {
                        'absorption_candle':      {'triggered': s1, 'score': sc1, **d1},
                        'repeated_lower_wicks':   {'triggered': s2, 'score': sc2, **d2},
                        'sideways_consolidation': {'triggered': s3, 'score': sc3, **d3},
                        'volume_breakout':        {'triggered': s4, 'score': sc4, **d4},
                        'volume_at_support':      {'triggered': s5, 'score': sc5, **d5},
                        'bullish_reversal':       {'triggered': s6, 'score': sc6, **d6},
                        'vwap_support':           {'triggered': s7, 'score': sc7, **d7},
                    },
                },
            }

            if momentum_detected:
                active = [k for k, v in result['details']['signal_breakdown'].items()
                          if v['triggered']]
                logger.info(
                    f"{ticker} | score={total_score:.1f}  type={buy_type}  signals={active}"
                )

            return result

        except Exception as e:
            logger.error(f"Error detecting momentum for {ticker}: {e}", exc_info=True)
            return result
