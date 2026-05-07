"""
Chart Generator Module - Creates professional candlestick charts with volume
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class CandleChart:
    """Generates professional candlestick charts"""

    # Colors
    COLOR_UP = '#00ff00'      # Green for bullish
    COLOR_DOWN = '#ff3333'    # Red for bearish
    COLOR_HIGHLIGHT = '#ffff00'  # Yellow for institutional buy signal
    COLOR_SUPPORT = '#00bcd4'  # Cyan support line
    COLOR_RESISTANCE = '#ff9800'  # Orange resistance line
    COLOR_VOLUME_UP = '#00ff00'   # Green volume
    COLOR_VOLUME_DOWN = '#ff3333' # Red volume
    COLOR_BACKGROUND = '#000000'  # Black background
    COLOR_GRID = '#333333'        # Dark gray grid
    COLOR_TEXT = '#ffffff'        # White text

    def __init__(self, width: float = 16, height: float = 9):
        """Initialize chart generator"""
        self.width = width
        self.height = height
        self.fig = None
        self.ax_candle = None
        self.ax_volume = None

    def create_sample_data(self, hours: int = 40, start_price: float = 100.0, 
                          highlight_position: int = None) -> Tuple[pd.DataFrame, int]:
        """
        Create sample 40-hour candlestick data with institutional buying pattern
        
        Returns: (DataFrame, highlight_bar_index)
        """
        data = []
        current_price = start_price
        
        for i in range(hours):
            # Generate realistic OHLCV data
            open_price = current_price
            
            # Random walk
            change = np.random.uniform(-0.5, 0.5)  # -0.5% to +0.5% per hour
            
            # Create bigger move at highlight position (institutional buy)
            if highlight_position is not None and i == highlight_position:
                change = np.random.uniform(0.8, 1.2)  # Strong upward move
                volume = np.random.uniform(8_000_000, 12_000_000)  # High volume
            else:
                volume = np.random.uniform(1_000_000, 2_500_000)  # Normal volume
            
            close_price = open_price * (1 + change / 100)
            high_price = max(open_price, close_price) * (1 + abs(np.random.uniform(0, 0.3)) / 100)
            low_price = min(open_price, close_price) * (1 - abs(np.random.uniform(0, 0.3)) / 100)
            
            timestamp = datetime.now() - timedelta(hours=hours - i - 1)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        df = pd.DataFrame(data)
        
        # Auto-detect institutional buy if not specified
        if highlight_position is None:
            # Find highest volume + biggest up candle
            df['up_move'] = (df['close'] > df['open']).astype(int)
            df['move_pct'] = ((df['close'] - df['open']) / df['open'] * 100).abs()
            df['signal_strength'] = df['volume'] / df['volume'].mean() * (df['move_pct'] / df['move_pct'].mean())
            highlight_position = df['signal_strength'].idxmax()
        
        return df, highlight_position

    def generate_chart(self, df: pd.DataFrame, highlight_position: int, 
                      ticker: str = "MOMENTUM", signal_type: str = "INSTITUTIONAL_BUY",
                      momentum_score: float = 78.5, output_path: str = None) -> str:
        """
        Generate candlestick chart with volume
        
        Parameters:
            df: DataFrame with OHLCV data
            highlight_position: Index of institutional buy candle
            ticker: Stock ticker
            signal_type: "INSTITUTIONAL_BUY" or "RETAIL_BUY"
            momentum_score: 0-100 momentum score
            output_path: Where to save the chart
        
        Returns:
            Path to saved PNG file
        """
        
        if output_path is None:
            output_path = f"data/charts/{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create figure with two subplots (candles and volume)
        self.fig, (self.ax_candle, self.ax_volume) = plt.subplots(
            2, 1, 
            figsize=(self.width, self.height),
            gridspec_kw={'height_ratios': [3, 1]},
            facecolor=self.COLOR_BACKGROUND
        )
        
        # Set backgrounds
        self.ax_candle.set_facecolor(self.COLOR_BACKGROUND)
        self.ax_volume.set_facecolor(self.COLOR_BACKGROUND)
        
        # X-axis positions
        x_pos = np.arange(len(df))
        
        # Plot candlesticks
        self._plot_candlesticks(df, x_pos, highlight_position)

        # Plot support/resistance levels
        self._plot_key_levels(df)
        
        # Plot volume
        self._plot_volume(df, x_pos, highlight_position)
        
        # Format axes
        self._format_axes(df, x_pos, signal_type, ticker, momentum_score)
        
        # Add title and info
        self._add_labels(ticker, signal_type, momentum_score, df, highlight_position)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        plt.savefig(output_path, dpi=100, facecolor=self.COLOR_BACKGROUND, edgecolor='none')
        logger.info(f"Chart saved to {output_path}")
        
        plt.close(self.fig)
        
        return output_path

    def _plot_candlesticks(self, df: pd.DataFrame, x_pos: np.ndarray, highlight_pos: int):
        """Plot candlestick chart"""
        
        width = 0.6
        
        for i, (idx, row) in enumerate(df.iterrows()):
            open_price = row['open']
            close_price = row['close']
            high_price = row['high']
            low_price = row['low']
            
            # Determine color
            if i == highlight_pos:
                # Highlight institutional buy candle
                body_color = self.COLOR_HIGHLIGHT
                wick_color = self.COLOR_HIGHLIGHT
                edge_color = '#ffffff'
                edge_width = 2.5
            elif close_price >= open_price:
                body_color = self.COLOR_UP
                wick_color = self.COLOR_UP
                edge_color = self.COLOR_UP
                edge_width = 0.5
            else:
                body_color = self.COLOR_DOWN
                wick_color = self.COLOR_DOWN
                edge_color = self.COLOR_DOWN
                edge_width = 0.5
            
            # Draw wick (high-low)
            self.ax_candle.plot([x_pos[i], x_pos[i]], [low_price, high_price], 
                               color=wick_color, linewidth=1.5, zorder=1)
            
            # Draw body (open-close)
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            rect = Rectangle((x_pos[i] - width/2, body_bottom), width, body_height,
                            facecolor=body_color, edgecolor=edge_color, 
                            linewidth=edge_width, zorder=2)
            self.ax_candle.add_patch(rect)
        
        # Set candlestick axis limits with padding
        prices = pd.concat([df['high'], df['low']])
        price_range = prices.max() - prices.min()
        padding = price_range * 0.1
        
        self.ax_candle.set_ylim(prices.min() - padding, prices.max() + padding)
        self.ax_candle.set_xlim(-1, len(df))

    def _plot_volume(self, df: pd.DataFrame, x_pos: np.ndarray, highlight_pos: int):
        """Plot volume bars"""
        
        width = 0.6
        
        for i, (idx, row) in enumerate(df.iterrows()):
            volume = row['volume']
            
            # Color based on candle direction
            if df['close'].iloc[i] >= df['open'].iloc[i]:
                color = self.COLOR_VOLUME_UP
                alpha = 0.4
            else:
                color = self.COLOR_VOLUME_DOWN
                alpha = 0.4
            
            # Highlight volume bar for institutional buy
            if i == highlight_pos:
                color = self.COLOR_HIGHLIGHT
                alpha = 0.8
            
            self.ax_volume.bar(x_pos[i], volume, width=width, 
                              color=color, alpha=alpha, edgecolor='none')
        
        self.ax_volume.set_ylim(0, df['volume'].max() * 1.2)
        self.ax_volume.set_xlim(-1, len(df))

    def _plot_key_levels(self, df: pd.DataFrame):
        """Draw support and resistance levels from recent candles."""
        if len(df) < 10:
            return

        recent = df.iloc[-min(20, len(df)):]
        support = float(recent['low'].min())
        resistance = float(recent['high'].max())

        self.ax_candle.axhline(
            support,
            color=self.COLOR_SUPPORT,
            linestyle='--',
            linewidth=1.2,
            alpha=0.85,
            label=f'Support {support:.2f}'
        )
        self.ax_candle.axhline(
            resistance,
            color=self.COLOR_RESISTANCE,
            linestyle='--',
            linewidth=1.2,
            alpha=0.85,
            label=f'Resistance {resistance:.2f}'
        )

        self.ax_candle.legend(
            loc='upper left',
            fontsize=8,
            facecolor=self.COLOR_BACKGROUND,
            edgecolor=self.COLOR_GRID,
            labelcolor=self.COLOR_TEXT,
        )

    def _format_axes(self, df: pd.DataFrame, x_pos: np.ndarray, 
                    signal_type: str, ticker: str, momentum_score: float):
        """Format chart axes"""
        
        # Candlestick axis
        self.ax_candle.set_ylabel('Price ($)', color=self.COLOR_TEXT, fontsize=12, fontweight='bold')
        self.ax_candle.grid(True, alpha=0.2, color=self.COLOR_GRID, linestyle='--')
        self.ax_candle.tick_params(colors=self.COLOR_TEXT, labelsize=10)
        
        # Set X labels (show every 4-5 hours)
        label_interval = max(1, len(df) // 8)
        x_labels = [df['timestamp'].iloc[i].strftime('%H:%M') if i % label_interval == 0 else '' 
                   for i in range(len(df))]
        self.ax_candle.set_xticks(x_pos)
        self.ax_candle.set_xticklabels(x_labels, rotation=45, ha='right')
        
        # Remove top/right spines
        self.ax_candle.spines['top'].set_visible(False)
        self.ax_candle.spines['right'].set_visible(False)
        self.ax_candle.spines['left'].set_color(self.COLOR_GRID)
        self.ax_candle.spines['bottom'].set_color(self.COLOR_GRID)
        
        # Volume axis
        self.ax_volume.set_ylabel('Volume', color=self.COLOR_TEXT, fontsize=11, fontweight='bold')
        self.ax_volume.set_xlabel('Time (1-Hour Candles)', color=self.COLOR_TEXT, fontsize=11, fontweight='bold')
        self.ax_volume.grid(True, alpha=0.1, color=self.COLOR_GRID, linestyle='--', axis='y')
        self.ax_volume.tick_params(colors=self.COLOR_TEXT, labelsize=9)
        
        # Format volume labels
        def format_volume(x, pos):
            if x >= 1_000_000:
                return f'{x/1_000_000:.0f}M'
            elif x >= 1_000:
                return f'{x/1_000:.0f}K'
            return f'{x:.0f}'
        
        from matplotlib.ticker import FuncFormatter
        self.ax_volume.yaxis.set_major_formatter(FuncFormatter(format_volume))
        
        # Remove top/right spines
        self.ax_volume.spines['top'].set_visible(False)
        self.ax_volume.spines['right'].set_visible(False)
        self.ax_volume.spines['left'].set_color(self.COLOR_GRID)
        self.ax_volume.spines['bottom'].set_color(self.COLOR_GRID)
        
        # Set X labels same as candle chart
        self.ax_volume.set_xticks(x_pos)
        self.ax_volume.set_xticklabels(x_labels, rotation=45, ha='right')

    def _add_labels(self, ticker: str, signal_type: str, 
                   momentum_score: float, df: pd.DataFrame, highlight_pos: int):
        """Add title and information labels"""
        
        # Title
        signal_label = "INSTITUTIONAL BUY" if signal_type == "INSTITUTIONAL_BUY" else "RETAIL BUY"
        title = f"{signal_label} - {ticker}"
        
        self.fig.suptitle(title, fontsize=20, fontweight='bold', 
                         color=self.COLOR_HIGHLIGHT, y=0.98)
        
        # Info box
        highlight_candle = df.iloc[highlight_pos]
        price_change = ((highlight_candle['close'] - highlight_candle['open']) / highlight_candle['open']) * 100
        volume_avg_ratio = highlight_candle['volume'] / df['volume'].mean()
        
        info_text = (
            f"Momentum Score: {momentum_score:.1f}/100  |  "
            f"Price Change: +{price_change:.2f}%  |  "
            f"Volume: {volume_avg_ratio:.1f}x average  |  "
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET"
        )
        
        # Add info as text annotation at top
        self.fig.text(0.5, 0.94, info_text, ha='center', fontsize=11, 
                     color=self.COLOR_TEXT, family='monospace',
                     bbox=dict(boxstyle='round', facecolor='#1a1a1a', 
                              edgecolor=self.COLOR_GRID, alpha=0.7))
        
        # Add legend
        legend_text = (
            "Chart: 40 × 1-hour candles | "
            f"Highlighted Candle: Institutional Buy Signal | "
            "Volume: Trading activity"
        )
        self.fig.text(0.5, 0.01, legend_text, ha='center', fontsize=9, 
                     color=self.COLOR_GRID, style='italic')


def create_momentum_chart(ticker: str, hourly_data: pd.DataFrame, 
                         signal_type: str = "INSTITUTIONAL_BUY",
                         momentum_score: float = 78.5,
                         highlight_position: int = None) -> str:
    """
    Convenience function to create a chart
    
    Parameters:
        ticker: Stock ticker
        hourly_data: DataFrame with OHLCV columns
        signal_type: "INSTITUTIONAL_BUY" or "RETAIL_BUY"  
        momentum_score: 0-100
        highlight_position: Position of signal candle (None = auto-detect)
    
    Returns:
        Path to saved PNG
    """
    
    # Ensure data is pandas DataFrame
    if isinstance(hourly_data, pd.DataFrame):
        df = hourly_data.copy()
    else:
        raise ValueError("hourly_data must be a pandas DataFrame")

    if 'timestamp' not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df['timestamp'] = df.index
        else:
            raise ValueError("hourly_data must include a timestamp column or DatetimeIndex")
    
    # Ensure required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            # Try to auto-rename from capitalized
            if col.capitalize() in df.columns:
                df.rename(columns={col.capitalize(): col}, inplace=True)
            else:
                raise ValueError(f"Missing required column: {col}")
    
    # Focus on the most recent 40 candles.
    if len(df) > 40:
        df = df.iloc[-40:].reset_index(drop=True)
    else:
        if len(df) < 40:
            logger.warning(
                f"{ticker} has only {len(df)} candles. Chart quality improves with at least 40 candles."
            )
        df = df.reset_index(drop=True)
    
    # Auto-find highlight position if not provided
    if highlight_position is None:
        # Scanner decisions are based on the latest candle, so highlight it by default.
        highlight_position = len(df) - 1
    
    chart_gen = CandleChart()
    output_path = f"data/charts/{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    return chart_gen.generate_chart(
        df, 
        highlight_position,
        ticker=ticker,
        signal_type=signal_type,
        momentum_score=momentum_score,
        output_path=output_path
    )
