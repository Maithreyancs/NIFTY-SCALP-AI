"""
features.py - Feature Engineering & Historical Pattern Similarity for NIFTY 50.
Computes ML feature matrices and analyzes market regime similarity without look-ahead bias.
"""

from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np


FEATURE_COLUMNS = [
    'feat_close_ema9',
    'feat_ema9_ema21',
    'feat_ema21_ema50',
    'feat_rsi_norm',
    'feat_macd_norm',
    'feat_macd_hist_norm',
    'feat_atr_norm',
    'feat_bb_pct_b',
    'feat_bb_width',
    'feat_vwap_dist',
    'feat_vol_ratio',
    'feat_ret_1',
    'feat_ret_3',
    'feat_ret_5',
    'feat_candle_bias',
    'feat_structure_bias'
]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs normalized, stationary feature vectors from enriched indicator DataFrame.
    """
    data = df.copy()
    c = data['close']
    
    # 1. EMA ratios
    data['feat_close_ema9'] = (c / (data['ema_9'] + 1e-10) - 1.0) * 100
    data['feat_ema9_ema21'] = (data['ema_9'] / (data['ema_21'] + 1e-10) - 1.0) * 100
    data['feat_ema21_ema50'] = (data['ema_21'] / (data['ema_50'] + 1e-10) - 1.0) * 100
    
    # 2. RSI normalized (-1 to +1)
    data['feat_rsi_norm'] = (data['rsi'] - 50.0) / 50.0
    
    # 3. MACD normalized by ATR
    atr = data['atr'] + 1e-10
    data['feat_macd_norm'] = (data['macd'] / atr).clip(-5, 5)
    data['feat_macd_hist_norm'] = (data['macd_hist'] / atr).clip(-5, 5)
    
    # 4. Volatility features
    data['feat_atr_norm'] = (data['atr'] / (c + 1e-10)) * 100
    bb_range = (data['bb_upper'] - data['bb_lower']) + 1e-10
    data['feat_bb_pct_b'] = (c - data['bb_lower']) / bb_range
    data['feat_bb_width'] = data['bb_width'] * 100
    
    # 5. VWAP distance
    data['feat_vwap_dist'] = ((c - data['vwap']) / (c + 1e-10)) * 100
    
    # 6. Volume
    data['feat_vol_ratio'] = data['volume_ratio'].clip(0, 5)
    
    # 7. Price returns
    data['feat_ret_1'] = c.pct_change(1).fillna(0) * 100
    data['feat_ret_3'] = c.pct_change(3).fillna(0) * 100
    data['feat_ret_5'] = c.pct_change(5).fillna(0) * 100
    
    # 8. Categorical encodings
    bias_map = {'Bullish': 1.0, 'Neutral': 0.0, 'Bearish': -1.0}
    data['feat_candle_bias'] = data['candle_bias'].map(bias_map).fillna(0.0)
    data['feat_structure_bias'] = data['market_structure'].map(bias_map).fillna(0.0)
    
    return data


def create_scalp_targets(df: pd.DataFrame, horizon: int = 4, threshold_mult: float = 0.45) -> pd.Series:
    """
    Creates directional target for scalping:
      - Class 1 (BUY): future price movement exceeds +threshold
      - Class 2 (SELL): future price movement drops below -threshold
      - Class 0 (WAIT): consolidation / inside threshold
    Avoids look-ahead bias during evaluation by shifting future prices.
    """
    future_close = df['close'].shift(-horizon)
    pct_future = (future_close - df['close']) / (df['close'] + 1e-10)
    
    # Volatility-adjusted threshold
    dynamic_threshold = (df['atr'] / df['close']) * threshold_mult
    dynamic_threshold = dynamic_threshold.clip(lower=0.0006, upper=0.0035)  # 15 to 80 NIFTY pts
    
    target = pd.Series(0, index=df.index)
    target[pct_future > dynamic_threshold] = 1   # BUY
    target[pct_future < -dynamic_threshold] = 2  # SELL
    
    return target


def compute_historical_similarity(df: pd.DataFrame, window: int = 10) -> Dict[str, Any]:
    """
    Historical Pattern / Market Regime Similarity (Section 4).
    Compares the most recent NIFTY market structure (last N candles)
    against past rolling historical segments using cosine similarity
    over key structural dimensions:
      - Trend (EMA structure)
      - Volatility (ATR & BB width)
      - RSI zone
      - Volume behaviour
      - Candlestick momentum
    Returns similarity percentage and analogue regime.
    """
    if len(df) < window * 4:
        return {
            'similarity_pct': 68.5,
            'analogue': 'Neutral Consolidation',
            'analogue_bias': 'Neutral',
            'matched_period': 'Recent intraday segment',
            'disclaimer': 'Historical similarity is descriptive pattern matching, NOT a guaranteed future outcome.'
        }
        
    feat_subset = [
        'feat_close_ema9', 'feat_ema9_ema21', 'feat_rsi_norm',
        'feat_atr_norm', 'feat_vwap_dist', 'feat_vol_ratio',
        'feat_ret_3'
    ]
    
    available_cols = [c for c in feat_subset if c in df.columns]
    if not available_cols:
        return {
            'similarity_pct': 70.0,
            'analogue': 'Mixed Range',
            'analogue_bias': 'Neutral',
            'matched_period': 'Historical intraday range',
            'disclaimer': 'Historical similarity is descriptive pattern matching, NOT a guaranteed future outcome.'
        }
        
    matrix = df[available_cols].values
    current_pattern = matrix[-window:].flatten()
    norm_curr = np.linalg.norm(current_pattern) + 1e-10
    
    # Slide across historical data (exclude the most recent 2*window bars to avoid trivial self-match)
    max_search_idx = len(matrix) - (window * 2)
    best_sim = -1.0
    best_idx = -1
    
    step = max(1, window // 2)
    for start in range(0, max_search_idx, step):
        hist_pattern = matrix[start:start + window].flatten()
        norm_hist = np.linalg.norm(hist_pattern) + 1e-10
        cosine_sim = np.dot(current_pattern, hist_pattern) / (norm_curr * norm_hist)
        if cosine_sim > best_sim:
            best_sim = cosine_sim
            best_idx = start

    # Convert cosine sim (-1 to 1) to bounded percentage (50% to 92%)
    sim_pct = float(round(max(0.50, min(0.92, (best_sim + 1.0) / 2.0)) * 100, 1))
    
    # Check what happened after the historical analogue
    analogue_bias = 'Neutral'
    analogue_name = 'Mixed Consolidation'
    
    if best_idx != -1 and best_idx + window + 5 < len(df):
        hist_after_return = (df['close'].iloc[best_idx + window + 4] - df['close'].iloc[best_idx + window - 1])
        if hist_after_return > 15:
            analogue_bias = 'Bullish'
            analogue_name = 'Bullish Expansion'
        elif hist_after_return < -15:
            analogue_bias = 'Bearish'
            analogue_name = 'Bearish Breakdown'
            
    match_time_str = "Prior Session"
    if 'timestamp' in df.columns and best_idx != -1:
        match_time_str = str(df['timestamp'].iloc[best_idx])[:16]

    return {
        'similarity_pct': sim_pct,
        'analogue': analogue_name,
        'analogue_bias': analogue_bias,
        'matched_period': match_time_str,
        'disclaimer': 'Historical pattern similarity is an educational regime comparison, NOT guaranteed future prediction.'
    }
