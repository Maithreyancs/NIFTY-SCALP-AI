# NIFTY 50 Historical Data Directory

This directory stores authentic NIFTY 50 OHLCV market datasets.

## Expected CSV Format

If supplying custom intraday CSV data, use the standard format:

```csv
timestamp,open,high,low,close,volume
2026-03-27 09:15:00,24850.50,24875.20,24840.10,24865.00,124500
2026-03-27 09:20:00,24865.00,24890.00,24855.30,24880.75,98000
```

### Supported File Names:
- `nifty_1m.csv` (1-Minute scalping data)
- `nifty_5m.csv` (5-Minute primary trend data)
- `nifty_15m.csv` (15-Minute higher timeframe data)

## Live Data Source

The application automatically connects to **Yahoo Finance (`^NSEI`)** to download real, legitimate intraday NIFTY 50 market data for:
- 1 Minute (up to 7 days)
- 5 Minutes (up to 60 days)
- 15 Minutes (up to 60 days)

## Important Rule
- Do not fabricate or invent fake 100-year NIFTY data.
- If data is unavailable, the system explicitly displays `Historical data unavailable — connect a supported data source`.
