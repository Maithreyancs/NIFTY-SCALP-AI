"""
candles.py - Candlestick Pattern Recognition for NIFTY 50 Scalping.
Calculates mathematical patterns directly from OHLC data.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes candlestick patterns for each row in the OHLC DataFrame.
    Returns DataFrame with 'candle_pattern' and 'candle_bias' columns.
    """
    data = df.copy()
    if len(data) < 3:
        data['candle_pattern'] = 'None'
        data['candle_bias'] = 'Neutral'
        return data

    o = data['open'].values
    h = data['high'].values
    l = data['low'].values
    c = data['close'].values

    n = len(data)
    patterns = ['None'] * n
    biases = ['Neutral'] * n

    for i in range(2, n):
        # Current candle properties
        body = abs(c[i] - o[i])
        c_range = max(h[i] - l[i], 1e-6)
        upper_wick = h[i] - max(o[i], c[i])
        lower_wick = min(o[i], c[i]) - l[i]
        is_bull = c[i] > o[i]
        is_bear = c[i] < o[i]

        # Prior candles properties
        prev_body = abs(c[i-1] - o[i-1])
        prev_range = max(h[i-1] - l[i-1], 1e-6)
        prev_is_bull = c[i-1] > o[i-1]
        prev_is_bear = c[i-1] < o[i-1]

        prev2_body = abs(c[i-2] - o[i-2])
        prev2_is_bull = c[i-2] > o[i-2]
        prev2_is_bear = c[i-2] < o[i-2]

        pattern = 'None'
        bias = 'Neutral'

        # 1. Morning Star (3-candle)
        if (prev2_is_bear and prev2_body > 0.5 * (h[i-2] - l[i-2]) and
            prev_body < 0.35 * prev_range and
            is_bull and c[i] > (o[i-2] + c[i-2]) / 2.0):
            pattern = 'Morning Star'
            bias = 'Bullish'

        # 2. Evening Star (3-candle)
        elif (prev2_is_bull and prev2_body > 0.5 * (h[i-2] - l[i-2]) and
              prev_body < 0.35 * prev_range and
              is_bear and c[i] < (o[i-2] + c[i-2]) / 2.0):
            pattern = 'Evening Star'
            bias = 'Bearish'

        # 3. Bullish Engulfing (2-candle)
        elif prev_is_bear and is_bull and (c[i] >= o[i-1]) and (o[i] <= c[i-1]):
            pattern = 'Bullish Engulfing'
            bias = 'Bullish'

        # 4. Bearish Engulfing (2-candle)
        elif prev_is_bull and is_bear and (c[i] <= o[i-1]) and (o[i] >= c[i-1]):
            pattern = 'Bearish Engulfing'
            bias = 'Bearish'

        # 5. Marubozu (1-candle)
        elif body >= 0.85 * c_range and upper_wick <= 0.08 * c_range and lower_wick <= 0.08 * c_range:
            if is_bull:
                pattern = 'Bullish Marubozu'
                bias = 'Bullish'
            else:
                pattern = 'Bearish Marubozu'
                bias = 'Bearish'

        # 6. Hammer (lower wick >= 2x body, tiny upper wick)
        elif lower_wick >= 2.0 * body and upper_wick <= 0.25 * body and body >= 0.1 * c_range:
            pattern = 'Hammer'
            bias = 'Bullish'

        # 7. Inverted Hammer (upper wick >= 2x body, tiny lower wick, after pullback)
        elif upper_wick >= 2.0 * body and lower_wick <= 0.25 * body and body >= 0.1 * c_range and c[i-1] <= c[i-2]:
            pattern = 'Inverted Hammer'
            bias = 'Bullish'

        # 8. Shooting Star (upper wick >= 2x body, tiny lower wick, at peak)
        elif upper_wick >= 2.0 * body and lower_wick <= 0.25 * body and body >= 0.1 * c_range and c[i-1] >= c[i-2]:
            pattern = 'Shooting Star'
            bias = 'Bearish'

        # 9. Doji (very thin body)
        elif body <= 0.10 * c_range and c_range > 0:
            pattern = 'Doji'
            bias = 'Neutral'

        patterns[i] = pattern
        biases[i] = bias

    data['candle_pattern'] = patterns
    data['candle_bias'] = biases
    return data


def get_latest_candle_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns summary of the latest detected candlestick for dashboard display.
    """
    if len(df) == 0:
        return {
            'pattern': 'None',
            'bias': 'Neutral',
            'open': 0.0,
            'high': 0.0,
            'low': 0.0,
            'close': 0.0,
            'volume': 0
        }

    last_row = df.iloc[-1]
    
    # If the exact last candle is None, check the previous one for relevant pattern context
    pattern = last_row.get('candle_pattern', 'None')
    bias = last_row.get('candle_bias', 'Neutral')
    
    if pattern == 'None' and len(df) > 1:
        prev_row = df.iloc[-2]
        if prev_row.get('candle_pattern', 'None') != 'None':
            pattern = f"{prev_row.get('candle_pattern')} (Prior)"
            bias = prev_row.get('candle_bias', 'Neutral')
            
    return {
        'pattern': pattern if pattern != 'None' else 'Standard Candle',
        'bias': bias,
        'open': float(round(last_row['open'], 2)),
        'high': float(round(last_row['high'], 2)),
        'low': float(round(last_row['low'], 2)),
        'close': float(round(last_row['close'], 2)),
        'volume': int(last_row['volume']) if 'volume' in last_row else 0
    }
