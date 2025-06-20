# strategies.py – Enhanced for Equity + Option Signals

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import json
from datetime import datetime, timedelta
from option_chain_utils import get_option_signals  # new util to be created

warnings.filterwarnings('ignore')

live_signals = []

__all__ = [
    "scan_symbols_enhanced",
    "generate_enhanced_signals",
    "get_signals",
    "get_signal_analytics",
    "filter_signals",
    "calculate_indicators",
    "calculate_signal_strength"
]

def calculate_indicators(df):
    try:
        df['EMA_8'] = df['Close'].ewm(span=8).mean()
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        df['EMA_200'] = df['Close'].ewm(span=200).mean()

        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['Signal_Line'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']

        bb_period = 20
        df['BB_Middle'] = df['Close'].rolling(bb_period).mean()
        bb_std = df['Close'].rolling(bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100

        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        df['Volume_Spike'] = df['Volume_Ratio'] > 2
        df['Supertrend'] = df['Close'] > ((df['High'] + df['Low']) / 2 - 3 * df['Close'].rolling(10).std())

        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = 2 * df['Pivot'] - df['Low']
        df['S1'] = 2 * df['Pivot'] - df['High']

        df['Hammer'] = ((df['Close'] - df['Low']) > 2 * (df['High'] - df['Close'])) & \
                       ((df['High'] - df['Close']) < 0.1 * (df['Close'] - df['Low']))

        df['Trend_Strength'] = np.where((df['EMA_8'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50']), 1, 0)
        return df

    except Exception as e:
        print("Indicator Calc Error:", e)
        return df

def calculate_signal_strength(hard_hits, soft_hits):
    base = 40
    score = base + len(hard_hits) * 15 + len(soft_hits) * 5
    if 'MACD Bullish Cross' in hard_hits and 'RSI Strong' in hard_hits:
        score += 10
    if 'Supertrend Reversal' in hard_hits:
        score += 8
    return min(100, score)

def generate_enhanced_signals(df, symbol, timeframe):
    if df.empty or len(df) < 20:
        return []
    signals = []
    try:
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        hard_hits, soft_hits = [], []

        if latest['MACD'] > latest['Signal_Line'] and previous['MACD'] <= previous['Signal_Line']:
            hard_hits.append("MACD Bullish Cross")
        elif latest['MACD_Histogram'] > previous['MACD_Histogram']:
            soft_hits.append("MACD Momentum")

        if latest['RSI'] > 60:
            hard_hits.append("RSI Strong")
        elif latest['RSI'] > 50:
            soft_hits.append("RSI Bullish")

        if latest['Supertrend'] and not previous['Supertrend']:
            hard_hits.append("Supertrend Reversal")
        elif latest['Supertrend']:
            soft_hits.append("Trend Positive")

        if latest['EMA_8'] > latest['EMA_20'] > latest['EMA_50']:
            soft_hits.append("EMA Bullish")

        if latest['Volume_Spike']:
            hard_hits.append("Volume Spike")

        score = calculate_signal_strength(hard_hits, soft_hits)
        signal_type = "Strong Buy" if score >= 85 else "Buy" if score >= 70 else "Watchlist"

        if score >= 60:
            signals.append({
                "symbol": symbol,
                "strategyTags": hard_hits + soft_hits,
                "type": "equity",
                "signalType": signal_type,
                "timeframe": timeframe,
                "price": round(latest['Close'], 2),
                "volume": int(latest['Volume']),
                "strength": score,
                "sparkline": df['Close'].tail(20).tolist(),
                "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            })

    except Exception as e:
        print(f"Signal generation error for {symbol} - {e}")
    return signals

def scan_symbols_enhanced(symbols, timeframes):
    global live_signals
    live_signals = []

    for symbol in symbols:
        for tf in timeframes:
            try:
                period = "6mo" if tf == "1d" else "5d"
                interval = tf
                df = yf.download(symbol, period=period, interval=interval)
                if df.empty:
                    continue
                df = calculate_indicators(df)
                signals = generate_enhanced_signals(df, symbol, tf)
                live_signals.extend(signals)
            except Exception as e:
                print(f"Scan error {symbol} - {e}")

    # Option Chain Signals (from utility)
    try:
        option_signals = get_option_signals()  # Should return formatted signal dicts
        live_signals.extend(option_signals)
    except Exception as e:
        print("Option signal error:", e)

    return sorted(live_signals, key=lambda x: x['strength'], reverse=True)

def get_signals():
    return live_signals

def get_signal_analytics():
    signals = live_signals
    if not signals:
        return {}
    by_type = {}
    for sig in signals:
        t = sig.get('type', 'equity')
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "total": len(signals),
        "by_type": by_type,
        "avg_strength": round(sum(s['strength'] for s in signals) / len(signals), 2)
    }

def filter_signals(min_strength=60, types=None):
    filtered = [s for s in live_signals if s['strength'] >= min_strength]
    if types:
        filtered = [s for s in filtered if s.get('type') in types]
    return filtered
