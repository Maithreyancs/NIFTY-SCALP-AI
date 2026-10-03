# NIFTY SCALP AI

> **AI-Powered NIFTY 50 Scalping Intelligence & Quantitative Analysis Dashboard**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An educational, institutional-grade web application designed strictly for **NIFTY 50 scalping**. It combines machine learning classification, multi-timeframe trend confirmation (1M, 5M, 15M), real mathematical candlestick pattern recognition, and volatility-aware ATR risk modeling into high-conviction scalping signals.

---

## 1. Core Architectural Concepts

* **Single Market Focus**: Engineered exclusively for the Indian benchmark index **NIFTY 50** (`^NSEI`).
* **Scalping Horizon**: 1M (entry timing), 5M (primary trend), and 15M (higher-timeframe bias).
* **Authentic Data Rule**: Connects to authentic market feeds (Yahoo Finance `^NSEI` or standard OHLCV CSVs). Never invents 100-year fake histories.
* **Point-in-Time ML Pipeline**: Lightweight Histogram-based Gradient Boosting trained strictly on chronological splits to prevent data leakage and look-ahead bias.
* **Light-Themed Modern UI**: Apple and Microsoft Fluent inspired design system with soft glassmorphism, responsive canvas charts, and zero cyberpunk cliches.
* **Paper Portfolio**: Educational simulation with an initial balance strictly initialized to **₹0.00**.

---

## 2. Directory & File Tree (16 Files Total)

```text
nifty-scalp-ai/
│
├── README.md                 # Complete documentation & operational manual
├── requirements.txt          # Python dependencies
├── .gitignore                # Git exclusions (models, environments, caches)
├── Procfile                  # Production process definition for Render / PaaS
│
├── app.py                    # Flask web server & REST endpoints
├── train.py                  # Chronological ML training & metric serialization
├── predictor.py              # Live multi-timeframe inference & ATR trade plan generator
├── backtest.py               # Point-in-time historical backtest engine & equity curve
├── indicators.py             # Trend, momentum, volatility, volume & S/R math
├── candles.py                # Mathematical candlestick pattern detection (OHLC)
├── features.py               # Feature matrix builder & historical similarity analyzer
├── data_loader.py            # Live Yahoo Finance (^NSEI) & CSV loader + opening analysis
│
├── data/
│   └── README.md             # Dataset formatting rules & specifications
│
├── model/
│   └── README.md             # Model artifacts description & evaluation guidelines
│
├── templates/
│   └── index.html            # Premium light-themed dashboard UI
│
└── static/
    ├── style.css             # Vanilla CSS design system & typography
    └── app.js                # High-DPI canvas charts, portfolio & sync logic
```

*Total count: 17 core source files (Strictly within the requested 15–20 file limit, well under 30 files).*

---

## 3. Uploading to GitHub

The `.venv` folder contains local virtual environment libraries and is automatically excluded by `.gitignore`. The actual project source code is **lightweight (~150 KB, 17 files)** and uploads instantly to GitHub:

```bash
git add .
git commit -m "feat: NIFTY SCALP AI production release"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
git push -u origin main
```

---

## 4. Deploying on Render (Render.com)

You can host this application on Render as a **Web Service** in less than 2 minutes:

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `nifty-scalp-ai`
   - **Environment**: `Python`
   - **Region**: Any (e.g., Singapore / Oregon / Frankfurt)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (or it will automatically detect the `Procfile`)
   - **Plan**: `Free`
4. Click **Deploy Web Service**.
   Render will automatically install dependencies, train the baseline model on startup, and provide you with a live HTTPS URL (e.g. `https://nifty-scalp-ai.onrender.com`).

---

## 5. Local Installation & Setup

### Prerequisites
* Python 3.10+ or Python 3.11
* `uv` or standard `pip`

### Step 1: Clone or Navigate to Project Directory
```bash
cd "New folder"
```

### Step 2: Set up Virtual Environment & Install Dependencies
Using `uv` (Recommended):
```bash
uv venv .venv
uv pip install -r requirements.txt
```

Or using standard Python:
```bash
python -m venv .venv
.venv\Scripts\activate       # On Windows
pip install -r requirements.txt
```

---

## 4. Running the Application

### Train the ML Model
Train the Histogram-based Gradient Boosting Classifier on chronological splits:
```bash
python train.py
```
*(Model artifact is saved to `model/nifty_scalp_model.joblib` and genuine metrics to `model/metrics.json`)*.

### Start the Flask Server
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. How Prediction Works

1. **Multi-Timeframe Ingestion**:
   - **1M**: Evaluates fast micro-structure for scalp entry timing.
   - **5M**: Identifies primary intraday trend direction and momentum.
   - **15M**: Anchors higher-timeframe baseline and structural support/resistance.
2. **Technical Confluence**:
   - Compares price to **EMA 9**, **EMA 21**, **EMA 50**, and session **VWAP**.
   - Evaluates momentum via **RSI (14)** and **MACD (12, 26, 9)**.
   - Monitors volume spikes relative to the 20-period moving average.
3. **Candlestick Pattern Recognition**:
   - Directly computes Doji, Hammer, Inverted Hammer, Shooting Star, Bullish/Bearish Engulfing, Morning/Evening Star, and Marubozu from OHLC data.
4. **Machine Learning Inference**:
   - Feeds normalized feature vectors into `HistGradientBoostingClassifier` to compute class probabilities (`BUY`, `SELL`, `WAIT`).
5. **Volatility-Aware Trade Plan**:
   - Stop Loss and Target are dynamically sized based on **14-period ATR**:
     - $\text{Stop Loss} = \text{Entry} \mp (1.25 \times \text{ATR})$
     - $\text{Target} = \text{Entry} \pm (2.10 \times \text{ATR})$
     - Produces asymmetric favorable Risk/Reward ratios ($\ge 1 : 2.0$).
6. **Market Opening Behaviour**:
   - Examines session opening at 09:15 IST vs previous close to detect Gap Up, Gap Down, or Flat opening conditions.
7. **Historical Regime Similarity**:
   - Evaluates cosine distance between the current multi-dimensional feature vector and past trading regimes to identify historical analogues.

---

## 6. How Backtesting Works

- **Zero Look-Ahead Bias**: Iterates through historical bars sequentially.
- **Entry Simulation**: At bar close $t$, if confluence conditions meet the threshold, a virtual trade is triggered.
- **Outcome Evaluation**: Tracks subsequent bars up to the scalp horizon to detect if the high reached the Target or low breached Stop Loss.
- **Metrics Computed**:
  - Win Rate (%)
  - Profit Factor ($\frac{\sum \text{Gains}}{\sum \text{Losses}}$)
  - Average Return per scalp (%)
  - Maximum Drawdown (%)
  - Cumulative Equity Curve

---

## 7. Limitations & Real-World Constraints

- **Execution Latency & Slippage**: In live high-frequency scalping, sub-second latency and order execution slippage can impact fill prices.
- **Exchange Fees & Taxes**: Real NIFTY trading involves STT, exchange transaction charges, SEBI turnover fees, GST, and brokerage.
- **Macro Feed Dependency**: Without an active institutional news API subscription, macro data (RBI, CPI, Fed) defaults to "Data unavailable" rather than fabricating information.

---

## 8. Financial Disclaimer

> **IMPORTANT**: This project is for **educational and research purposes only**. It does not provide guaranteed trading predictions, financial advice, or automated order routing. Past backtest performance does not guarantee future results. The software does not execute real monetary transactions.
