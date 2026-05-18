import time
import random
import threading
import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime, timedelta
import os
import warnings
from sklearn.exceptions import ConvergenceWarning

# Har tarah ki AI warnings band karne ke liye (Clean Console)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings("ignore", category=ConvergenceWarning)

from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# IMPORTANT: Run `pip install MetaTrader5 pandas numpy plotly scikit-learn xlsxwriter`
try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("MetaTrader5 library nahi mili. Simulation mode me run kar rahe hain.")


class UltimateQuantEngine:
    def __init__(self, symbol="GOLD.i#", risk_percent=2.0):
        self.symbol = symbol
        self.risk_percent = risk_percent
        self.is_connected = False
        self.active_trade = None
        self.market_memory_m1 = deque(maxlen=300)
        self.market_memory_m5 = deque(maxlen=100)
        self.backtest_logs = []
        self.contract_size = 100.0
        self.daily_pnl = 0.0
        self.target_milestone_notified = False
        self.consecutive_losses = 0

    def connect_broker(self):
        if not MT5_AVAILABLE:
            self.is_connected = True
            return False, "MetaTrader5 library missing. Simulation Mode Only."
        if not mt5.initialize():
            return False, "MT5 Initialization failed. Check MT5 Terminal."

        sym_info = mt5.symbol_info(self.symbol)
        if sym_info is None:
            return False, f"Symbol {self.symbol} not found in MT5."
        if not sym_info.visible:
            mt5.symbol_select(self.symbol, True)

        self.is_connected = True
        return True, f"Connected to {self.symbol} successfully!"

    def detect_ml_support_resistance(self, df_m5, current_price):
        if len(df_m5) < 30: return current_price - 2.0, current_price + 2.0
        prices = np.concatenate([df_m5['high'].values, df_m5['low'].values]).reshape(-1, 1)
        unique_prices = len(np.unique(prices))
        n_clusters = min(5, unique_prices)
        if n_clusters < 2: return current_price - 2.0, current_price + 2.0
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit(prices)
        clusters = sorted(kmeans.cluster_centers_.flatten())
        resistances = [c for c in clusters if c > current_price]
        supports = [c for c in clusters if c < current_price]
        nearest_resistance = min(resistances) if len(resistances) > 0 else current_price + 3.0
        nearest_support = max(supports) if len(supports) > 0 else current_price - 3.0
        return nearest_support, nearest_resistance

    def get_m1_precision_sl(self, df_m1, action):
        if len(df_m1) < 10: return 1.0
        if action == "BUY":
            local_min = argrelextrema(df_m1['low'].values[-20:], np.less, order=2)[0]
            return df_m1['low'].values[-20:][local_min[-1]] - 0.2 if len(local_min) > 0 else df_m1['low'].min() - 0.2
        else:
            local_max = argrelextrema(df_m1['high'].values[-20:], np.greater, order=2)[0]
            return df_m1['high'].values[-20:][local_max[-1]] + 0.2 if len(local_max) > 0 else df_m1['high'].max() + 0.2

    def calculate_god_level_lot_size(self, current_price, m1_sl_price, target_loss_dollars=2.0):
        distance_points = abs(current_price - m1_sl_price)
        if distance_points < 0.3: distance_points = 0.3
        ideal_lot = target_loss_dollars / (distance_points * self.contract_size)
        lot_size = max(0.01, min(round(ideal_lot, 2), 2.0))
        actual_sl_distance = target_loss_dollars / (lot_size * self.contract_size)
        return actual_sl_distance, lot_size

    def analyze_m5_trend(self, df_m5):
        if len(df_m5) < 20: return "NEUTRAL"
        df_m5['ema20'] = df_m5['close'].ewm(span=20, adjust=False).mean()
        curr_close = df_m5['close'].iloc[-1]
        ema20 = df_m5['ema20'].iloc[-1]
        if curr_close > ema20:
            return "BULL"
        elif curr_close < ema20:
            return "BEAR"
        return "NEUTRAL"

    def the_supreme_decision_maker(self, df_m1, df_m5, m5_trend_override=None, current_wallet_balance=0.0):
        if len(df_m1) < 20 or len(df_m5) < 20:
            return "WAIT", 0, 0, 0.0, 0.01, "NONE", 2.0

        current_price = df_m1['close'].iloc[-1]
        m5_trend = m5_trend_override if m5_trend_override else self.analyze_m5_trend(df_m5)
        support_m5, resistance_m5 = self.detect_ml_support_resistance(df_m5, current_price)

        delta = df_m1['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        rsi_m1 = 100 - (100 / (1 + rs)).iloc[-1]
        momentum_m1 = df_m1['close'].iloc[-1] - df_m1['close'].iloc[-5]

        if current_wallet_balance > 0 and current_wallet_balance <= 200:
            target_risk, tp_mult, base_min_conf = 2.0, 5.0, 94.0
        elif current_wallet_balance > 200 and current_wallet_balance < 1000:
            target_risk, tp_mult, base_min_conf = current_wallet_balance * 0.01, 4.0, 92.0
        elif current_wallet_balance >= 1000:
            target_risk, tp_mult, base_min_conf = current_wallet_balance * 0.005, 4.0, 90.0
        else:
            target_risk, tp_mult, base_min_conf = 2.0, 4.0, 92.0

        action, ai_confidence, strategy_used = "WAIT", 0.0, "NONE"

        if m5_trend == "BULL" and rsi_m1 < 45 and momentum_m1 > 0.1:
            action, ai_confidence, strategy_used = "BUY", 92.0 + (45 - rsi_m1) * 0.2, "PULLBACK_SCALP"
        elif m5_trend == "BEAR" and rsi_m1 > 55 and momentum_m1 < -0.1:
            action, ai_confidence, strategy_used = "SELL", 92.0 + (rsi_m1 - 55) * 0.2, "PULLBACK_SCALP"

        if m5_trend == "BULL" and momentum_m1 > 0.5 and rsi_m1 < 80:
            action, ai_confidence, strategy_used = "BUY", 95.0 + momentum_m1 * 2.0, "TREND_BREAKOUT"
        elif m5_trend == "BEAR" and momentum_m1 < -0.5 and rsi_m1 > 20:
            action, ai_confidence, strategy_used = "SELL", 95.0 + abs(momentum_m1) * 2.0, "TREND_BREAKOUT"

        min_confidence = base_min_conf if self.consecutive_losses == 0 else base_min_conf + 2.0

        if action != "WAIT" and ai_confidence >= min_confidence:
            m1_raw_sl = self.get_m1_precision_sl(df_m1, action)
            sl_distance, lot_size = self.calculate_god_level_lot_size(current_price, m1_raw_sl, target_risk)
            if action == "BUY":
                tp_distance = max(resistance_m5 - current_price, sl_distance * tp_mult)
            else:
                tp_distance = max(current_price - support_m5, sl_distance * tp_mult)
            return action, sl_distance, tp_distance, round(min(ai_confidence, 99.9),
                                                           2), lot_size, strategy_used, target_risk

        return "WAIT", 0, 0, 0.0, 0.01, "NONE", target_risk

    def place_real_mt5_order(self, action_type, lot_size, price, sl, tp):
        if not self.is_connected or not MT5_AVAILABLE: return None
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None: return None

        if action_type == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            exe_price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            exe_price = tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": self.symbol, "volume": float(lot_size),
            "type": order_type, "price": float(exe_price), "sl": float(sl), "tp": float(tp),
            "deviation": 10, "magic": 999111, "comment": "God Level AI",
            "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
        }
        return mt5.order_send(request)

    def manage_dynamic_trailing_sl(self, current_price):
        if not self.active_trade: return
        trade_type = self.active_trade['type']
        entry_price = self.active_trade['entry_price']
        current_sl = self.active_trade['sl']
        ticket = self.active_trade.get('ticket')
        lot_size = self.active_trade['lot']
        target_risk = self.active_trade.get('risk_amount', 2.0)

        points_for_risk = target_risk / (lot_size * self.contract_size)
        activation_dist = points_for_risk * 1.0
        trailing_gap = points_for_risk * 0.5

        if trade_type == "BUY":
            if current_price - entry_price >= activation_dist:
                new_sl = current_price - trailing_gap
                if new_sl > current_sl:
                    self.active_trade['sl'] = new_sl
                    self.active_trade['trailing_hits'] = self.active_trade.get('trailing_hits', 0) + 1
                    if ticket and self.is_connected and MT5_AVAILABLE: mt5.order_send(
                        {"action": mt5.TRADE_ACTION_SLTP, "position": ticket, "sl": float(new_sl), "magic": 999111})
        elif trade_type == "SELL":
            if entry_price - current_price >= activation_dist:
                new_sl = current_price + trailing_gap
                if new_sl < current_sl or current_sl == 0:
                    self.active_trade['sl'] = new_sl
                    self.active_trade['trailing_hits'] = self.active_trade.get('trailing_hits', 0) + 1
                    if ticket and self.is_connected and MT5_AVAILABLE: mt5.order_send(
                        {"action": mt5.TRADE_ACTION_SLTP, "position": ticket, "sl": float(new_sl), "magic": 999111})

    def sync_and_trade_live(self):
        if not self.is_connected or not MT5_AVAILABLE: return

        rates_m1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 300)
        rates_m5 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, 100)

        if rates_m1 is not None and len(rates_m1) > 0:
            for r in rates_m1: self.market_memory_m1.append(
                {'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']})
        if rates_m5 is not None and len(rates_m5) > 0:
            for r in rates_m5: self.market_memory_m5.append(
                {'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']})

        if len(self.market_memory_m1) < 20: return
        current_price = self.market_memory_m1[-1]['close']

        positions = mt5.positions_get(symbol=self.symbol)

        if self.active_trade and (positions is None or len(positions) == 0):
            closed_trade = self.active_trade
            exit_price = 0.0
            pnl = 0.0

            from_date = datetime.now() - timedelta(days=1)
            to_date = datetime.now() + timedelta(days=1)
            history_deals = mt5.history_deals_get(from_date, to_date, position=closed_trade.get('ticket', 0))
            if history_deals and len(history_deals) > 0:
                for deal in history_deals:
                    if deal.entry == mt5.DEAL_ENTRY_OUT:
                        exit_price = deal.price
                        pnl = deal.profit

            trade_log = {
                'Type': closed_trade['type'], 'Strategy': closed_trade['strategy'],
                'Entry $': closed_trade['entry_price'], 'Exit $': exit_price,
                'PnL ($)': pnl, 'Time': datetime.now().strftime('%H:%M:%S')
            }
            if 'live_trades' not in st.session_state: st.session_state.live_trades = []
            st.session_state.live_trades.insert(0, trade_log)

            # Cumulative PnL tracking for charting
            if 'live_equity_curve' not in st.session_state: st.session_state.live_equity_curve = [0.0]
            st.session_state.live_equity_curve.append(st.session_state.live_equity_curve[-1] + pnl)

            card_style = "card-profit" if pnl > 0 else "card-loss"
            pnl_color = "#00E676" if pnl > 0 else "#FF1744"
            sign = "+" if pnl > 0 else ""
            new_card = f"""
            <div class="live-trade-card {card_style}">
                <div>
                    <span style="color: #fff; font-weight: bold; font-size: 14px;">{closed_trade['type']} Closed ({closed_trade['strategy']})</span><br>
                    <span style="color:#718096; font-size:11px;">Entry: {closed_trade['entry_price']:.2f} ➔ Exit: {exit_price:.2f}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: {pnl_color}; font-weight: bold; font-size: 16px;">{sign}${pnl:.2f}</span><br>
                    <span style="color:#718096; font-size:10px;">{trade_log['Time']}</span>
                </div>
            </div>
            """
            if 'live_trade_cards' not in st.session_state: st.session_state.live_trade_cards = []
            st.session_state.live_trade_cards.insert(0, new_card)
            if len(st.session_state.live_trade_cards) > 10: st.session_state.live_trade_cards.pop()

            self.active_trade = None

        elif self.active_trade and positions and len(positions) > 0:
            self.manage_dynamic_trailing_sl(current_price)
            # Safely update floating PnL in session state for active position
            matching_pos = [p for p in positions if p.ticket == self.active_trade.get('ticket')]
            if matching_pos:
                st.session_state.floating_pnl = matching_pos[0].profit
            else:
                st.session_state.floating_pnl = 0.0

        if not self.active_trade:
            st.session_state.floating_pnl = 0.0
            df_m1 = pd.DataFrame(list(self.market_memory_m1))
            df_m5 = pd.DataFrame(list(self.market_memory_m5))
            acc_info = mt5.account_info()
            bal = acc_info.balance if acc_info else 0.0

            action, sl_dist, tp_dist, confidence, lot_size, strategy, target_risk = self.the_supreme_decision_maker(
                df_m1, df_m5, current_wallet_balance=bal)

            if action != "WAIT":
                sl = current_price - sl_dist if action == "BUY" else current_price + sl_dist
                tp = current_price + tp_dist if action == "BUY" else current_price - tp_dist
                res = self.place_real_mt5_order(action, lot_size, current_price, sl, tp)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    self.active_trade = {'type': action, 'entry_price': current_price, 'sl': sl, 'initial_sl': sl,
                                         'tp': tp, 'lot': lot_size, 'ticket': res.order, 'conf': confidence,
                                         'strategy': strategy, 'risk_amount': target_risk}


st.set_page_config(page_title="AuraQuant Pro AI", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .metric-box { background: rgba(18, 24, 38, 0.7); border: 1px solid #2D3748; border-radius: 12px; padding: 15px; text-align: center; }
    .metric-value { font-size: 26px; font-weight: bold; color: #fff; }
    .metric-label { font-size: 13px; color: #A0AEC0; text-transform: uppercase; letter-spacing: 1px; }
    .profit-text { color: #00E676 !important; }
    .loss-text { color: #FF1744 !important; }
    .instant-box { background: rgba(30, 41, 59, 0.6); padding: 15px; border-radius: 12px; border: 1px dashed #475569; margin-bottom: 10px; }
    .live-trade-card { display: flex; justify-content: space-between; padding: 15px; margin-bottom: 10px; border-radius: 8px; background: rgba(15, 23, 42, 0.8); }
    .card-profit { border-left: 4px solid #00E676; box-shadow: 0 4px 15px rgba(0, 230, 118, 0.1); }
    .card-loss { border-left: 4px solid #FF1744; box-shadow: 0 4px 15px rgba(255, 23, 68, 0.1); }

    /* Radar animation for scanning */
    .radar-pulse {
        width: 15px; height: 15px; border-radius: 50%; background: #3182CE; display: inline-block;
        box-shadow: 0 0 0 0 rgba(49, 130, 206, 1); transform: scale(1); animation: pulse 2s infinite; margin-right: 10px;
    }
    .trade-pulse {
        width: 15px; height: 15px; border-radius: 50%; background: #00E676; display: inline-block;
        box-shadow: 0 0 0 0 rgba(0, 230, 118, 1); transform: scale(1); animation: pulse-green 2s infinite; margin-right: 10px;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(49, 130, 206, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(49, 130, 206, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(49, 130, 206, 0); }
    }
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 230, 118, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }
    .active-trade-panel {
        background: linear-gradient(145deg, #1A202C, #2D3748); border: 2px solid #00E676; 
        border-radius: 12px; padding: 20px; box-shadow: 0 8px 32px rgba(0, 230, 118, 0.15);
    }
</style>
""", unsafe_allow_html=True)

if 'engine' not in st.session_state:
    st.session_state.engine = UltimateQuantEngine(symbol="XAUUSD")
if 'ui_connected' not in st.session_state:
    st.session_state.ui_connected = False
if 'live_trades' not in st.session_state:
    st.session_state.live_trades = []
if 'live_trade_cards' not in st.session_state:
    st.session_state.live_trade_cards = []
if 'live_equity_curve' not in st.session_state:
    st.session_state.live_equity_curve = [0.0]
if 'floating_pnl' not in st.session_state:
    st.session_state.floating_pnl = 0.0
if 'is_running_live' not in st.session_state:
    st.session_state.is_running_live = False

engine = st.session_state.engine

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2642/2642502.png", width=60)
    st.markdown("### AuraQuant Pro AI")
    st.markdown("Institutional God-Level Algo")
    st.divider()

    if not st.session_state.ui_connected:
        st.warning("Broker Disconnected. System Locked.")
    else:
        st.success(f"Connected to MT5 ({engine.symbol})")
        app_mode = st.radio("Select Operating Mode:", ["📊 Backtesting Simulator", "🔴 Live Trading Engine"],
                            key="nav_app_mode")
        st.divider()
        if st.button("Disconnect Terminal", width="stretch", key="nav_disconnect_btn"):
            if MT5_AVAILABLE: mt5.shutdown()
            st.session_state.ui_connected = False
            st.session_state.is_running_live = False
            st.rerun()

if not st.session_state.ui_connected:
    st.title("Welcome to AuraQuant Pro AI 🌌")
    st.markdown("Authenticate your MetaTrader 5 terminal to unlock the omni-engine dashboard.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='instant-box'>", unsafe_allow_html=True)
        sym_input = st.text_input("Active Asset Symbol (As per Broker)", value="XAUUSD", key="auth_sym_input")
        if st.button("🔗 Connect to MT5 Terminal", type="primary", width="stretch", key="auth_connect_btn"):
            engine.symbol = sym_input
            success, msg = engine.connect_broker()
            if success:
                st.session_state.ui_connected = True
                st.success(msg)
                time.sleep(1)
                st.rerun()
            else:
                st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.info(
            "💡 **Instructions:** Ensure MT5 is running on your desktop and 'Allow Algorithmic Trading' is enabled in options.")

elif app_mode == "📊 Backtesting Simulator":
    st.title("📊 Limitless Profit Simulator")

    b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
    with b_col1:
        sim_days = st.number_input("Lookback Days", min_value=1, max_value=30, value=7, key="bt_days")
    with b_col2:
        sim_bal = st.number_input("Virtual Starting Balance ($)", value=40.0, key="bt_bal")
    with b_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_sim = st.button("🚀 Run God-Level Backtest", type="primary", width="stretch", key="bt_run_btn")

    if run_sim:
        if not MT5_AVAILABLE:
            st.error("MetaTrader5 is required for real backtesting data!")
        else:
            with st.spinner(f"Quantum Computing {sim_days} days of M1/M5 Data..."):
                m1_bars = sim_days * 1440
                m5_bars = sim_days * 288
                rates_m1 = mt5.copy_rates_from_pos(engine.symbol, mt5.TIMEFRAME_M1, 0, m1_bars)
                rates_m5 = mt5.copy_rates_from_pos(engine.symbol, mt5.TIMEFRAME_M5, 0, m5_bars)

                if rates_m1 is None or len(rates_m1) == 0:
                    st.error("Failed to fetch data. Check MT5 symbol name.")
                else:
                    df_m1 = pd.DataFrame(rates_m1)
                    df_m1['time'] = pd.to_datetime(df_m1['time'], unit='s')
                    df_m5 = pd.DataFrame(rates_m5)
                    df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s')
                    df_m5['ema20'] = df_m5['close'].ewm(span=20, adjust=False).mean()
                    df_m5['m5_trend'] = np.where(df_m5['close'] > df_m5['ema20'], 'BULL', 'BEAR')
                    df_merged = pd.merge_asof(df_m1, df_m5[['time', 'm5_trend']], on='time', direction='backward')

                    virtual_balance = sim_bal
                    engine.market_memory_m1.clear()
                    engine.backtest_logs.clear()
                    engine.active_trade = None
                    trade_id_counter = 1

                    progress_bar = st.progress(0)
                    total_rows = len(df_merged)

                    for index, row in df_merged.iterrows():
                        if index % 500 == 0: progress_bar.progress(index / total_rows)

                        engine.market_memory_m1.append(
                            {'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close']})
                        if len(engine.market_memory_m1) < 20: continue

                        current_time, current_price, high_price, low_price = row['time'], row['close'], row['high'], \
                        row['low']

                        if engine.active_trade:
                            trade = engine.active_trade
                            exit_reason = None
                            exit_price = 0.0
                            if trade['type'] == 'BUY':
                                if low_price <= trade['sl']:
                                    exit_reason = "Trailed SL" if trade.get('trailing_hits', 0) > 0 else "SL Hit"
                                    exit_price = trade['sl']
                                elif high_price >= trade['tp']:
                                    exit_reason = "TP Hit"
                                    exit_price = trade['tp']
                            elif trade['type'] == 'SELL':
                                if high_price >= trade['sl']:
                                    exit_reason = "Trailed SL" if trade.get('trailing_hits', 0) > 0 else "SL Hit"
                                    exit_price = trade['sl']
                                elif low_price <= trade['tp']:
                                    exit_reason = "TP Hit"
                                    exit_price = trade['tp']

                            if exit_reason:
                                pnl = (exit_price - trade['entry_price']) * trade['lot'] * engine.contract_size if \
                                trade['type'] == 'BUY' else (trade['entry_price'] - exit_price) * trade[
                                    'lot'] * engine.contract_size
                                virtual_balance += pnl
                                engine.backtest_logs.append({
                                    "Trade ID": f"TRD-{trade_id_counter:03d}", "Type": trade['type'],
                                    "Entry": trade['entry_price'], "Exit": exit_price,
                                    "Lot": trade['lot'], "PnL ($)": pnl, "Bal ($)": virtual_balance
                                })
                                trade_id_counter += 1
                                engine.active_trade = None

                        if not engine.active_trade:
                            df_m1_temp = pd.DataFrame(list(engine.market_memory_m1))
                            df_m5_temp = pd.DataFrame(
                                {'close': [row['close']], 'high': [row['high']], 'low': [row['low']]})
                            for i in range(20): df_m5_temp.loc[i] = df_m5_temp.loc[0]

                            act, sl_dist, tp_dist, conf, lot, strat, t_risk = engine.the_supreme_decision_maker(
                                df_m1_temp, df_m5_temp, m5_trend_override=row['m5_trend'],
                                current_wallet_balance=virtual_balance)
                            if act != "WAIT":
                                sl = current_price - sl_dist if act == "BUY" else current_price + sl_dist
                                tp = current_price + tp_dist if act == "BUY" else current_price - tp_dist
                                engine.active_trade = {'type': act, 'entry_time': current_time,
                                                       'entry_price': current_price, 'sl': sl, 'initial_sl': sl,
                                                       'tp': tp, 'lot': lot, 'conf': conf, 'strategy': strat,
                                                       'risk_amount': t_risk}

                    progress_bar.progress(1.0)

                    if len(engine.backtest_logs) > 0:
                        df_logs = pd.DataFrame(engine.backtest_logs)
                        wins = len(df_logs[df_logs['PnL ($)'] > 0])
                        losses = len(df_logs) - wins
                        win_rate = (wins / len(df_logs)) * 100
                        net_profit = virtual_balance - sim_bal

                        st.markdown("### 🏆 Backtest Results Visualized")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.markdown(
                            f"<div class='metric-box'><div class='metric-label'>Total Trades</div><div class='metric-value'>{len(df_logs)}</div></div>",
                            unsafe_allow_html=True)
                        c2.markdown(
                            f"<div class='metric-box'><div class='metric-label'>Win Rate</div><div class='metric-value'>{win_rate:.1f}%</div></div>",
                            unsafe_allow_html=True)
                        c3.markdown(
                            f"<div class='metric-box'><div class='metric-label'>Net Profit</div><div class='metric-value profit-text'>+${net_profit:.2f}</div></div>",
                            unsafe_allow_html=True)
                        c4.markdown(
                            f"<div class='metric-box'><div class='metric-label'>Final Balance</div><div class='metric-value'>${virtual_balance:.2f}</div></div>",
                            unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        graph_col1, graph_col2 = st.columns([2, 1])

                        with graph_col1:
                            st.markdown("##### 📈 Equity Growth Curve")
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(y=df_logs['Bal ($)'], mode='lines+markers', name='Balance',
                                                     line=dict(color='#00E676', width=3), fill='tozeroy',
                                                     fillcolor='rgba(0, 230, 118, 0.1)'))
                            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                              font=dict(color='#A0AEC0'), margin=dict(l=0, r=0, t=10, b=0), height=300)
                            st.plotly_chart(fig, use_container_width=True)

                        with graph_col2:
                            st.markdown("##### 🎯 Win vs Loss Ratio")
                            fig_pie = px.pie(values=[wins, losses], names=['Wins', 'Losses'],
                                             color_discrete_sequence=['#00E676', '#FF1744'], hole=0.6)
                            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                                  font=dict(color='#A0AEC0'), margin=dict(l=0, r=0, t=10, b=0),
                                                  height=300, showlegend=False)
                            st.plotly_chart(fig_pie, use_container_width=True)

                        st.markdown("##### 📜 Detailed Execution Log")
                        st.dataframe(df_logs.style.map(
                            lambda v: "color:#00E676; font-weight:bold" if v > 0 else "color:#FF1744" if v < 0 else "",
                            subset=['PnL ($)']), use_container_width=True)
                    else:
                        st.warning("No trades executed. Strict criteria not met.")

elif app_mode == "🔴 Live Trading Engine":
    st.title("🔴 Live Hedge Fund Terminal")

    # Calculate Session Analytics from st.session_state
    df_live = pd.DataFrame(st.session_state.live_trades)
    session_trades = len(df_live)
    session_pnl = df_live['PnL ($)'].sum() if session_trades > 0 else 0.0
    session_wins = len(df_live[df_live['PnL ($)'] > 0]) if session_trades > 0 else 0
    session_win_rate = (session_wins / session_trades * 100) if session_trades > 0 else 0.0

    # MT5 Live Account Info
    acc_bal, acc_eq, acc_margin = 0.0, 0.0, 0.0
    if MT5_AVAILABLE:
        ai = mt5.account_info()
        if ai: acc_bal, acc_eq, acc_margin = ai.balance, ai.equity, ai.margin_free

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div class='metric-box'><div class='metric-label'>Live Balance</div><div class='metric-value'>${acc_bal:.2f}</div></div>",
        unsafe_allow_html=True)
    c2.markdown(
        f"<div class='metric-box'><div class='metric-label'>Live Equity</div><div class='metric-value'>${acc_eq:.2f}</div></div>",
        unsafe_allow_html=True)
    c3.markdown(
        f"<div class='metric-box'><div class='metric-label'>Session PnL</div><div class='metric-value {'profit-text' if session_pnl >= 0 else 'loss-text'}'>${session_pnl:.2f}</div></div>",
        unsafe_allow_html=True)
    c4.markdown(
        f"<div class='metric-box'><div class='metric-label'>Win Rate ({session_trades} Trades)</div><div class='metric-value'>{session_win_rate:.1f}%</div></div>",
        unsafe_allow_html=True)

    st.markdown("---")

    # AI Engine Status Bar & Active Trade Monitor
    status_col, active_col = st.columns([1, 2])

    with status_col:
        st.markdown("#### ⚙️ AI Engine Status")
        if st.session_state.is_running_live:
            if engine.active_trade:
                st.markdown(
                    "<div style='padding:15px; border-radius:8px; background:rgba(0, 230, 118, 0.1); border:1px solid #00E676;'><div class='trade-pulse'></div><b style='color:#00E676; font-size:18px;'>ACTIVE TRADE IN PROGRESS</b><br><span style='color:#A0AEC0; font-size:12px;'>Managing Trailing Stop Loss & Target</span></div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div style='padding:15px; border-radius:8px; background:rgba(49, 130, 206, 0.1); border:1px solid #3182CE;'><div class='radar-pulse'></div><b style='color:#3182CE; font-size:18px;'>SCANNING MARKET</b><br><span style='color:#A0AEC0; font-size:12px;'>KMeans & Neural logic seeking setup...</span></div>",
                    unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🛑 STOP AI ENGINE", key="live_stop_btn", width="stretch"):
                st.session_state.is_running_live = False
                st.rerun()
        else:
            st.markdown(
                "<div style='padding:15px; border-radius:8px; background:rgba(255, 23, 68, 0.1); border:1px solid #FF1744;'><b style='color:#FF1744; font-size:18px;'>ENGINE IDLE (OFFLINE)</b><br><span style='color:#A0AEC0; font-size:12px;'>Awaiting startup command.</span></div>",
                unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 START AI ENGINE", type="primary", key="live_start_btn", width="stretch"):
                st.session_state.is_running_live = True
                st.rerun()

    with active_col:
        st.markdown("#### 🎯 Active Position Tracker")
        if engine.active_trade:
            t = engine.active_trade
            fpnl = st.session_state.floating_pnl
            color = "#00E676" if fpnl > 0 else "#FF1744"
            st.markdown(f"""
            <div class='active-trade-panel'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <h3 style='margin:0; color:#fff;'>{t['type']} <span style='font-size:14px; color:#A0AEC0;'>({t['lot']} Lots)</span></h3>
                        <span style='color:#A0AEC0; font-size:13px;'>Strat: {t['strategy']} | Conf: {t['conf']}%</span>
                    </div>
                    <div style='text-align:right;'>
                        <h2 style='margin:0; color:{color};'>${fpnl:.2f}</h2>
                        <span style='color:#A0AEC0; font-size:12px;'>Floating PnL</span>
                    </div>
                </div>
                <hr style='border-color:#4A5568;'>
                <div style='display:flex; justify-content:space-between; text-align:center;'>
                    <div><span style='color:#A0AEC0; font-size:11px;'>ENTRY</span><br><b style='color:#fff;'>{t['entry_price']:.2f}</b></div>
                    <div><span style='color:#A0AEC0; font-size:11px;'>STOP LOSS</span><br><b style='color:#FF1744;'>{t['sl']:.2f}</b></div>
                    <div><span style='color:#A0AEC0; font-size:11px;'>TARGET</span><br><b style='color:#00E676;'>{t['tp']:.2f}</b></div>
                    <div><span style='color:#A0AEC0; font-size:11px;'>RISK</span><br><b style='color:#fff;'>${t.get('risk_amount', 0):.2f}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: rgba(18, 24, 38, 0.7); border: 1px dashed #2D3748; padding: 35px; text-align: center; border-radius: 12px; color: #718096;">
                    <i>No Active Trades Running. Engine is hunting.</i>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Charts and Execution Feed
    chart_col, feed_col = st.columns([2, 1])

    with chart_col:
        st.markdown("#### 📈 Live Session Growth Curve")
        if len(st.session_state.live_equity_curve) > 1:
            fig_live = go.Figure()
            fig_live.add_trace(go.Scatter(y=st.session_state.live_equity_curve, mode='lines', name='Session PnL',
                                          line=dict(color='#00BFFF', width=3), fill='tozeroy',
                                          fillcolor='rgba(0, 191, 255, 0.1)'))
            fig_live.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                   font=dict(color='#A0AEC0'), margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig_live, use_container_width=True)
        else:
            st.info("Curve will plot after the first trade closes.")

        st.markdown("#### 🚨 Manual Overrides")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            if st.button("🟢 QUICK BUY", key="live_buy_btn", width="stretch"):
                tick = mt5.symbol_info_tick(engine.symbol) if MT5_AVAILABLE else None
                if tick:
                    engine.place_real_mt5_order("BUY", 0.01, tick.ask, tick.ask - 2.0, tick.ask + 4.0)
                else:
                    st.toast("Tick Data Unavailable!", icon="⚠️")
        with m_col2:
            if st.button("🔴 QUICK SELL", key="live_sell_btn", width="stretch"):
                tick = mt5.symbol_info_tick(engine.symbol) if MT5_AVAILABLE else None
                if tick:
                    engine.place_real_mt5_order("SELL", 0.01, tick.bid, tick.bid + 2.0, tick.bid - 4.0)
                else:
                    st.toast("Tick Data Unavailable!", icon="⚠️")
        with m_col3:
            if st.button("🚨 PANIC CLOSE", key="cmd_close_all_btn", width="stretch", type="primary"):
                if MT5_AVAILABLE:
                    pos = mt5.positions_get(symbol=engine.symbol)
                    if pos:
                        for p in pos:
                            action = mt5.ORDER_TYPE_SELL if p.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                            tick = mt5.symbol_info_tick(engine.symbol)
                            if tick:
                                price = tick.bid if action == mt5.ORDER_TYPE_SELL else tick.ask
                                mt5.order_send(
                                    {"action": mt5.TRADE_ACTION_DEAL, "symbol": engine.symbol, "volume": p.volume,
                                     "type": action, "position": p.ticket, "price": price, "magic": 999111})
                engine.active_trade = None
                st.toast("🚨 All positions liquidated!", icon="🔥")

    with feed_col:
        st.markdown("#### 📜 Live Executed Trades")
        if 'live_trade_cards' in st.session_state and len(st.session_state.live_trade_cards) > 0:
            st.markdown(
                f"<div style='max-height:400px; overflow-y:auto;'>{''.join(st.session_state.live_trade_cards)}</div>",
                unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: rgba(18, 24, 38, 0.7); border: 1px dashed #2D3748; padding: 20px; text-align: center; border-radius: 12px; color: #718096;">
                    <i>Awaiting first closed position...</i>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 📊 Session Transactions Ledger")
    if session_trades > 0:
        st.dataframe(df_live.style.map(
            lambda val: "color: #00E676; font-weight: bold;" if val > 0 else "color: #FF1744;" if val < 0 else "",
            subset=['PnL ($)']), use_container_width=True)
    else:
        st.info("No trades executed in the current session.")

    # Auto-Refresh Loop when Live Engine is ON
    if st.session_state.is_running_live:
        engine.sync_and_trade_live()
        time.sleep(5)  # Auto-sync every 5 seconds
        st.rerun()