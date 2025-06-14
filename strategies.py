import yfinance as yf
import pandas as pd
import numpy as np

# Store live signals globally
live_signals = []

def calculate_indicators(df):
    if df.empty or len(df) < 20:
        return df

    df = df.reset_index()
    high = df['High']
    low = df['Low']
    close = df['Close']

    df['EMA_8'] = close.ewm(span=8, adjust=False).mean()
    df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
    df['EMA_200'] = close.ewm(span=200, adjust=False).mean()

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    hl2 = (high + low) / 2
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr_df = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3})
    tr = tr_df.max(axis=1)
    atr = tr.rolling(window=10).mean()
    df['UpperBand'] = hl2 + (3 * atr)
    df['LowerBand'] = hl2 - (3 * atr)

    try:
        supertrend = pd.Series(np.nan, index=df.index, dtype=float)
        trend = pd.Series(False, index=df.index, dtype=bool)

        for i in range(1, len(df)):
            if pd.isna(supertrend.iloc[i - 1]):
                if close.iloc[i] <= df['UpperBand'].iloc[i]:
                    supertrend.iloc[i] = df['UpperBand'].iloc[i]
                    trend.iloc[i] = False
                else:
                    supertrend.iloc[i] = df['LowerBand'].iloc[i]
                    trend.iloc[i] = True
            else:
                if trend.iloc[i - 1]:
                    if close.iloc[i] <= df['LowerBand'].iloc[i]:
                        supertrend.iloc[i] = df['UpperBand'].iloc[i]
                        trend.iloc[i] = False
                    else:
                        supertrend.iloc[i] = df['LowerBand'].iloc[i]
                        trend.iloc[i] = True
                else:
                    if close.iloc[i] >= df['UpperBand'].iloc[i]:
                        supertrend.iloc[i] = df['LowerBand'].iloc[i]
                        trend.iloc[i] = True
                    else:
                        supertrend.iloc[i] = df['UpperBand'].iloc[i]
                        trend.iloc[i] = False

        df['Supertrend'] = trend

    except Exception as e:
        df['Supertrend'] = pd.Series([False] * len(df), index=df.index)

    df['Pivot'] = (high + low + close) / 3

    try:
        if 'Volume' in df.columns:
            volume_ma = df['Volume'].rolling(window=10).mean()
            df['Volume_Spike'] = df['Volume'] > (volume_ma * 1.5)
        else:
            df['Volume_Spike'] = pd.Series([False] * len(df), index=df.index)
    except:
        df['Volume_Spike'] = pd.Series([False] * len(df), index=df.index)

    return df

def generate_signals(df, symbol, timeframe):
    if len(df) < 2:
        return []

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signals = []
    hard_hits = []
    soft_hits = []

    try:
        if latest['MACD'] > latest['Signal_Line'] and previous['MACD'] < previous['Signal_Line']:
            hard_hits.append("MACD")
        if latest['RSI'] > 60 and previous['RSI'] <= 60:
            hard_hits.append("RSI")
        if latest['Supertrend'] and not previous['Supertrend']:
            hard_hits.append("Supertrend")
        if latest['Close'] > latest['Pivot']:
            hard_hits.append("Pivot")
        if latest['Volume_Spike']:
            hard_hits.append("Volume")
        if (latest['Close'] > latest['EMA_200'] and 
            previous['EMA_8'] < previous['EMA_20'] and 
            latest['EMA_8'] > latest['EMA_20']):
            hard_hits.append("EMA Crossover")

        if len(hard_hits) >= 2:
            signals.append({
                "symbol": symbol,
                "strategy": " + ".join(hard_hits),
                "strategyTags": hard_hits,
                "timeframe": timeframe,
                "type": "Intraday" if timeframe in ["5m", "15m"] else "Swing",
                "price": round(latest['Close'], 2),
                "strength": min(100, 80 + len(hard_hits) * 5)
            })

        if latest['MACD'] > previous['MACD'] and latest['MACD'] < latest['Signal_Line']:
            soft_hits.append("MACD Early Reversal")
        if latest['RSI'] > 50 and previous['RSI'] < 50:
            soft_hits.append("RSI Momentum Building")
        if abs(latest['EMA_8'] - latest['EMA_20']) / latest['Close'] < 0.01:
            soft_hits.append("EMA Convergence")
        if latest['Close'] > latest['Pivot'] and not latest['Volume_Spike']:
            soft_hits.append("Above Pivot (Low Volume)")
        if latest['Supertrend'] and not latest['Volume_Spike']:
            soft_hits.append("Supertrend (Weak Volume)")

        if len(soft_hits) >= 2:
            signals.append({
                "symbol": symbol,
                "strategy": " + ".join(soft_hits),
                "strategyTags": soft_hits,
                "timeframe": timeframe,
                "type": "Watchlist",
                "price": round(latest['Close'], 2),
                "strength": 55 + len(soft_hits) * 5
            })

    except:
        pass

    return signals

def scan_symbols(symbols, timeframes):
    global live_signals
    final_signals = []

    for symbol in symbols:
        for tf in timeframes:
            try:
                interval = "5m" if tf == "5m" else "15m" if tf == "15m" else "1d"
                period = "2d" if tf in ["5m", "15m"] else "6mo"
                df = yf.download(symbol, interval=interval, period=period, progress=False)
                if df.empty or len(df) < 20:
                    continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                df = calculate_indicators(df)
                signals = generate_signals(df, symbol, tf)
                if signals:
                    final_signals.extend(signals)
            except:
                continue

    live_signals = final_signals
    return final_signals

def get_signals():
    return live_signals
