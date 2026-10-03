"""
app.py - Web Backend for NIFTY SCALP AI.
Production-style Flask application serving Scalping Intelligence,
Real-time Technical Analysis, Candlestick Recognition, and Backtesting APIs.
"""

import os
from flask import Flask, render_template, jsonify, request
from data_loader import get_nifty_data
from indicators import calculate_all_indicators
from candles import detect_candle_patterns
from predictor import generate_scalp_prediction
from backtest import run_historical_backtest
from train import train_scalp_model


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Simple in-memory paper portfolio session (Initial balance strictly ₹0.00)
PAPER_PORTFOLIO = {
    'balance': 0.0,
    'available_balance': 0.0,
    'open_position': None,  # {'direction': 'BUY', 'entry_price': 24850, 'qty': 50, 'sl': 24800, 'tp': 24950}
    'realized_pnl': 0.0,
    'trade_history': []
}


@app.route('/')
def index():
    """Serves the primary NIFTY SCALP AI dashboard."""
    return render_template('index.html')


@app.route('/api/market', methods=['GET'])
def get_market_data():
    """
    Returns OHLCV candle series and overlay indicator lines
    for the interactive candlestick chart.
    Query param: timeframe = 1m | 5m | 15m
    """
    timeframe = request.args.get('timeframe', '5m').lower()
    if timeframe not in ['1m', '5m', '15m']:
        timeframe = '5m'
        
    try:
        df_raw, source_desc = get_nifty_data(timeframe)
        if len(df_raw) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Market data unavailable — connect a supported data source.'
            }), 404

        df_ind = calculate_all_indicators(df_raw)
        df_candles = detect_candle_patterns(df_ind)
        
        # Prepare candle records for chart (up to last 150 candles)
        chart_df = df_candles.tail(150).copy()
        candles = []
        for _, row in chart_df.iterrows():
            candles.append({
                'time': str(row['timestamp']) if 'timestamp' in row else '',
                'open': float(round(row['open'], 2)),
                'high': float(round(row['high'], 2)),
                'low': float(round(row['low'], 2)),
                'close': float(round(row['close'], 2)),
                'volume': int(row['volume']) if 'volume' in row else 0,
                'ema9': float(round(row.get('ema_9', row['close']), 2)),
                'ema21': float(round(row.get('ema_21', row['close']), 2)),
                'vwap': float(round(row.get('vwap', row['close']), 2)),
                'support': float(round(row.get('support', row['low']), 2)),
                'resistance': float(round(row.get('resistance', row['high']), 2)),
                'pattern': str(row.get('candle_pattern', 'None')),
                'pattern_bias': str(row.get('candle_bias', 'Neutral'))
            })
            
        last = chart_df.iloc[-1]
        summary = {
            'instrument': 'NIFTY 50',
            'timeframe': timeframe.upper(),
            'source': source_desc,
            'current_price': float(round(last['close'], 2)),
            'day_high': float(round(chart_df['high'].max(), 2)),
            'day_low': float(round(chart_df['low'].min(), 2)),
            'current_volume': int(last['volume']) if 'volume' in last else 0,
            'candle_count': len(candles)
        }
        
        return jsonify({
            'status': 'success',
            'summary': summary,
            'candles': candles
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving market data: {str(e)}"
        }), 500


@app.route('/api/predict', methods=['GET'])
def get_prediction():
    """
    Returns AI/ML scalping prediction, multi-timeframe analysis,
    volatility-aware trade plan, candlestick pattern, and similarity.
    Query param: timeframe = 1m | 5m | 15m
    """
    timeframe = request.args.get('timeframe', '5m').lower()
    if timeframe not in ['1m', '5m', '15m']:
        timeframe = '5m'
        
    try:
        result = generate_scalp_prediction(timeframe)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Prediction engine error: {str(e)}"
        }), 500


@app.route('/api/backtest', methods=['GET'])
def get_backtest():
    """
    Executes historical point-in-time backtest on selected timeframe.
    Query param: timeframe = 1m | 5m | 15m
    """
    timeframe = request.args.get('timeframe', '5m').lower()
    if timeframe not in ['1m', '5m', '15m']:
        timeframe = '5m'
        
    try:
        results = run_historical_backtest(timeframe)
        return jsonify(results)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Backtest execution error: {str(e)}"
        }), 500


@app.route('/api/train', methods=['POST'])
def trigger_training():
    """
    Retrains the ML model on latest NIFTY 50 dataset.
    """
    timeframe = request.args.get('timeframe', '5m').lower()
    try:
        metrics = train_scalp_model(timeframe)
        if metrics:
            return jsonify({
                'status': 'success',
                'message': 'Model trained successfully on chronological split.',
                'metrics': metrics
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Model training failed due to insufficient data.'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Training failed: {str(e)}"
        }), 500


@app.route('/api/portfolio', methods=['GET', 'POST'])
def manage_portfolio():
    """
    Paper portfolio management (Educational only, initial balance strictly ₹0.00).
    Supports GET (view balance/positions) and POST (paper trade simulator).
    """
    global PAPER_PORTFOLIO
    
    if request.method == 'GET':
        return jsonify({
            'status': 'success',
            'portfolio': PAPER_PORTFOLIO,
            'disclaimer': 'Paper portfolio for educational analysis only. Initial balance strictly ₹0.00. No real funds or broker connections.'
        })
        
    data = request.get_json(silent=True) or {}
    action = data.get('action')  # 'init_demo_capital', 'place_paper_order', 'close_position', 'reset'
    
    if action == 'init_demo_capital':
        amount = float(data.get('amount', 50000.0))
        PAPER_PORTFOLIO['balance'] = amount
        PAPER_PORTFOLIO['available_balance'] = amount
        return jsonify({'status': 'success', 'portfolio': PAPER_PORTFOLIO})
        
    elif action == 'place_paper_order':
        direction = data.get('direction', 'BUY')
        price = float(data.get('price', 24850.0))
        sl = float(data.get('sl', 24800.0))
        tp = float(data.get('tp', 24950.0))
        qty = int(data.get('qty', 25))  # NIFTY lot size
        
        required_margin = (price * qty) / 5.0  # Approx 5x intraday leverage
        if PAPER_PORTFOLIO['available_balance'] < required_margin:
            return jsonify({
                'status': 'error',
                'message': f"Insufficient available balance (₹{PAPER_PORTFOLIO['available_balance']:,.2f}) for required margin ₹{required_margin:,.2f}. Initialize paper demo capital first."
            }), 400
            
        PAPER_PORTFOLIO['available_balance'] -= required_margin
        PAPER_PORTFOLIO['open_position'] = {
            'direction': direction,
            'entry_price': price,
            'sl': sl,
            'tp': tp,
            'qty': qty,
            'margin': required_margin
        }
        return jsonify({'status': 'success', 'portfolio': PAPER_PORTFOLIO})
        
    elif action == 'close_position':
        if not PAPER_PORTFOLIO['open_position']:
            return jsonify({'status': 'error', 'message': 'No open position to close.'}), 400
            
        pos = PAPER_PORTFOLIO['open_position']
        exit_price = float(data.get('exit_price', pos['entry_price']))
        direction = pos['direction']
        qty = pos['qty']
        
        pnl = (exit_price - pos['entry_price']) * qty if direction == 'BUY' else (pos['entry_price'] - exit_price) * qty
        PAPER_PORTFOLIO['balance'] += pnl
        PAPER_PORTFOLIO['available_balance'] += pos['margin'] + pnl
        PAPER_PORTFOLIO['realized_pnl'] += pnl
        
        trade_rec = {
            'direction': direction,
            'entry': pos['entry_price'],
            'exit': exit_price,
            'qty': qty,
            'pnl': round(pnl, 2)
        }
        PAPER_PORTFOLIO['trade_history'].append(trade_rec)
        PAPER_PORTFOLIO['open_position'] = None
        return jsonify({'status': 'success', 'portfolio': PAPER_PORTFOLIO})
        
    elif action == 'reset':
        PAPER_PORTFOLIO = {
            'balance': 0.0,
            'available_balance': 0.0,
            'open_position': None,
            'realized_pnl': 0.0,
            'trade_history': []
        }
        return jsonify({'status': 'success', 'portfolio': PAPER_PORTFOLIO})
        
    return jsonify({'status': 'error', 'message': 'Invalid action'}), 400


# Auto-initialize model if missing (works seamlessly for both Gunicorn on Render & local dev)
def _init_model_on_start():
    from predictor import MODEL_PATH
    if not os.path.exists(MODEL_PATH):
        print("[*] Initializing model with default dataset on startup...")
        try:
            train_scalp_model('5m')
        except Exception as e:
            print(f"[!] Warning: Initial model training skipped ({e})")

_init_model_on_start()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
