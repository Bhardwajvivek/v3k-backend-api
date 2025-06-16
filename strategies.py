import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import json
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# Global live signal store
live_signals = []

TELEGRAM_TOKEN = "7685961335:AAGwpUiRpKpIpUZh3w1PQVWElFO0fIYyHEs"
TELEGRAM_CHAT_ID = "6955435826"

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
    """Calculate technical indicators for the dataframe"""
    try:
        # EMA calculations
        df['EMA_8'] = df['Close'].ewm(span=8).mean()
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        df['EMA_200'] = df['Close'].ewm(span=200).mean()
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD calculation
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['Signal_Line'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
        
        # Bollinger Bands
        bb_period = 20
        df['BB_Middle'] = df['Close'].rolling(window=bb_period).mean()
        bb_std = df['Close'].rolling(window=bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100
        
        # Volume indicators
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        df['Volume_Spike'] = df['Volume_Ratio'] > 2.0
        df['Volume_Trend'] = df['Volume_Ratio'] > 1.5
        
        # Supertrend (simplified)
        hl2 = (df['High'] + df['Low']) / 2
        atr = df[['High', 'Low', 'Close']].apply(lambda x: max(x['High'] - x['Low'], 
                                                              abs(x['High'] - x['Close']), 
                                                              abs(x['Low'] - x['Close'])), axis=1).rolling(10).mean()
        upperband = hl2 + (3 * atr)
        lowerband = hl2 - (3 * atr)
        df['Supertrend'] = df['Close'] > lowerband
        
        # Pivot Points (simplified)
        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = 2 * df['Pivot'] - df['Low']
        df['S1'] = 2 * df['Pivot'] - df['High']
        
        # Pattern recognition (simplified)
        df['Hammer'] = ((df['Close'] - df['Low']) > 2 * (df['High'] - df['Close'])) & \
                       ((df['High'] - df['Close']) < 0.1 * (df['Close'] - df['Low']))
        
        # Trend strength
        df['Trend_Strength'] = np.where(
            (df['EMA_8'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50']), 1, 0
        )
        
        return df
        
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return df

def calculate_signal_strength(hard_hits, soft_hits, market_conditions=None):
    base_strength = 40
    strength = base_strength + (len(hard_hits) * 15) + (len(soft_hits) * 5)

    if 'MACD' in hard_hits and 'RSI' in hard_hits:
        strength += 10
    if 'Volume' in hard_hits and 'Supertrend' in hard_hits:
        strength += 8
    if 'EMA Crossover' in hard_hits:
        strength += 12

    return min(100, strength)

def generate_enhanced_signals(df, symbol, timeframe):
    if len(df) < 5:
        return []

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signals = []
    hard_hits = []
    soft_hits = []
    signal_metadata = {}

    try:
        if latest['MACD'] > latest['Signal_Line']:
            if previous['MACD'] <= previous['Signal_Line']:
                hard_hits.append("MACD Bullish Cross")
                signal_metadata['macd_cross'] = True
            elif latest['MACD_Histogram'] > previous['MACD_Histogram']:
                soft_hits.append("MACD Momentum")

        if latest['RSI'] > 60:
            hard_hits.append("RSI Strong")
        elif latest['RSI'] > 55:
            soft_hits.append("RSI Bullish")
        elif latest['RSI'] > 50 and latest['RSI'] > previous['RSI']:
            soft_hits.append("RSI Rising")

        if latest['Supertrend']:
            if not previous['Supertrend']:
                hard_hits.append("Supertrend Reversal")
                signal_metadata['trend_reversal'] = True
            else:
                soft_hits.append("Supertrend Bullish")

        if latest['EMA_8'] > latest['EMA_20']:
            if previous['EMA_8'] <= previous['EMA_20']:
                hard_hits.append("EMA Golden Cross")
                signal_metadata['ema_cross'] = True
            else:
                soft_hits.append("EMA Bullish Alignment")

        if latest['EMA_20'] > latest['EMA_50'] > latest['EMA_200']:
            soft_hits.append("Long-term Bullish")

        if latest['Volume_Spike']:
            hard_hits.append("Volume Breakout")
            signal_metadata['volume_spike'] = round(float(latest['Volume_Ratio']), 2)
        elif latest['Volume_Trend']:
            soft_hits.append("Volume Trend")

        if latest['Close'] > latest['BB_Upper']:
            soft_hits.append("BB Breakout")
        elif latest['Close'] > latest['BB_Middle'] and latest['BB_Width'] < 10:
            soft_hits.append("BB Squeeze")

        if latest['Close'] > latest['R1']:
            soft_hits.append("Above R1")
        elif latest['Close'] > latest['Pivot']:
            soft_hits.append("Above Pivot")

        if latest['Hammer']:
            soft_hits.append("Hammer Pattern")
        elif latest['Trend_Strength'] == 1:
            soft_hits.append("Strong Uptrend")

        strength = calculate_signal_strength(hard_hits, soft_hits)

        if len(hard_hits) >= 2 or (len(hard_hits) >= 1 and len(soft_hits) >= 2):
            signal_type = "Strong Buy"
            min_strength = 75
        elif len(hard_hits) >= 1 or len(soft_hits) >= 3:
            signal_type = "Buy"
            min_strength = 60
        elif len(soft_hits) >= 2:
            signal_type = "Watchlist"
            min_strength = 45
        else:
            return []

        if strength >= min_strength:
            sparkline_data = df['Close'].tail(20).tolist() if len(df) >= 20 else df['Close'].tolist()
            price_change = latest['Close'] - previous['Close']
            change_percent = (price_change / previous['Close']) * 100

            signal = {
                "symbol": symbol,
                "strategy": " + ".join((hard_hits + soft_hits)[:3]),
                "strategyTags": hard_hits + soft_hits,
                "timeframe": timeframe,
                "type": "Intraday" if timeframe in ["5m", "15m"] else "Swing" if timeframe == "1d" else "Position",
                "signalType": signal_type,
                "price": round(float(latest['Close']), 2),
                "change": round(price_change, 2),
                "changePercent": round(change_percent, 2),
                "volume": int(latest.get('Volume', 0)),
                "strength": strength,
                "sparkline": sparkline_data,
                "metadata": signal_metadata,
                "indicators": {
                    "rsi": round(latest['RSI'], 2),
                    "macd": round(latest['MACD'], 4),
                    "ema_8": round(latest['EMA_8'], 2),
                    "ema_20": round(latest['EMA_20'], 2),
                    "supertrend": bool(latest['Supertrend']),
                    "volume_ratio": round(latest['Volume_Ratio'], 2)
                },
                "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S') if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
            }

            signals.append(json.loads(json.dumps(signal)))

    except Exception as e:
        print(f"❌ Enhanced signal error for {symbol} ({timeframe}):", e)

    return signals

def scan_symbols_enhanced(symbols, timeframes):
    """Actually scan symbols and generate signals"""
    global live_signals
    live_signals = []  # Clear previous signals
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                # Download data
                if timeframe == "1d":
                    period = "6mo"
                    interval = "1d"
                elif timeframe == "1h":
                    period = "1mo"
                    interval = "1h"
                else:
                    period = "5d"
                    interval = timeframe
                
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if df.empty or len(df) < 20:
                    continue
                
                # Calculate indicators
                df = calculate_indicators(df)
                
                # Generate signals
                signals = generate_enhanced_signals(df, symbol, timeframe)
                live_signals.extend(signals)
                
            except Exception as e:
                print(f"Error scanning {symbol} ({timeframe}): {e}")
                continue
    
    return live_signals

def get_signals():
    """Return current live signals"""
    return live_signals

def filter_signals(min_strength=60, signal_types=None, timeframes=None, symbols=None):
    """Filter signals based on criteria"""
    filtered = live_signals
    
    # Filter by strength
    filtered = [s for s in filtered if s.get('strength', 0) >= min_strength]
    
    # Filter by signal types
    if signal_types:
        filtered = [s for s in filtered if s.get('signalType') in signal_types]
    
    # Filter by timeframes
    if timeframes:
        filtered = [s for s in filtered if s.get('timeframe') in timeframes]
    
    # Filter by symbols
    if symbols:
        filtered = [s for s in filtered if s.get('symbol') in symbols]
    
    return filtered

def get_signal_analytics():
    """Return analytics about current signals"""
    if not live_signals:
        return {
            "total_signals": 0,
            "by_strength": {},
            "by_type": {},
            "by_timeframe": {},
            "avg_strength": 0
        }
    
    analytics = {
        "total_signals": len(live_signals),
        "by_strength": {},
        "by_type": {},
        "by_timeframe": {},
        "avg_strength": sum(s.get('strength', 0) for s in live_signals) / len(live_signals)
    }
    
    # Group by strength ranges
    for signal in live_signals:
        strength = signal.get('strength', 0)
        if strength >= 80:
            key = "80+"
        elif strength >= 70:
            key = "70-79"
        elif strength >= 60:
            key = "60-69"
        else:
            key = "50-59"
        analytics["by_strength"][key] = analytics["by_strength"].get(key, 0) + 1
    
    # Group by signal type
    for signal in live_signals:
        sig_type = signal.get('signalType', 'Unknown')
        analytics["by_type"][sig_type] = analytics["by_type"].get(sig_type, 0) + 1
    
    # Group by timeframe
    for signal in live_signals:
        timeframe = signal.get('timeframe', 'Unknown')
        analytics["by_timeframe"][timeframe] = analytics["by_timeframe"].get(timeframe, 0) + 1
    
    return analytics