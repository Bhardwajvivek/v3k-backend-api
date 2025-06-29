# utils.py – Utility functions for V3k AI Trading Bot

import pandas as pd
import numpy as np
import yfinance as yf

def calculate_moving_average(data, window):
    return data['Close'].rolling(window=window).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

# ✅ Added missing function
def get_live_stock_data(symbol, period="5d", interval="15m"):
    """
    Fetch live stock data for the given symbol.
    """
    try:
        df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_technical_indicators(df):
    """
    Add all key technical indicators to the dataframe.
    Used before signal generation.
    """
    df['EMA_8'] = df['Close'].ewm(span=8, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df

def analyze_stock_signals(symbol, df):
    """
    Analyze all major indicators on the given dataframe and generate signals.
    This function is used inside the background scanner and signal engine.
    """
    signals = []

    # Example: Supertrend-based signal (if you have Supertrend logic elsewhere)
    if "Supertrend" in df.columns:
        last = df.iloc[-1]
        prev = df.iloc[-2]
        if last['Close'] > last['Supertrend'] and prev['Close'] <= prev['Supertrend']:
            signals.append({
                "symbol": symbol,
                "type": "BUY",
                "strategy": "Supertrend Bullish Crossover",
                "timeframe": "15m",
                "strength": 90,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    # Example: EMA crossover
    if "EMA_8" in df.columns and "EMA_20" in df.columns:
        if df["EMA_8"].iloc[-1] > df["EMA_20"].iloc[-1] and df["EMA_8"].iloc[-2] <= df["EMA_20"].iloc[-2]:
            signals.append({
                "symbol": symbol,
                "type": "BUY",
                "strategy": "EMA 8/20 Bullish Crossover",
                "timeframe": "15m",
                "strength": 85,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    # Add more rules here (RSI breakout, MACD cross, Pivot Break, etc.)
    
    return signals

def calculate_performance_metrics(signals):
    """
    Calculate simple metrics from a list of signals for summary/statistics.
    You can expand this later for accuracy %, win rate, etc.
    """
    metrics = {
        "total_signals": len(signals),
        "high_confidence_signals": len([s for s in signals if s.get("strength", 0) >= 85]),
        "avg_strength": round(np.mean([s.get("strength", 0) for s in signals]), 2) if signals else 0
    }
    return metrics

def generate_live_option_signals():
    """
    Generate mock option trading signals.
    Replace with real option chain logic later.
    """
    mock_signals = [
        {
            "symbol": "NIFTY24JUL22400CE",
            "type": "CALL",
            "signal": "CALL BUY",
            "reason": ["Open Interest Surge", "Bullish Trend"],
            "confidence": "High",
            "strength": 88,
            "timeframe": "15m",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "symbol": "BANKNIFTY24JUL48500PE",
            "type": "PUT",
            "signal": "PUT BUY",
            "reason": ["IV Spike", "Bearish Reversal"],
            "confidence": "Medium",
            "strength": 80,
            "timeframe": "15m",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    return mock_signals

def generate_live_scalping_signals():
    """
    Generate mock scalping signals for high-frequency trading.
    Replace with real tick/volume breakout logic later.
    """
    mock_scalping = [
        {
            "symbol": "RELIANCE.NS",
            "signal": "Scalp Buy",
            "reason": ["Volume Spike", "VWAP Rebound"],
            "confidence": "High",
            "strength": 90,
            "timeframe": "5m",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "symbol": "TATASTEEL.NS",
            "signal": "Scalp Sell",
            "reason": ["Fast MA Crossover", "Breakdown below VWAP"],
            "confidence": "Medium",
            "strength": 82,
            "timeframe": "5m",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    return mock_scalping
