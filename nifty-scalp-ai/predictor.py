"""
predictor.py - Live NIFTY 50 Scalping Prediction Engine & Trade Plan Generator.
Integrates Multi-Timeframe analysis (1M/5M/15M), ML classification,
Volatility-based ATR risk modeling, and Candlestick patterns into actionable signals.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

from data_loader import get_nifty_data, analyze_opening_behaviour, get_macro_sentiment_context
from indicators import calculate_all_indicators
from candles import detect_candle_patterns, get_latest_candle_info
from features import extract_features, compute_historical_similarity, FEATURE_COLUMNS


MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'nifty_scalp_model.joblib')
METRICS_PATH = os.path.join(os.path.dirname(__file__), 'model', 'metrics.json')


def load_trained_model():
    """Safely loads serialized ML model if it exists."""
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


def get_multi_timeframe_analysis() -> Dict[str, Dict[str, str]]:
    """
    Computes directional trend and preliminary signal across 1M, 5M, and 15M timeframes.
    1M  = Entry & Scalping Timing
    5M  = Primary Scalping Trend
    15M = Higher-Timeframe (HTF) Trend & Bias
    """
    timeframes = ['1m', '5m', '15m']
    mtf_results = {}
    
    for tf in timeframes:
        try:
            df_raw, _ = get_nifty_data(tf)
            if len(df_raw) >= 25:
                df_ind = calculate_all_indicators(df_raw)
                last_row = df_ind.iloc[-1]
                trend = last_row.get('trend_direction', 'Neutral')
                rsi = last_row.get('rsi', 50.0)
                macd_hist = last_row.get('macd_hist', 0.0)
                
                # Preliminary directional stance for timeframe
                if trend == 'Bullish' and rsi > 48 and macd_hist >= -1.0:
                    sig = 'BUY'
                elif trend == 'Bearish' and rsi < 52 and macd_hist <= 1.0:
                    sig = 'SELL'
                else:
                    sig = 'WAIT'
                    
                mtf_results[tf] = {
                    'timeframe': tf.upper(),
                    'trend': trend,
                    'signal': sig,
                    'close': float(round(last_row['close'], 2)),
                    'ema9': float(round(last_row['ema_9'], 2)),
                    'ema21': float(round(last_row['ema_21'], 2))
                }
            else:
                mtf_results[tf] = {
                    'timeframe': tf.upper(),
                    'trend': 'Neutral',
                    'signal': 'WAIT',
                    'close': 0.0,
                    'ema9': 0.0,
                    'ema21': 0.0
                }
        except Exception:
            mtf_results[tf] = {
                'timeframe': tf.upper(),
                'trend': 'Neutral',
                'signal': 'WAIT',
                'close': 0.0,
                'ema9': 0.0,
                'ema21': 0.0
            }
            
    return mtf_results


def calculate_trade_plan(signal: str, current_price: float, atr: float, support: float, resistance: float) -> Dict[str, Any]:
    """
    Volatility-aware entry, stop loss, and target zones using ATR multipliers (Section 14).
    BUY:
      Entry = current_price to (current_price + 0.15*ATR)
      Stop Loss = Entry - 1.2 * ATR
      Target = Entry + 2.2 * ATR
    SELL:
      Entry = current_price to (current_price - 0.15*ATR)
      Stop Loss = Entry + 1.2 * ATR
      Target = Entry - 2.2 * ATR
    """
    atr = max(atr, 10.0)  # Minimum safety bounds for NIFTY
    
    if signal == 'BUY':
        entry_low = round(current_price - 0.05 * atr, 1)
        entry_high = round(current_price + 0.15 * atr, 1)
        entry_mid = round(current_price, 1)
        
        # Stop loss below support or Entry - 1.25 * ATR
        sl_calc = round(entry_mid - (1.25 * atr), 1)
        if support > 0 and support < entry_mid and (entry_mid - support) <= (1.5 * atr):
            sl = round(support - 5.0, 1)
        else:
            sl = sl_calc
            
        sl_low = round(sl - 5.0, 1)
        sl_high = round(sl + 5.0, 1)
        
        risk = entry_mid - sl
        target_dist = risk * 2.1
        target_mid = round(entry_mid + target_dist, 1)
        target_low = round(target_mid - 8.0, 1)
        target_high = round(target_mid + 8.0, 1)
        
        rr_ratio = round(target_dist / max(risk, 1.0), 2)
        
        return {
            'entry_zone': f"₹{entry_low:,.1f} – ₹{entry_high:,.1f}",
            'entry_price': entry_mid,
            'stop_loss_zone': f"₹{sl_low:,.1f} – ₹{sl_high:,.1f}",
            'stop_loss_price': sl,
            'target_zone': f"₹{target_low:,.1f} – ₹{target_high:,.1f}",
            'target_price': target_mid,
            'risk_points': round(risk, 1),
            'reward_points': round(target_dist, 1),
            'risk_reward': f"1 : {rr_ratio}",
            'rr_value': rr_ratio
        }

    elif signal == 'SELL':
        entry_low = round(current_price - 0.15 * atr, 1)
        entry_high = round(current_price + 0.05 * atr, 1)
        entry_mid = round(current_price, 1)
        
        # Stop loss above resistance or Entry + 1.25 * ATR
        sl_calc = round(entry_mid + (1.25 * atr), 1)
        if resistance > 0 and resistance > entry_mid and (resistance - entry_mid) <= (1.5 * atr):
            sl = round(resistance + 5.0, 1)
        else:
            sl = sl_calc
            
        sl_low = round(sl - 5.0, 1)
        sl_high = round(sl + 5.0, 1)
        
        risk = sl - entry_mid
        target_dist = risk * 2.1
        target_mid = round(entry_mid - target_dist, 1)
        target_low = round(target_mid - 8.0, 1)
        target_high = round(target_mid + 8.0, 1)
        
        rr_ratio = round(target_dist / max(risk, 1.0), 2)
        
        return {
            'entry_zone': f"₹{entry_low:,.1f} – ₹{entry_high:,.1f}",
            'entry_price': entry_mid,
            'stop_loss_zone': f"₹{sl_low:,.1f} – ₹{sl_high:,.1f}",
            'stop_loss_price': sl,
            'target_zone': f"₹{target_low:,.1f} – ₹{target_high:,.1f}",
            'target_price': target_mid,
            'risk_points': round(risk, 1),
            'reward_points': round(target_dist, 1),
            'risk_reward': f"1 : {rr_ratio}",
            'rr_value': rr_ratio
        }

    else:  # WAIT
        return {
            'entry_zone': f"Watch Zone: ₹{current_price - 10:,.1f} – ₹{current_price + 10:,.1f}",
            'entry_price': current_price,
            'stop_loss_zone': "Inactive (Wait for confirmed trigger)",
            'stop_loss_price': 0.0,
            'target_zone': "Inactive (Awaiting edge)",
            'target_price': 0.0,
            'risk_points': 0.0,
            'reward_points': 0.0,
            'risk_reward': "1 : 0.0",
            'rr_value': 0.0
        }


def generate_scalp_prediction(timeframe: str = '5m') -> Dict[str, Any]:
    """
    Main prediction pipeline:
      1. Loads real NIFTY 50 data
      2. Computes indicators, candles, features
      3. Performs multi-timeframe analysis
      4. Synthesizes ML probabilities and technical confluence
      5. Formulates BUY / SELL / WAIT signal with confidence & strength
      6. Generates Trade Plan (Entry, SL, Target, R:R)
      7. Returns comprehensive JSON
    """
    df_raw, source_desc = get_nifty_data(timeframe)
    if len(df_raw) < 20:
        return {
            'status': 'error',
            'message': 'Historical data unavailable — connect a supported data source.'
        }
        
    # Enrich indicators & candlesticks
    df_ind = calculate_all_indicators(df_raw)
    df_candles = detect_candle_patterns(df_ind)
    df_feat = extract_features(df_candles)
    
    last = df_feat.iloc[-1]
    current_price = float(round(last['close'], 2))
    timestamp = str(last['timestamp']) if 'timestamp' in last else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. Candlestick Analysis
    candle_info = get_latest_candle_info(df_candles)
    
    # 2. Multi-Timeframe Confirmation
    mtf = get_multi_timeframe_analysis()
    bias_1m = 'Bullish' if mtf['1m']['signal'] == 'BUY' else ('Bearish' if mtf['1m']['signal'] == 'SELL' else 'Neutral')
    bias_5m = 'Bullish' if mtf['5m']['signal'] == 'BUY' else ('Bearish' if mtf['5m']['signal'] == 'SELL' else 'Neutral')
    bias_15m = 'Bullish' if mtf['15m']['signal'] == 'BUY' else ('Bearish' if mtf['15m']['signal'] == 'SELL' else 'Neutral')
    
    # 3. ML Model Inference
    model = load_trained_model()
    ml_confidence = 0.50
    ml_class = 0
    ml_status = "Active"
    
    if model is not None:
        try:
            feat_vector = df_feat[FEATURE_COLUMNS].iloc[-1:].values
            probs = model.predict_proba(feat_vector)[0]
            ml_class = int(np.argmax(probs))
            ml_confidence = float(np.max(probs))
        except Exception:
            ml_status = "Inference Fallback"
    else:
        ml_status = "Model not trained yet. Run train.py first."

    # 4. Confluence Scoring System
    bull_score = 0
    bear_score = 0
    
    # Trend score (weight 3)
    if last['trend_direction'] == 'Bullish':
        bull_score += 3
    elif last['trend_direction'] == 'Bearish':
        bear_score += 3
        
    # Multi-timeframe trend alignment (weight 3)
    if bias_5m == 'Bullish' and bias_15m == 'Bullish':
        bull_score += 3
    elif bias_5m == 'Bearish' and bias_15m == 'Bearish':
        bear_score += 3
        
    # VWAP confirmation (weight 2)
    if current_price > last['vwap']:
        bull_score += 2
    else:
        bear_score += 2
        
    # RSI & Momentum (weight 2)
    if 52 <= last['rsi'] <= 68:
        bull_score += 2
    elif 32 <= last['rsi'] <= 48:
        bear_score += 2
        
    # Candlestick pattern bias (weight 2)
    if candle_info['bias'] == 'Bullish':
        bull_score += 2
    elif candle_info['bias'] == 'Bearish':
        bear_score += 2
        
    # Volume spike / confirmation (weight 1)
    if last['volume_spike']:
        if bull_score > bear_score:
            bull_score += 1
        elif bear_score > bull_score:
            bear_score += 1
            
    # ML Class reinforcement (weight 3)
    if ml_class == 1 and ml_confidence > 0.45:
        bull_score += 3
    elif ml_class == 2 and ml_confidence > 0.45:
        bear_score += 3

    # Total possible score ~ 14
    net_score = bull_score - bear_score
    
    if net_score >= 4:
        final_signal = 'BUY'
        bias = 'Bullish'
        confidence = min(92.0, max(64.0, 50.0 + (net_score * 3.5)))
    elif net_score <= -4:
        final_signal = 'SELL'
        bias = 'Bearish'
        confidence = min(92.0, max(64.0, 50.0 + (abs(net_score) * 3.5)))
    else:
        final_signal = 'WAIT'
        bias = 'Neutral'
        confidence = float(round(max(52.0, 100.0 - (abs(net_score) * 8.0)), 1))
        
    # Signal Strength
    total_agreement = max(bull_score, bear_score)
    if total_agreement >= 9 and final_signal != 'WAIT':
        signal_strength = 'Strong'
    elif total_agreement >= 6 and final_signal != 'WAIT':
        signal_strength = 'Moderate'
    else:
        signal_strength = 'Weak'

    # 5. Volatility & Trade Plan
    atr_val = float(last.get('atr', 20.0))
    sup_val = float(last.get('support', current_price - 30.0))
    res_val = float(last.get('resistance', current_price + 30.0))
    trade_plan = calculate_trade_plan(final_signal, current_price, atr_val, sup_val, res_val)

    # 6. Opening Behaviour & Historical Similarity
    opening_info = analyze_opening_behaviour(df_raw)
    hist_similarity = compute_historical_similarity(df_feat)
    macro_sentiment = get_macro_sentiment_context(df_ind)

    # 7. Model evaluation stats if available
    eval_metrics = {}
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, 'r') as f:
                eval_metrics = json.load(f)
        except Exception:
            pass

    return {
        'status': 'success',
        'instrument': 'NIFTY 50',
        'timestamp': timestamp,
        'timeframe': timeframe.upper(),
        'source': source_desc,
        'current_price': current_price,
        
        # Primary Signal Card
        'signal': final_signal,
        'confidence': round(confidence, 1),
        'signal_strength': signal_strength,
        'bias': bias,
        
        # Biases
        'short_term_bias': bias_1m,
        'intraday_bias': bias_5m,
        'htf_bias': bias_15m,
        'final_scalping_bias': bias,
        
        # Multi-timeframe Card
        'multi_timeframe': [
            {'timeframe': '1M', 'trend': mtf['1m']['trend'], 'signal': mtf['1m']['signal'], 'role': 'Entry / Scalping Timing'},
            {'timeframe': '5M', 'trend': mtf['5m']['trend'], 'signal': mtf['5m']['signal'], 'role': 'Primary Scalping Trend'},
            {'timeframe': '15M', 'trend': mtf['15m']['trend'], 'signal': mtf['15m']['signal'], 'role': 'Higher-Timeframe Bias'}
        ],
        
        # Trade Plan Card
        'trade_plan': trade_plan,
        
        # Candlestick Card
        'candlestick': candle_info,
        
        # Technical Analysis Card
        'technical': {
            'rsi': float(round(last.get('rsi', 50.0), 1)),
            'macd': float(round(last.get('macd', 0.0), 2)),
            'macd_signal': float(round(last.get('macd_signal', 0.0), 2)),
            'macd_hist': float(round(last.get('macd_hist', 0.0), 2)),
            'ema_9': float(round(last.get('ema_9', current_price), 2)),
            'ema_21': float(round(last.get('ema_21', current_price), 2)),
            'ema_50': float(round(last.get('ema_50', current_price), 2)),
            'vwap': float(round(last.get('vwap', current_price), 2)),
            'atr': float(round(atr_val, 2)),
            'volume_ratio': float(round(last.get('volume_ratio', 1.0), 2)),
            'volume_spike': bool(last.get('volume_spike', False)),
            'support': float(round(sup_val, 2)),
            'resistance': float(round(res_val, 2)),
            'trend_strength': float(round(last.get('trend_strength', 50.0), 1))
        },
        
        # Market Structure Card
        'market_structure': {
            'structure': str(last.get('market_structure', 'Neutral')),
            'volatility_regime': str(last.get('volatility_regime', 'Normal')),
            'opening_behaviour': opening_info
        },
        
        # Historical Similarity Card
        'historical_similarity': hist_similarity,
        
        # Macro & Sentiment Card
        'sentiment_context': macro_sentiment,
        
        # Model Evaluation
        'ml_status': ml_status,
        'model_metrics': eval_metrics,
        'disclaimer': 'Educational scalping intelligence. Does not provide guaranteed trading predictions or financial advice.'
    }
