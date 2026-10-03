"""
indicators.py - Technical Indicators Engine for NIFTY 50 Scalping.
Calculates Trend, Momentum, Volatility, Volume, Price Levels, and Market Structure.
"""

import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal_span: int = 9):
    """Calculate MACD Line, Signal Line, and Histogram."""
    fast_ema = compute_ema(series, fast)
    slow_ema = compute_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, signal_span)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr


def compute_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    """Calculate Bollinger Bands (Middle, Upper, Lower, Bandwidth)."""
    middle = series.rolling(window=period, min_periods=1).mean()
    std = series.rolling(window=period, min_periods=1).std().fillna(0)
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = (upper - lower) / (middle + 1e-10)
    return upper, middle, lower, bandwidth


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Intraday Volume Weighted Average Price (VWAP).
    Resets at the start of each trading session if timestamps exist.
    """
    df_temp = df.copy()
    typical_price = (df_temp['high'] + df_temp['low'] + df_temp['close']) / 3.0
    tp_vol = typical_price * df_temp['volume']
    
    # Try grouping by date if timestamp column is available
    if 'timestamp' in df_temp.columns:
        dates = pd.to_datetime(df_temp['timestamp']).dt.date
        cum_tp_vol = tp_vol.groupby(dates).cumsum()
        cum_vol = df_temp['volume'].groupby(dates).cumsum()
    else:
        cum_tp_vol = tp_vol.cumsum()
        cum_vol = df_temp['volume'].cumsum()
        
    vwap = cum_tp_vol / (cum_vol + 1e-10)
    return vwap.fillna(df_temp['close'])


def compute_support_resistance(df: pd.DataFrame, window: int = 15):
    """
    Calculate dynamic support and resistance using swing highs and swing lows.
    Also returns previous high, previous low, intraday high, and intraday low.
    """
    rolling_high = df['high'].rolling(window=window, min_periods=1).max()
    rolling_low = df['low'].rolling(window=window, min_periods=1).min()
    
    # Intraday extrema
    if 'timestamp' in df.columns:
        dates = pd.to_datetime(df['timestamp']).dt.date
        intraday_high = df.groupby(dates)['high'].cummax()
        intraday_low = df.groupby(dates)['low'].cummin()
    else:
        intraday_high = df['high'].cummax()
        intraday_low = df['low'].cummin()
        
    prev_high = df['high'].shift(1)
    prev_low = df['low'].shift(1)
    
    return rolling_high, rolling_low, intraday_high, intraday_low, prev_high, prev_low


def detect_hh_hl_structure(df: pd.DataFrame, lookback: int = 5):
    """
    Analyze Higher High / Higher Low (Bullish) or Lower High / Lower Low (Bearish).
    """
    highs = df['high']
    lows = df['low']
    
    hh = (highs > highs.shift(lookback)).astype(int)
    hl = (lows > lows.shift(lookback)).astype(int)
    lh = (highs < highs.shift(lookback)).astype(int)
    ll = (lows < lows.shift(lookback)).astype(int)
    
    structure_score = (hh + hl) - (lh + ll)
    return structure_score


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich OHLCV DataFrame with complete suite of technical indicators for NIFTY 50.
    """
    data = df.copy()
    if len(data) == 0:
        return data

    close = data['close']
    
    # 1. Trend Indicators
    data['ema_9'] = compute_ema(close, 9)
    data['ema_21'] = compute_ema(close, 21)
    data['ema_50'] = compute_ema(close, 50)
    
    # Trend direction & strength
    ema_bullish = (data['ema_9'] > data['ema_21']) & (close > data['ema_21'])
    ema_bearish = (data['ema_9'] < data['ema_21']) & (close < data['ema_21'])
    data['trend_direction'] = np.where(ema_bullish, 'Bullish', np.where(ema_bearish, 'Bearish', 'Neutral'))
    
    divergence = (data['ema_9'] - data['ema_21']).abs() / (close + 1e-10) * 1000
    data['trend_strength'] = (divergence * 15).clip(10, 95).round(1)
    
    # 2. Momentum
    data['rsi'] = compute_rsi(close, 14)
    macd, signal, hist = compute_macd(close, 12, 26, 9)
    data['macd'] = macd
    data['macd_signal'] = signal
    data['macd_hist'] = hist
    data['momentum'] = close.diff(5).fillna(0)
    
    # 3. Volatility
    data['atr'] = compute_atr(data, 14)
    bb_upper, bb_mid, bb_lower, bb_width = compute_bollinger_bands(close, 20, 2.0)
    data['bb_upper'] = bb_upper
    data['bb_middle'] = bb_mid
    data['bb_lower'] = bb_lower
    data['bb_width'] = bb_width
    data['candle_range'] = data['high'] - data['low']
    
    # Volatility Regime
    atr_median = data['atr'].rolling(window=50, min_periods=5).median()
    atr_ratio = data['atr'] / (atr_median + 1e-10)
    data['volatility_regime'] = np.where(
        atr_ratio > 1.6, 'Extreme',
        np.where(atr_ratio > 1.2, 'High',
                 np.where(atr_ratio < 0.8, 'Low', 'Normal'))
    )
    
    # 4. Volume
    vol = data['volume']
    data['vol_sma_20'] = vol.rolling(window=20, min_periods=1).mean()
    data['volume_ratio'] = (vol / (data['vol_sma_20'] + 1e-10)).round(2)
    data['volume_spike'] = data['volume_ratio'] > 1.8
    
    # 5. Price Levels & VWAP
    data['vwap'] = compute_vwap(data)
    res, sup, intra_h, intra_l, prev_h, prev_l = compute_support_resistance(data)
    data['resistance'] = res
    data['support'] = sup
    data['intraday_high'] = intra_h
    data['intraday_low'] = intra_l
    data['prev_high'] = prev_h
    data['prev_low'] = prev_l
    
    # 6. Market Structure
    data['structure_score'] = detect_hh_hl_structure(data)
    data['market_structure'] = np.where(
        data['structure_score'] > 0, 'Bullish',
        np.where(data['structure_score'] < 0, 'Bearish', 'Neutral')
    )
    
    return data
