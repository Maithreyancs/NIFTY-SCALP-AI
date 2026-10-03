/**
 * app.js - Frontend Controller for NIFTY SCALP AI.
 * Handles API synchronization, High-DPI Candlestick & Equity Canvas charts,
 * Multi-Timeframe views, Backtesting visualizations, and Paper Portfolio.
 */

document.addEventListener('DOMContentLoaded', () => {
  // App State
  const state = {
    timeframe: '5m',
    backtestTf: '5m',
    currentTab: 'tab-dashboard',
    marketData: null,
    predictionData: null,
    backtestData: null,
    indicators: {
      ema9: true,
      ema21: true,
      vwap: true,
      sr: true
    },
    autoRefreshInterval: null,
    isRefreshing: false
  };

  // DOM Elements
  const els = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    tfBtns: document.querySelectorAll('#tfSelector .tf-btn'),
    backtestTfBtns: document.querySelectorAll('#backtestTfSelector .tf-btn'),
    btnRefresh: document.getElementById('btnRefresh'),
    statusSource: document.getElementById('statusSource'),
    
    // Main Signal Card
    signalTimeframeBadge: document.getElementById('signalTimeframeBadge'),
    heroPrice: document.getElementById('heroPrice'),
    heroTimestamp: document.getElementById('heroTimestamp'),
    heroSignalBadge: document.getElementById('heroSignalBadge'),
    heroSignalAction: document.getElementById('heroSignalAction'),
    heroConfidence: document.getElementById('heroConfidence'),
    heroSignalStrength: document.getElementById('heroSignalStrength'),
    heroBiasValue: document.getElementById('heroBiasValue'),
    
    // Trade Plan
    tradePlanRR: document.getElementById('tradePlanRR'),
    planEntryZone: document.getElementById('planEntryZone'),
    planSlZone: document.getElementById('planSlZone'),
    planTpZone: document.getElementById('planTpZone'),
    planRiskPts: document.getElementById('planRiskPts'),
    planRewardPts: document.getElementById('planRewardPts'),
    
    // Multi-Timeframe
    mtfFinalBias: document.getElementById('mtfFinalBias'),
    mtfTableBody: document.getElementById('mtfTableBody'),
    
    // Candlestick & Opening & Similarity
    candlePatternName: document.getElementById('candlePatternName'),
    candlePatternBias: document.getElementById('candlePatternBias'),
    candleBiasBadge: document.getElementById('candleBiasBadge'),
    candleRangeVal: document.getElementById('candleRangeVal'),
    candleVolVal: document.getElementById('candleVolVal'),
    openingStatusBadge: document.getElementById('openingStatusBadge'),
    openingTypeVal: document.getElementById('openingTypeVal'),
    openingGapVal: document.getElementById('openingGapVal'),
    openingRangeVal: document.getElementById('openingRangeVal'),
    openingMomentumVal: document.getElementById('openingMomentumVal'),
    histSimilarityPct: document.getElementById('histSimilarityPct'),
    histAnalogueName: document.getElementById('histAnalogueName'),
    histAnalogueDesc: document.getElementById('histAnalogueDesc'),
    
    // Technical Indicators
    techRsi: document.getElementById('techRsi'),
    techRsiFill: document.getElementById('techRsiFill'),
    techRsiSub: document.getElementById('techRsiSub'),
    techMacd: document.getElementById('techMacd'),
    techMacdSub: document.getElementById('techMacdSub'),
    techEma9: document.getElementById('techEma9'),
    techEma21: document.getElementById('techEma21'),
    techEma50: document.getElementById('techEma50'),
    techVwap: document.getElementById('techVwap'),
    techVwapSub: document.getElementById('techVwapSub'),
    techAtr: document.getElementById('techAtr'),
    techVolRegime: document.getElementById('techVolRegime'),
    techVolRatio: document.getElementById('techVolRatio'),
    techVolSpike: document.getElementById('techVolSpike'),
    techSR: document.getElementById('techSR'),
    
    // Chart
    candleCanvas: document.getElementById('candleChartCanvas'),
    chartTooltip: document.getElementById('chartTooltip'),
    chartTimeframeLabel: document.getElementById('chartTimeframeLabel'),
    chkEMA9: document.getElementById('chkEMA9'),
    chkEMA21: document.getElementById('chkEMA21'),
    chkVWAP: document.getElementById('chkVWAP'),
    chkSR: document.getElementById('chkSR'),
    
    // Backtest
    kpiWinRate: document.getElementById('kpiWinRate'),
    kpiWinsLosses: document.getElementById('kpiWinsLosses'),
    kpiAccuracy: document.getElementById('kpiAccuracy'),
    kpiProfitFactor: document.getElementById('kpiProfitFactor'),
    kpiAvgReturn: document.getElementById('kpiAvgReturn'),
    kpiMaxDrawdown: document.getElementById('kpiMaxDrawdown'),
    kpiTotalTrades: document.getElementById('kpiTotalTrades'),
    kpiPrecision: document.getElementById('kpiPrecision'),
    kpiRecall: document.getElementById('kpiRecall'),
    kpiF1: document.getElementById('kpiF1'),
    equityCanvas: document.getElementById('equityChartCanvas'),
    backtestTradeLogBody: document.getElementById('backtestTradeLogBody'),
    
    // Portfolio
    portBalance: document.getElementById('portBalance'),
    portAvailable: document.getElementById('portAvailable'),
    portPosition: document.getElementById('portPosition'),
    portPosDetails: document.getElementById('portPosDetails'),
    portPnl: document.getElementById('portPnl'),
    btnInitDemoFunds: document.getElementById('btnInitDemoFunds'),
    btnExecutePaperBuy: document.getElementById('btnExecutePaperBuy'),
    btnExecutePaperSell: document.getElementById('btnExecutePaperSell'),
    btnClosePaperPos: document.getElementById('btnClosePaperPos'),
    btnResetPortfolio: document.getElementById('btnResetPortfolio'),
    paperAlertMsg: document.getElementById('paperAlertMsg'),
    
    // Analysis
    macroRbiStatus: document.getElementById('macroRbiStatus'),
    macroCpiStatus: document.getElementById('macroCpiStatus'),
    macroGlobalStatus: document.getElementById('macroGlobalStatus'),
    macroSentimentVal: document.getElementById('macroSentimentVal'),
    macroSentimentExpl: document.getElementById('macroSentimentExpl'),
    mlModelStatusLabel: document.getElementById('mlModelStatusLabel'),
    btnRetrainModel: document.getElementById('btnRetrainModel'),
    retrainResultNote: document.getElementById('retrainResultNote')
  };

  /* ==========================================================================
     Tab Navigation & Timeframe Controls
     ========================================================================== */

  els.navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      els.navBtns.forEach(b => b.classList.remove('active'));
      els.tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(tabId)?.classList.add('active');
      state.currentTab = tabId;

      if (tabId === 'tab-backtest' && !state.backtestData) {
        fetchBacktest(state.backtestTf);
      } else if (tabId === 'tab-portfolio') {
        fetchPortfolio();
      } else if (tabId === 'tab-dashboard') {
        renderCandleChart();
      }
    });
  });

  els.tfBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tf = btn.getAttribute('data-tf');
      if (tf === state.timeframe) return;

      els.tfBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.timeframe = tf;
      els.signalTimeframeBadge.textContent = `${tf.toUpperCase()} SCALPING`;
      els.chartTimeframeLabel.textContent = `${tf.toUpperCase()} Candles`;

      refreshAllData();
    });
  });

  els.backtestTfBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tf = btn.getAttribute('data-tf');
      els.backtestTfBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.backtestTf = tf;
      fetchBacktest(tf);
    });
  });

  els.btnRefresh.addEventListener('click', () => {
    refreshAllData(true);
  });

  // Chart Overlay Checkboxes
  els.chkEMA9?.addEventListener('change', (e) => { state.indicators.ema9 = e.target.checked; renderCandleChart(); });
  els.chkEMA21?.addEventListener('change', (e) => { state.indicators.ema21 = e.target.checked; renderCandleChart(); });
  els.chkVWAP?.addEventListener('change', (e) => { state.indicators.vwap = e.target.checked; renderCandleChart(); });
  els.chkSR?.addEventListener('change', (e) => { state.indicators.sr = e.target.checked; renderCandleChart(); });

  /* ==========================================================================
     Data Fetching
     ========================================================================== */

  async function fetchMarket() {
    try {
      const res = await fetch(`/api/market?timeframe=${state.timeframe}`);
      const data = await res.json();
      if (data.status === 'success') {
        state.marketData = data;
        els.statusSource.textContent = data.summary.source;
        renderCandleChart();
      }
    } catch (err) {
      console.error('Market fetch error:', err);
      els.statusSource.textContent = 'Data error';
    }
  }

  async function fetchPrediction() {
    try {
      const res = await fetch(`/api/predict?timeframe=${state.timeframe}`);
      const data = await res.json();
      if (data.status === 'success') {
        state.predictionData = data;
        updateDashboardUI(data);
      }
    } catch (err) {
      console.error('Prediction fetch error:', err);
    }
  }

  async function fetchBacktest(tf = '5m') {
    try {
      els.kpiWinRate.textContent = 'Calculating...';
      const res = await fetch(`/api/backtest?timeframe=${tf}`);
      const data = await res.json();
      if (data.status === 'success') {
        state.backtestData = data;
        updateBacktestUI(data);
      }
    } catch (err) {
      console.error('Backtest fetch error:', err);
    }
  }

  async function fetchPortfolio() {
    try {
      const res = await fetch('/api/portfolio');
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
      }
    } catch (err) {
      console.error('Portfolio fetch error:', err);
    }
  }

  async function refreshAllData(showAnimation = false) {
    if (state.isRefreshing) return;
    state.isRefreshing = true;

    if (showAnimation) {
      els.btnRefresh.classList.add('spinning');
    }

    await Promise.all([fetchMarket(), fetchPrediction()]);

    if (showAnimation) {
      setTimeout(() => els.btnRefresh.classList.remove('spinning'), 500);
    }
    state.isRefreshing = false;
  }

  /* ==========================================================================
     UI Population: Dashboard
     ========================================================================== */

  function updateDashboardUI(data) {
    // 1. Hero Card
    els.heroPrice.textContent = data.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2 });
    els.heroTimestamp.textContent = `Timestamp: ${data.timestamp}`;
    
    // Signal badge styling
    const sig = data.signal.toUpperCase();
    els.heroSignalAction.textContent = sig;
    els.heroConfidence.textContent = `Confidence: ${data.confidence}%`;
    els.heroSignalStrength.textContent = `${data.signal_strength} Signal`;
    
    els.heroSignalBadge.className = 'signal-badge-large';
    if (sig === 'BUY') {
      els.heroSignalBadge.classList.add('sig-buy');
    } else if (sig === 'SELL') {
      els.heroSignalBadge.classList.add('sig-sell');
    } else {
      els.heroSignalBadge.classList.add('sig-wait');
    }

    els.heroBiasValue.textContent = `${data.bias} (${data.signal_strength})`;

    // 2. Trade Plan Card
    const plan = data.trade_plan;
    els.tradePlanRR.textContent = `R : R = ${plan.risk_reward}`;
    els.planEntryZone.textContent = plan.entry_zone;
    els.planSlZone.textContent = plan.stop_loss_zone;
    els.planTpZone.textContent = plan.target_zone;
    els.planRiskPts.textContent = `Risk: ${plan.risk_points} pts`;
    els.planRewardPts.textContent = `Target: ${plan.reward_points} pts`;

    // 3. Multi-Timeframe Confirmation
    els.mtfFinalBias.textContent = `Final Bias: ${data.final_scalping_bias}`;
    if (data.multi_timeframe && data.multi_timeframe.length > 0) {
      els.mtfTableBody.innerHTML = data.multi_timeframe.map(m => {
        const trendClass = m.trend === 'Bullish' ? 'trend-bull' : (m.trend === 'Bearish' ? 'trend-bear' : 'trend-neutral');
        const sigClass = m.signal === 'BUY' ? 'sig-buy' : (m.signal === 'SELL' ? 'sig-sell' : 'sig-wait');
        return `
          <tr>
            <td><strong>${m.timeframe}</strong></td>
            <td>${m.role}</td>
            <td><span class="trend-pill ${trendClass}">${m.trend}</span></td>
            <td><span class="sig-pill ${sigClass}">${m.signal}</span></td>
          </tr>
        `;
      }).join('');
    }

    // 4. Candlestick Recognition
    const c = data.candlestick;
    els.candlePatternName.textContent = c.pattern;
    els.candlePatternBias.textContent = c.bias;
    els.candleBiasBadge.textContent = `${c.bias} Bias`;
    els.candleBiasBadge.className = 'badge-soft';
    if (c.bias === 'Bullish') els.candleBiasBadge.style.background = '#ecfdf5', els.candleBiasBadge.style.color = '#10b981';
    else if (c.bias === 'Bearish') els.candleBiasBadge.style.background = '#fef2f2', els.candleBiasBadge.style.color = '#ef4444';
    else els.candleBiasBadge.style.background = '#fffbeb', els.candleBiasBadge.style.color = '#d97706';

    const rangePts = (c.high - c.low).toFixed(1);
    els.candleRangeVal.textContent = `${rangePts} pts (H: ₹${c.high} / L: ₹${c.low})`;
    els.candleVolVal.textContent = c.volume.toLocaleString('en-IN');

    // 5. Market Opening Behaviour
    const op = data.market_structure.opening_behaviour;
    els.openingTypeVal.textContent = op.gap_type || 'Market Open';
    els.openingGapVal.textContent = `${op.gap_points > 0 ? '+' : ''}${op.gap_points} pts (${op.gap_percent}%)`;
    els.openingRangeVal.textContent = `${op.opening_range} pts`;
    els.openingMomentumVal.textContent = op.early_momentum;

    // 6. Historical Pattern Similarity
    const sim = data.historical_similarity;
    els.histSimilarityPct.textContent = `Similarity: ${sim.similarity_pct}%`;
    els.histAnalogueName.textContent = sim.analogue;
    els.histAnalogueDesc.textContent = `Matched period: ${sim.matched_period}. ${sim.disclaimer}`;

    // 7. Technical Indicators
    const t = data.technical;
    els.techRsi.textContent = t.rsi.toFixed(1);
    els.techRsiFill.style.width = `${Math.min(100, Math.max(0, t.rsi))}%`;
    if (t.rsi > 70) els.techRsiSub.textContent = 'Overbought (>70)';
    else if (t.rsi < 30) els.techRsiSub.textContent = 'Oversold (<30)';
    else els.techRsiSub.textContent = 'Balanced Momentum';

    els.techMacd.textContent = `${t.macd > 0 ? '+' : ''}${t.macd.toFixed(2)}`;
    els.techMacdSub.textContent = `Signal: ${t.macd_signal} | Hist: ${t.macd_hist}`;
    els.techEma9.textContent = `₹${t.ema_9.toLocaleString('en-IN')}`;
    els.techEma21.textContent = `EMA 21: ₹${t.ema_21.toLocaleString('en-IN')}`;
    els.techEma50.textContent = `₹${t.ema_50.toLocaleString('en-IN')}`;
    els.techVwap.textContent = `₹${t.vwap.toLocaleString('en-IN')}`;
    els.techVwapSub.textContent = data.current_price >= t.vwap ? 'Price Above VWAP (Bullish)' : 'Price Below VWAP (Bearish)';

    els.techAtr.textContent = `${t.atr.toFixed(1)} pts`;
    els.techVolRegime.textContent = `Regime: ${data.market_structure.volatility_regime}`;
    els.techVolRatio.textContent = `${t.volume_ratio}x`;
    els.techVolSpike.textContent = t.volume_spike ? 'Volume Spike Detected' : 'Average Volume Flow';
    els.techSR.textContent = `S: ₹${t.support.toLocaleString('en-IN')} | R: ₹${t.resistance.toLocaleString('en-IN')}`;

    // 8. Macro & Sentiment (in Analysis Tab)
    const sent = data.sentiment_context;
    els.macroSentimentVal.textContent = sent.sentiment;
    els.macroSentimentExpl.textContent = sent.explanation;
    els.macroRbiStatus.textContent = sent.macro_context;
    els.macroGlobalStatus.textContent = sent.global_influence;
    els.mlModelStatusLabel.textContent = data.ml_status;
  }

  /* ==========================================================================
     UI Population: Backtest
     ========================================================================== */

  function updateBacktestUI(data) {
    els.kpiWinRate.textContent = `${data.win_rate}%`;
    els.kpiWinsLosses.textContent = `${data.winning_trades} Wins / ${data.losing_trades} Losses`;
    els.kpiAccuracy.textContent = `${data.accuracy}%`;
    els.kpiProfitFactor.textContent = `${data.profit_factor}`;
    els.kpiAvgReturn.textContent = `${data.average_return > 0 ? '+' : ''}${data.average_return}%`;
    els.kpiMaxDrawdown.textContent = `-${data.max_drawdown}%`;
    els.kpiTotalTrades.textContent = `${data.total_trades}`;
    els.kpiPrecision.textContent = `${data.precision}%`;
    els.kpiRecall.textContent = `${data.recall}%`;
    els.kpiF1.textContent = `${data.f1}%`;

    // Render Equity Curve Canvas
    renderEquityCurve(data.equity_curve);

    // Render Trades Table
    if (data.recent_trades && data.recent_trades.length > 0) {
      els.backtestTradeLogBody.innerHTML = data.recent_trades.map(t => {
        const pClass = t.is_win ? 'text-green' : 'text-red';
        const badgeClass = t.direction === 'BUY' ? 'sig-buy' : 'sig-sell';
        return `
          <tr>
            <td>#${t.trade_no}</td>
            <td><span class="sig-pill ${badgeClass}">${t.direction}</span></td>
            <td>${t.entry_time.slice(-8)}</td>
            <td>₹${t.entry_price.toLocaleString('en-IN')}</td>
            <td>₹${t.exit_price.toLocaleString('en-IN')}</td>
            <td><strong>${t.outcome.replace('_', ' ')}</strong></td>
            <td class="${pClass}"><strong>${t.pct_return > 0 ? '+' : ''}${t.pct_return}% (${t.points} pts)</strong></td>
          </tr>
        `;
      }).join('');
    } else {
      els.backtestTradeLogBody.innerHTML = `<tr><td colspan="7" class="text-center">No simulated trades found in this timeframe range.</td></tr>`;
    }
  }

  /* ==========================================================================
     UI Population: Portfolio
     ========================================================================== */

  function updatePortfolioUI(p) {
    els.portBalance.textContent = `₹${p.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    els.portAvailable.textContent = `₹${p.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    
    if (p.open_position) {
      const pos = p.open_position;
      els.portPosition.textContent = `${pos.direction} (Qty ${pos.qty})`;
      els.portPosition.style.color = pos.direction === 'BUY' ? 'var(--bull-green)' : 'var(--bear-red)';
      els.portPosDetails.textContent = `Entry: ₹${pos.entry_price} | SL: ₹${pos.sl} | TP: ₹${pos.tp}`;
    } else {
      els.portPosition.textContent = 'None';
      els.portPosition.style.color = 'var(--text-primary)';
      els.portPosDetails.textContent = 'No active scalps';
    }

    const pnlSign = p.realized_pnl >= 0 ? '+' : '';
    els.portPnl.textContent = `${pnlSign}₹${p.realized_pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    els.portPnl.className = `p-value ${p.realized_pnl >= 0 ? 'text-green' : 'text-red'}`;
  }

  function showPaperAlert(msg, isSuccess = true) {
    els.paperAlertMsg.textContent = msg;
    els.paperAlertMsg.className = `paper-alert show ${isSuccess ? 'success' : 'error'}`;
    setTimeout(() => {
      els.paperAlertMsg.className = 'paper-alert';
    }, 4500);
  }

  // Portfolio Actions
  els.btnInitDemoFunds?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/portfolio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'init_demo_capital', amount: 50000.0 })
      });
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
        showPaperAlert('Initialized virtual demo capital of ₹50,000.00 for educational simulation.', true);
      }
    } catch (e) {
      showPaperAlert('Failed to initialize demo funds.', false);
    }
  });

  els.btnExecutePaperBuy?.addEventListener('click', async () => {
    if (!state.predictionData) return;
    const plan = state.predictionData.trade_plan;
    const price = state.predictionData.current_price;
    try {
      const res = await fetch('/api/portfolio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'place_paper_order',
          direction: 'BUY',
          price: price,
          sl: plan.stop_loss_price,
          tp: plan.target_price,
          qty: 25
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
        showPaperAlert(`Executed Paper BUY @ ₹${price} (Qty 25, SL: ₹${plan.stop_loss_price}, TP: ₹${plan.target_price})`, true);
      } else {
        showPaperAlert(data.message, false);
      }
    } catch (e) {
      showPaperAlert('Error executing paper order.', false);
    }
  });

  els.btnExecutePaperSell?.addEventListener('click', async () => {
    if (!state.predictionData) return;
    const plan = state.predictionData.trade_plan;
    const price = state.predictionData.current_price;
    try {
      const res = await fetch('/api/portfolio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'place_paper_order',
          direction: 'SELL',
          price: price,
          sl: plan.stop_loss_price,
          tp: plan.target_price,
          qty: 25
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
        showPaperAlert(`Executed Paper SELL @ ₹${price} (Qty 25, SL: ₹${plan.stop_loss_price}, TP: ₹${plan.target_price})`, true);
      } else {
        showPaperAlert(data.message, false);
      }
    } catch (e) {
      showPaperAlert('Error executing paper order.', false);
    }
  });

  els.btnClosePaperPos?.addEventListener('click', async () => {
    if (!state.predictionData) return;
    const exitPrice = state.predictionData.current_price;
    try {
      const res = await fetch('/api/portfolio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'close_position', exit_price: exitPrice })
      });
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
        showPaperAlert(`Closed open position @ ₹${exitPrice}. P&L updated.`, true);
      } else {
        showPaperAlert(data.message, false);
      }
    } catch (e) {
      showPaperAlert('Error closing position.', false);
    }
  });

  els.btnResetPortfolio?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/portfolio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      });
      const data = await res.json();
      if (data.status === 'success') {
        updatePortfolioUI(data.portfolio);
        showPaperAlert('Portfolio reset to ₹0.00 baseline.', true);
      }
    } catch (e) {
      showPaperAlert('Reset failed.', false);
    }
  });

  // Retrain Model Trigger
  els.btnRetrainModel?.addEventListener('click', async () => {
    els.btnRetrainModel.disabled = true;
    els.retrainResultNote.textContent = 'Training HistGradientBoostingClassifier on chronological split...';
    try {
      const res = await fetch(`/api/train?timeframe=${state.timeframe}`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        const m = data.metrics;
        els.retrainResultNote.textContent = `Model trained successfully! Accuracy: ${m.accuracy}% | Precision: ${m.precision}% | Active Win Rate: ${m.win_rate}%`;
        refreshAllData(true);
      } else {
        els.retrainResultNote.textContent = `Training failed: ${data.message}`;
      }
    } catch (e) {
      els.retrainResultNote.textContent = 'Error triggering model training.';
    } finally {
      els.btnRetrainModel.disabled = false;
    }
  });

  /* ==========================================================================
     High-DPI Interactive Canvas Candlestick Chart (Apple / Fluent Style)
     ========================================================================== */

  function renderCandleChart() {
    const canvas = els.candleCanvas;
    if (!canvas || !state.marketData || !state.marketData.candles) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    // Scale for crystal sharp retina displays
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 65, bottom: 30, left: 15 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    const candles = state.marketData.candles;
    if (candles.length === 0) return;

    // Calculate High/Low bounds
    let minPrice = Infinity;
    let maxPrice = -Infinity;

    candles.forEach(c => {
      minPrice = Math.min(minPrice, c.low);
      maxPrice = Math.max(maxPrice, c.high);
      if (state.indicators.ema9 && c.ema9) { minPrice = Math.min(minPrice, c.ema9); maxPrice = Math.max(maxPrice, c.ema9); }
      if (state.indicators.ema21 && c.ema21) { minPrice = Math.min(minPrice, c.ema21); maxPrice = Math.max(maxPrice, c.ema21); }
      if (state.indicators.vwap && c.vwap) { minPrice = Math.min(minPrice, c.vwap); maxPrice = Math.max(maxPrice, c.vwap); }
    });

    // Add 8% buffer top and bottom
    const range = maxPrice - minPrice || 1.0;
    minPrice -= range * 0.08;
    maxPrice += range * 0.08;

    const getY = (val) => padding.top + chartH - ((val - minPrice) / (maxPrice - minPrice)) * chartH;
    const getX = (idx) => padding.left + (idx + 0.5) * (chartW / candles.length);
    const candleWidth = Math.max(2, (chartW / candles.length) * 0.72);

    // 1. Draw Grid Lines
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 1;
    const gridSteps = 5;
    for (let i = 0; i <= gridSteps; i++) {
      const y = padding.top + (i / gridSteps) * chartH;
      const priceAtY = maxPrice - (i / gridSteps) * (maxPrice - minPrice);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Right Y-axis labels
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(`₹${priceAtY.toFixed(1)}`, width - padding.right + 8, y + 3);
    }

    // 2. Draw S/R Zones if enabled
    if (state.indicators.sr) {
      const lastC = candles[candles.length - 1];
      if (lastC.support) {
        const supY = getY(lastC.support);
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, supY);
        ctx.lineTo(width - padding.right, supY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = '#10b981';
        ctx.fillText(`Sup ₹${lastC.support.toFixed(0)}`, width - padding.right + 8, supY - 2);
      }
      if (lastC.resistance) {
        const resY = getY(lastC.resistance);
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, resY);
        ctx.lineTo(width - padding.right, resY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = '#ef4444';
        ctx.fillText(`Res ₹${lastC.resistance.toFixed(0)}`, width - padding.right + 8, resY - 2);
      }
    }

    // 3. Draw Candlesticks
    candles.forEach((c, idx) => {
      const x = getX(idx);
      const isBull = c.close >= c.open;
      const bodyTop = getY(Math.max(c.open, c.close));
      const bodyBottom = getY(Math.min(c.open, c.close));
      const bodyHeight = Math.max(1.5, bodyBottom - bodyTop);

      ctx.strokeStyle = isBull ? '#10b981' : '#ef4444';
      ctx.fillStyle = isBull ? '#10b981' : '#ef4444';

      // Upper and lower wicks
      ctx.beginPath();
      ctx.moveTo(x, getY(c.high));
      ctx.lineTo(x, getY(c.low));
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Candle body
      ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
    });

    // 4. Draw Overlay Lines
    function drawLine(prop, color, isDashed = false) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6;
      if (isDashed) ctx.setLineDash([4, 3]);
      else ctx.setLineDash([]);

      ctx.beginPath();
      let started = false;
      candles.forEach((c, idx) => {
        if (c[prop]) {
          const x = getX(idx);
          const y = getY(c[prop]);
          if (!started) { ctx.moveTo(x, y); started = true; }
          else { ctx.lineTo(x, y); }
        }
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    if (state.indicators.ema9) drawLine('ema9', '#2563eb');
    if (state.indicators.ema21) drawLine('ema21', '#8b5cf6');
    if (state.indicators.vwap) drawLine('vwap', '#ea580c', true);

    // X-axis timestamps
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    const stepX = Math.max(1, Math.floor(candles.length / 6));
    for (let idx = 0; idx < candles.length; idx += stepX) {
      const timeStr = candles[idx].time ? candles[idx].time.slice(11, 16) : '';
      if (timeStr) {
        ctx.fillText(timeStr, getX(idx), height - padding.bottom + 18);
      }
    }
  }

  // Canvas Hover Tooltip & Crosshair
  els.candleCanvas?.addEventListener('mousemove', (e) => {
    if (!state.marketData || !state.marketData.candles) return;
    const rect = els.candleCanvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const padding = { left: 15, right: 65 };
    const chartW = rect.width - padding.left - padding.right;
    const candles = state.marketData.candles;

    const idx = Math.floor(((mouseX - padding.left) / chartW) * candles.length);
    if (idx >= 0 && idx < candles.length) {
      const c = candles[idx];
      const tt = els.chartTooltip;
      tt.style.display = 'block';
      tt.style.left = `${Math.min(rect.width - 180, Math.max(10, mouseX + 15))}px`;
      tt.style.top = `30px`;
      tt.innerHTML = `
        <strong>${c.time || 'NIFTY 50'}</strong><br/>
        O: ₹${c.open.toFixed(2)} | H: ₹${c.high.toFixed(2)}<br/>
        L: ₹${c.low.toFixed(2)} | C: ₹${c.close.toFixed(2)}<br/>
        Vol: ${c.volume.toLocaleString('en-IN')}<br/>
        ${c.pattern !== 'None' ? `<span style="color:#38bdf8;">${c.pattern}</span>` : ''}
      `;
    }
  });

  els.candleCanvas?.addEventListener('mouseleave', () => {
    if (els.chartTooltip) els.chartTooltip.style.display = 'none';
  });

  /* ==========================================================================
     High-DPI Equity Curve Canvas Chart
     ========================================================================== */

  function renderEquityCurve(curve) {
    const canvas = els.equityCanvas;
    if (!canvas || !curve || curve.length < 2) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 50, bottom: 25, left: 15 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    const minVal = Math.min(...curve) * 0.98;
    const maxVal = Math.max(...curve) * 1.02;

    const getY = (val) => padding.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    const getX = (idx) => padding.left + (idx / (curve.length - 1)) * chartW;

    // Background gradient fill
    const grad = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    grad.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
    grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    ctx.beginPath();
    ctx.moveTo(getX(0), height - padding.bottom);
    curve.forEach((val, idx) => {
      ctx.lineTo(getX(idx), getY(val));
    });
    ctx.lineTo(getX(curve.length - 1), height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    curve.forEach((val, idx) => {
      if (idx === 0) ctx.moveTo(getX(idx), getY(val));
      else ctx.lineTo(getX(idx), getY(val));
    });
    ctx.stroke();

    // Baseline 100 mark
    const base100Y = getY(100.0);
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, base100Y);
    ctx.lineTo(width - padding.right, base100Y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText('100.0 (Base)', width - padding.right + 5, base100Y + 3);
  }

  // Handle Window Resizing for Canvas
  window.addEventListener('resize', () => {
    renderCandleChart();
    if (state.backtestData && state.backtestData.equity_curve) {
      renderEquityCurve(state.backtestData.equity_curve);
    }
  });

  // Initial Boot
  refreshAllData();
  fetchPortfolio();

  // Auto-refresh market data every 15 seconds
  state.autoRefreshInterval = setInterval(() => {
    if (state.currentTab === 'tab-dashboard') {
      refreshAllData();
    }
  }, 15000);
});
