import yfinance as yf
import pandas as pd
import numpy as np
import datetime

def detect_momentum_ignition(df, symbol, timeframe):
    signals = []
    if len(df) < 20:
        return signals

    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    df['Volume_Change'] = df['Volume'].pct_change()

    recent = df.iloc[-1]
    previous = df.iloc[-2]

    # Momentum rules
    fast_price_jump = recent['Returns'] > 0.01  # >1% candle
    fast_volume_surge = recent['Volume'] > (df['Volume'].rolling(10).mean().iloc[-1] * 2)
    fast_continuation = previous['Returns'] > 0 and recent['Returns'] > 0

    if fast_price_jump and fast_volume_surge and fast_continuation:
        signals.append({
            "symbol": symbol,
            "strategy": "Momentum Ignition",
            "strategyTags": ["Price Jump", "Volume Surge", "Ignition"],
            "timeframe": timeframe,
            "type": "Intraday",
            "price": round(recent['Close'], 2),
            "strength": 95,
            "reason": "Fast price jump + Volume explosion + Positive continuation"
        })

    return signals

# Optional batch scanner
def scan_momentum_symbols(symbols, timeframe="5m"):
    results = []
    for symbol in symbols:
        try:
            df = yf.download(symbol, period="2d", interval=timeframe, progress=False)
            if df.empty:
                continue
            signal = detect_momentum_ignition(df, symbol, timeframe)
            if signal:
                results.extend(signal)
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
    return results

# Example test
if __name__ == "__main__":
    test_symbols = ["RELIANCE.NS", "TATASTEEL.NS", "BANKBARODA.NS"]
    results = scan_momentum_symbols(test_symbols, timeframe="5m")
    for r in results:
        print(r)
