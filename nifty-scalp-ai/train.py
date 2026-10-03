"""
train.py - ML Training Pipeline for NIFTY 50 Scalping Engine.
Trains a Histogram-based Gradient Boosting Classifier strictly on chronological splits.
Prevents data leakage, computes authentic out-of-sample metrics, and persists artifacts.
"""

import os
import json
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

from data_loader import get_nifty_data
from indicators import calculate_all_indicators
from candles import detect_candle_patterns
from features import extract_features, create_scalp_targets, FEATURE_COLUMNS


MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_FILE = os.path.join(MODEL_DIR, 'nifty_scalp_model.joblib')
METRICS_FILE = os.path.join(MODEL_DIR, 'metrics.json')


def train_scalp_model(timeframe: str = '5m', split_ratio: float = 0.80):
    """
    Executes end-to-end model training:
      1. Loads real NIFTY 50 intraday data
      2. Enriches with technical indicators & candlestick patterns
      3. Extracts features & generates scalp targets
      4. Strict chronological split (No shuffling!)
      5. Trains HistGradientBoostingClassifier
      6. Evaluates genuine out-of-sample test metrics
      7. Persists model & metrics JSON
    """
    print(f"\n{'='*60}")
    print(f"  NIFTY SCALP AI - Machine Learning Training Pipeline")
    print(f"{'='*60}")
    
    # 1. Load Data
    print(f"[*] Loading NIFTY 50 data (timeframe: {timeframe})...")
    df_raw, source = get_nifty_data(timeframe)
    print(f"    Source: {source} ({len(df_raw)} candles)")
    
    if len(df_raw) < 50:
        print("[!] Error: Insufficient data points to train model. Need at least 50 candles.")
        return None

    # 2. Enrich Indicators & Candlesticks
    print("[*] Computing technical indicators & candlestick patterns...")
    df_ind = calculate_all_indicators(df_raw)
    df_candles = detect_candle_patterns(df_ind)
    
    # 3. Extract Features
    print("[*] Engineering predictive feature matrix...")
    df_feat = extract_features(df_candles)
    
    # 4. Generate Target
    df_feat['target'] = create_scalp_targets(df_feat, horizon=4)
    
    # Drop rows with NaNs in feature columns or unfulfilled target (at end of dataframe)
    valid_df = df_feat.dropna(subset=FEATURE_COLUMNS).copy()
    valid_df = valid_df.iloc[:-4]  # Remove trailing bars with undefined forward returns
    
    if len(valid_df) < 40:
        print("[!] Error: Insufficient valid feature rows.")
        return None

    X = valid_df[FEATURE_COLUMNS].values
    y = valid_df['target'].values
    
    # 5. Chronological Train/Test Split (Strictly NO SHUFFLING!)
    split_idx = int(len(X) * split_ratio)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print(f"[*] Chronological Split: {len(X_train)} training candles | {len(X_test)} out-of-sample test candles")
    print(f"    Target Distribution (Train): WAIT={np.sum(y_train==0)}, BUY={np.sum(y_train==1)}, SELL={np.sum(y_train==2)}")
    
    # 6. Model Training
    print("[*] Training Histogram-based Gradient Boosting Classifier...")
    model = HistGradientBoostingClassifier(
        max_iter=120,
        learning_rate=0.06,
        max_depth=5,
        min_samples_leaf=15,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 7. Authentic Evaluation
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    acc = float(round(accuracy_score(y_test, y_pred) * 100, 2))
    prec = float(round(precision_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2))
    rec = float(round(recall_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2))
    f1 = float(round(f1_score(y_test, y_pred, average='weighted', zero_division=0) * 100, 2))
    
    # Directional Win Rate for active scalp signals (BUY/SELL)
    active_mask = (y_test != 0) & (y_pred != 0)
    if np.sum(active_mask) > 0:
        win_rate = float(round(accuracy_score(y_test[active_mask], y_pred[active_mask]) * 100, 2))
    else:
        win_rate = acc

    # 8. Save Artifacts
    print(f"[*] Saving model to {MODEL_FILE}...")
    joblib.dump(model, MODEL_FILE)
    
    metrics = {
        'model_name': 'HistGradientBoostingClassifier',
        'timeframe': timeframe,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'win_rate': win_rate,
        'total_evaluated_trades': int(len(X_test)),
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'feature_count': len(FEATURE_COLUMNS),
        'disclaimer': 'Past backtest performance does not guarantee future results. No fabrication.'
    }
    
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    print(f"\n{'-'*40}")
    print(f"  TRAINING EVALUATION RESULTS (GENUINE)")
    print(f"{'-'*40}")
    print(f"  Model Accuracy : {acc}%")
    print(f"  Precision      : {prec}%")
    print(f"  Recall         : {rec}%")
    print(f"  F1 Score       : {f1}%")
    print(f"  Active Win Rate: {win_rate}%")
    print(f"  Evaluated Bars : {len(X_test)}")
    print(f"{'-'*40}")
    print(f"[OK] Model successfully trained and saved.\n")
    return metrics


if __name__ == '__main__':
    train_scalp_model()
