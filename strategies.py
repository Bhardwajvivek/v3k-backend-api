import pandas as pd
import yfinance as yf
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from datetime import datetime

TIMEFRAMES = {
    '5m': '5m',
    '15m': '15m',
    '1d': '1d',
    '1wk': '1wk',
    '1mo': '1mo'
}

def calculate_indicators(df):
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()

    df['EMA_8'] = EMAIndicator(close, window=8).ema_indicator()
    df['EMA_20'] = EMAIndicator(close, window=20).ema_indicator()
    df['EMA_200'] = EMAIndicator(close, window=200).ema_indicator()

    macd = MACD(close=close)
    df['MACD'] = macd.macd()
    df['MACD_SIGNAL'] = macd.macd_signal()

    rsi = RSIIndicator(close=close)
    df['RSI'] = rsi.rsi()

    atr = AverageTrueRange(high, low, close)
    df['ATR'] = atr.average_true_range()

    return df

def detect_signals(df, symbol, tf):
    signals = []
    if df.empty or len(df) < 200:
        print(f"[{symbol}][{tf}] Not enough data: {len(df)} rows")
        return signals

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if previous['MACD'] < previous['MACD_SIGNAL'] and latest['MACD'] > latest['MACD_SIGNAL']:
        signals.append('MACD Bullish Crossover')

    if latest['RSI'] < 30:
        signals.append('RSI Oversold')
    elif latest['RSI'] > 70:
        signals.append('RSI Overbought')

    if latest['Close'] > latest['EMA_8'] > latest['EMA_20']:
        signals.append('Supertrend Buy Signal')

    recent_high = df['High'][-2:].max()
    if latest['Close'] > recent_high:
        signals.append('Pivot Breakout')

    if latest['EMA_8'] > latest['EMA_20'] > latest['EMA_200']:
        signals.append('MA Crossover Bullish (8 > 20 > 200)')

    if signals:
        print(f"[{symbol}][{tf}] Signals Found: {signals}")
    else:
        print(f"[{symbol}][{tf}] No signals.")
    return signals

def fetch_and_analyze(symbol, interval):
    period = '60d' if interval in ['5m', '15m'] else '365d'
    try:
        print(f"Fetching {symbol} @ {interval}")
        df = yf.download(symbol, interval=interval, period=period, progress=False)
        df = calculate_indicators(df)
        return detect_signals(df, symbol, interval)
    except Exception as e:
        print(f"Error fetching {symbol} @ {interval}: {e}")
        return []

def generate_all_signals():
    result = []
    stock_list = pd.read_csv("nifty.csv")['Symbol'].tolist()

    for symbol in stock_list:
        for tf_name, tf_value in TIMEFRAMES.items():
            signals = fetch_and_analyze(symbol, tf_value)
            if signals:
                result.append({
                    'symbol': symbol,
                    'timeframe': tf_name,
                    'signals': signals,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
    return result
