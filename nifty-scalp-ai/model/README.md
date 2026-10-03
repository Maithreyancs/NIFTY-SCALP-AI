# NIFTY SCALP AI Models Directory

This directory stores trained machine learning models and genuine out-of-sample evaluation metrics.

## Artifacts

- `nifty_scalp_model.joblib`: Serialized lightweight model (Histogram-based Gradient Boosting or Random Forest Classifier) trained strictly on chronological time-series splits without look-ahead bias or data leakage.
- `metrics.json`: Actual evaluation results:
  - Accuracy
  - Precision
  - Recall
  - F1 Score
  - Win Rate
  - Total Backtest Trades
  - Training Timestamp

## Performance Philosophy

- We never claim "95% guaranteed accuracy".
- Metrics reflect actual out-of-sample test results.
- Past backtest performance does not guarantee future results.
