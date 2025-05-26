
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_indicators(df):
    # EMA
    df['EMA_8'] = df['Close'].ewm(span=8, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # MACD
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ATR (for SL)
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()

    # Supertrend
    factor = 3
    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (factor * df['ATR'])
    df['LowerBand'] = hl2 - (factor * df['ATR'])
    df['Supertrend'] = np.nan
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['UpperBand'].iloc[i-1]:
            df['Supertrend'].iloc[i] = 'buy'
        elif df['Close'].iloc[i] < df['LowerBand'].iloc[i-1]:
            df['Supertrend'].iloc[i] = 'sell'
        else:
            df['Supertrend'].iloc[i] = df['Supertrend'].iloc[i-1]
    return df

def get_pivot_levels(df):
    last_row = df.iloc[-2]
    pp = (last_row['High'] + last_row['Low'] + last_row['Close']) / 3
    r1 = (2 * pp) - last_row['Low']
    s1 = (2 * pp) - last_row['High']
    return pp, r1, s1

def volume_spike(df):
    avg_vol = df['Volume'].rolling(window=10).mean().iloc[-2]
    latest_vol = df['Volume'].iloc[-1]
    return latest_vol > 1.5 * avg_vol

def generate_signal(symbol, interval, period):
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False)
        if df.empty or len(df) < 200:
            return None
        df = calculate_indicators(df)
        pp, r1, s1 = get_pivot_levels(df)
        last = df.iloc[-1]

        if (
            last['Close'] > last['EMA_200'] and
            last['EMA_8'] > last['EMA_20'] and
            last['MACD'] > last['Signal_Line'] and
            55 < last['RSI'] < 70 and
            last['Supertrend'] == 'buy' and
            last['Close'] > r1 and
            volume_spike(df)
        ):
            return {
                'symbol': symbol,
                'type': 'BUY',
                'price': round(last['Close'], 2),
                'target': round(last['Close'] + 2 * df['ATR'].iloc[-1], 2),
                'stop_loss': round(last['Close'] - df['ATR'].iloc[-1], 2),
                'reason': 'MACD+RSI+EMA+Crossover+Pivot+Volume Spike',
                'confidence': 98
            }
        elif (
            last['Close'] < last['EMA_200'] and
            last['EMA_8'] < last['EMA_20'] and
            last['MACD'] < last['Signal_Line'] and
            30 < last['RSI'] < 45 and
            last['Supertrend'] == 'sell' and
            last['Close'] < s1 and
            volume_spike(df)
        ):
            return {
                'symbol': symbol,
                'type': 'SELL',
                'price': round(last['Close'], 2),
                'target': round(last['Close'] - 2 * df['ATR'].iloc[-1], 2),
                'stop_loss': round(last['Close'] + df['ATR'].iloc[-1], 2),
                'reason': 'MACD+RSI+EMA+Breakdown+Pivot+Volume Spike',
                'confidence': 97
            }
    except Exception as e:
        print(f"Error in {symbol}: {e}")
        return None

def scan_symbols(symbols):
    signals = []
    for symbol in symbols:
        for interval, period in [('5m', '2d'), ('15m', '5d'), ('1d', '6mo')]:
            signal = generate_signal(symbol, interval, period)
            if signal:
                signals.append(signal)
                break  # Avoid multiple alerts for same symbol
    return signals
