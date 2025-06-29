# Enhanced Pro Trading Strategies - V3K AI Trading Bot
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import json
import time
from datetime import datetime, timedelta
import ta  # Technical Analysis library
import scipy.stats as stats

from types import SimpleNamespace

# Global scan state and cache
bot_state = SimpleNamespace(
    scan_status="idle",
    last_scan_time=None,
    cached_signals=[],
    cached_options=[],
    cached_scalping=[],
    performance_metrics={}
)


# Make sklearn optional to avoid import errors
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
    print("✅ Sklearn available - ML features enabled")
except ImportError:
    print("⚠️ Sklearn not available - ML features disabled")
    SKLEARN_AVAILABLE = False
    # Create dummy classes as fallback
    class LinearRegression:
        def __init__(self):
            pass
        def fit(self, X, y):
            return self
        def predict(self, X):
            return np.zeros(len(X))
    
    class StandardScaler:
        def __init__(self):
            pass
        def fit(self, X):
            return self
        def transform(self, X):
            return X
        def fit_transform(self, X):
            return X

warnings.filterwarnings('ignore')

# Global live signal store
live_signals = []
backtesting_results = {}
strategy_performance = {}

TELEGRAM_TOKEN = "7685961335:AAGwpUiRpKpIpUZh3w1PQVWElFO0fIYyHEs"
TELEGRAM_CHAT_ID = "6955435826"

def calculate_advanced_indicators(df):
    """Calculate comprehensive technical indicators"""
    try:
        # === TREND INDICATORS ===
        df['EMA_8'] = ta.trend.EMAIndicator(df['Close'], window=8).ema_indicator()
        df['EMA_20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
        df['EMA_50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
        
        # Supertrend
        hl2 = (df['High'] + df['Low']) / 2
        atr = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=10).average_true_range()
        df['ATR'] = atr
        df['Supertrend_Upper'] = hl2 + (3 * atr)
        df['Supertrend_Lower'] = hl2 - (3 * atr)
        df['Supertrend'] = np.where(df['Close'] > df['Supertrend_Lower'], 1, 0)
        
        # Ichimoku Cloud
        df['Ichimoku_A'] = ((df['High'].rolling(9).max() + df['Low'].rolling(9).min()) / 2).shift(26)
        df['Ichimoku_B'] = ((df['High'].rolling(26).max() + df['Low'].rolling(26).min()) / 2).shift(26)
        df['Cloud_Green'] = df['Ichimoku_A'] > df['Ichimoku_B']
        
        # === MOMENTUM INDICATORS ===
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['RSI_MA'] = df['RSI'].rolling(window=5).mean()
        df['RSI_Divergence'] = calculate_divergence(df['Close'], df['RSI'])
        
        # MACD with histogram
        macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Histogram'] = macd.macd_diff()
        df['MACD_Zero_Cross'] = (df['MACD'] > 0) & (df['MACD'].shift(1) <= 0)
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        # Williams %R
        df['Williams_R'] = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close']).williams_r()
        
        # === VOLATILITY INDICATORS ===
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Keltner Channels
        kc = ta.volatility.KeltnerChannel(df['High'], df['Low'], df['Close'])
        df['KC_Upper'] = kc.keltner_channel_hband()
        df['KC_Lower'] = kc.keltner_channel_lband()
        df['Squeeze'] = (df['BB_Upper'] < df['KC_Upper']) & (df['BB_Lower'] > df['KC_Lower'])
        
        # === VOLUME INDICATORS ===
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        df['Volume_Spike'] = df['Volume_Ratio'] > 2.0
        df['Volume_Trend'] = df['Volume_Ratio'] > 1.5
        
        # Volume Profile approximation
        df['VWAP'] = ta.volume.VolumePriceTrendIndicator(df['High'], df['Low'], df['Close'], df['Volume']).volume_price_trend()
        df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
        df['CMF'] = ta.volume.ChaikinMoneyFlowIndicator(df['High'], df['Low'], df['Close'], df['Volume']).chaikin_money_flow()
        
        # === SUPPORT/RESISTANCE ===
        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['R1'] = 2 * df['Pivot'] - df['Low']
        df['R2'] = df['Pivot'] + (df['High'] - df['Low'])
        df['S1'] = 2 * df['Pivot'] - df['High']
        df['S2'] = df['Pivot'] - (df['High'] - df['Low'])
        
        # Dynamic Support/Resistance
        df['Support_Level'] = calculate_support_resistance(df, 'support')
        df['Resistance_Level'] = calculate_support_resistance(df, 'resistance')
        
        # === PATTERN RECOGNITION ===
        df['Hammer'] = detect_hammer(df)
        df['Doji'] = detect_doji(df)
        df['Engulfing'] = detect_engulfing(df)
        df['Morning_Star'] = detect_morning_star(df)
        df['Evening_Star'] = detect_evening_star(df)
        
        # === MARKET STRUCTURE ===
        df['Higher_High'] = (df['High'] > df['High'].shift(1)) & (df['High'].shift(1) > df['High'].shift(2))
        df['Higher_Low'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2))
        df['Lower_High'] = (df['High'] < df['High'].shift(1)) & (df['High'].shift(1) < df['High'].shift(2))
        df['Lower_Low'] = (df['Low'] < df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'].shift(2))
        
        # Trend Strength
        df['Trend_Strength'] = calculate_trend_strength(df)
        df['Momentum_Score'] = calculate_momentum_score(df)
        
        # === MACHINE LEARNING FEATURES ===
        df['Price_ROC'] = df['Close'].pct_change(periods=5) * 100
        df['Volume_ROC'] = df['Volume'].pct_change(periods=5) * 100
        df['Volatility'] = df['Close'].rolling(window=20).std()
        df['ML_Signal'] = generate_ml_signal(df)
        
        return df
        
    except Exception as e:
        print(f"Error calculating advanced indicators: {e}")
        return df

def calculate_divergence(price, indicator, lookback=5):
    """Calculate bullish/bearish divergence"""
    try:
        price_peaks = []
        indicator_peaks = []
        
        for i in range(lookback, len(price) - lookback):
            if price.iloc[i] == price.iloc[i-lookback:i+lookback+1].max():
                price_peaks.append((i, price.iloc[i]))
            if indicator.iloc[i] == indicator.iloc[i-lookback:i+lookback+1].max():
                indicator_peaks.append((i, indicator.iloc[i]))
        
        # Check for divergence in last few peaks
        divergence = np.zeros(len(price))
        if len(price_peaks) >= 2 and len(indicator_peaks) >= 2:
            last_price_peak = price_peaks[-1]
            prev_price_peak = price_peaks[-2]
            last_ind_peak = indicator_peaks[-1]
            prev_ind_peak = indicator_peaks[-2]
            
            # Bearish divergence: price higher, indicator lower
            if (last_price_peak[1] > prev_price_peak[1] and 
                last_ind_peak[1] < prev_ind_peak[1]):
                divergence[last_price_peak[0]] = -1
            
            # Bullish divergence: price lower, indicator higher
            elif (last_price_peak[1] < prev_price_peak[1] and 
                  last_ind_peak[1] > prev_ind_peak[1]):
                divergence[last_price_peak[0]] = 1
        
        return divergence
    except:
        return np.zeros(len(price))

# Add this function to your strategies.py
def ensure_complete_trading_levels(signal_data, entry_price):
    """Ensure all trading levels are populated with realistic values"""
    try:
        entry = float(entry_price) if entry_price else 1000.0
        
        # Calculate percentage-based levels if missing
        levels = {
            'entry': entry,
            'target1': signal_data.get('exit') or signal_data.get('target1') or (entry * 1.02),
            'target2': signal_data.get('target2') or (entry * 1.04),
            'target3': signal_data.get('target3') or (entry * 1.06),
            'exit': signal_data.get('exit') or (entry * 1.02),  # For compatibility
            'stoploss': signal_data.get('stoploss') or (entry * 0.98),
            'trailingSL': signal_data.get('trailingSL') or (entry * 0.985),
            'riskReward': signal_data.get('riskReward') or 2.0
        }
        
        # Round all values to 2 decimal places
        for key, value in levels.items():
            if key != 'riskReward':
                levels[key] = round(float(value), 2)
            else:
                levels[key] = round(float(value), 2)
        
        return levels
        
    except Exception as e:
        print(f"Error ensuring trading levels: {e}")
        # Return safe defaults
        entry = 1000.0
        return {
            'entry': entry,
            'target1': round(entry * 1.02, 2),
            'target2': round(entry * 1.04, 2),
            'target3': round(entry * 1.06, 2),
            'exit': round(entry * 1.02, 2),
            'stoploss': round(entry * 0.98, 2),
            'trailingSL': round(entry * 0.985, 2),
            'riskReward': 2.0
        }

# Update your signal generation to use this
def generate_professional_signals(df, symbol, timeframe):
    """Generate signals with guaranteed price levels"""
    # Your existing signal logic...
    
    if len(hard_hits) >= 1 or len(soft_hits) >= 3:
        entry_price = latest['Close']
        
        # Create base signal
        signal_base = {
            "symbol": symbol,
            "strategy": " + ".join((hard_hits + soft_hits)[:4]),
            "strategyTags": hard_hits + soft_hits,
            "timeframe": timeframe,
            "type": determine_signal_category(timeframe, latest),
            "signalType": signal_type,
            "price": round(float(latest['Close']), 2),
            "strength": strength,
            "confidence": calculate_confidence_score(latest, hard_hits, soft_hits),
            # Add basic levels first
            "entry": round(float(entry_price), 2),
            "exit": round(float(entry_price * 1.02), 2),
            "stoploss": round(float(entry_price * 0.98), 2),
        }
        
        # Ensure ALL trading levels are populated
        complete_levels = ensure_complete_trading_levels(signal_base, entry_price)
        signal_base.update(complete_levels)
        
        signals.append(signal_base)
        
    return signals

def calculate_support_resistance(df, level_type='support', window=20):
    """Calculate dynamic support/resistance levels"""
    try:
        if level_type == 'support':
            levels = df['Low'].rolling(window=window).min()
        else:
            levels = df['High'].rolling(window=window).max()
        return levels
    except:
        return df['Close'] * 0.95 if level_type == 'support' else df['Close'] * 1.05

def detect_hammer(df):
    """Detect hammer candlestick pattern"""
    try:
        body = abs(df['Close'] - df['Open'])
        lower_shadow = df['Open'].min(df['Close']) - df['Low']
        upper_shadow = df['High'] - df['Open'].max(df['Close'])
        
        hammer = (lower_shadow > 2 * body) & (upper_shadow < 0.5 * body) & (body > 0)
        return hammer.astype(int)
    except:
        return pd.Series(0, index=df.index)

def detect_doji(df):
    """Detect doji candlestick pattern"""
    try:
        body_size = abs(df['Close'] - df['Open'])
        candle_range = df['High'] - df['Low']
        doji = body_size <= (candle_range * 0.1)
        return doji.astype(int)
    except:
        return pd.Series(0, index=df.index)

def detect_engulfing(df):
    """Detect bullish/bearish engulfing pattern"""
    try:
        current_body = abs(df['Close'] - df['Open'])
        prev_body = abs(df['Close'].shift(1) - df['Open'].shift(1))
        
        bullish_engulfing = (
            (df['Close'].shift(1) < df['Open'].shift(1)) &  # Previous red candle
            (df['Close'] > df['Open']) &  # Current green candle
            (df['Open'] < df['Close'].shift(1)) &  # Opens below prev close
            (df['Close'] > df['Open'].shift(1)) &  # Closes above prev open
            (current_body > prev_body)  # Larger body
        )
        
        return bullish_engulfing.astype(int)
    except:
        return pd.Series(0, index=df.index)

def detect_morning_star(df):
    """Detect morning star pattern"""
    try:
        # Three candle pattern
        first_red = (df['Close'].shift(2) < df['Open'].shift(2))
        small_body = abs(df['Close'].shift(1) - df['Open'].shift(1)) < abs(df['Close'].shift(2) - df['Open'].shift(2)) * 0.3
        third_green = (df['Close'] > df['Open']) & (df['Close'] > (df['Open'].shift(2) + df['Close'].shift(2)) / 2)
        
        morning_star = first_red & small_body & third_green
        return morning_star.astype(int)
    except:
        return pd.Series(0, index=df.index)

def detect_evening_star(df):
    """Detect evening star pattern"""
    try:
        first_green = (df['Close'].shift(2) > df['Open'].shift(2))
        small_body = abs(df['Close'].shift(1) - df['Open'].shift(1)) < abs(df['Close'].shift(2) - df['Open'].shift(2)) * 0.3
        third_red = (df['Close'] < df['Open']) & (df['Close'] < (df['Open'].shift(2) + df['Close'].shift(2)) / 2)
        
        evening_star = first_green & small_body & third_red
        return evening_star.astype(int)
    except:
        return pd.Series(0, index=df.index)

def calculate_trend_strength(df):
    """Calculate trend strength using multiple factors"""
    try:
        ema_alignment = (
            (df['EMA_8'] > df['EMA_20']).astype(int) +
            (df['EMA_20'] > df['EMA_50']).astype(int) +
            (df['EMA_50'] > df['EMA_200']).astype(int)
        ) / 3
        
        price_position = (df['Close'] - df['Close'].rolling(20).min()) / (df['Close'].rolling(20).max() - df['Close'].rolling(20).min())
        
        trend_strength = (ema_alignment + price_position) / 2
        return trend_strength.fillna(0.5)
    except:
        return pd.Series(0.5, index=df.index)

def calculate_momentum_score(df):
    """Calculate momentum score using multiple indicators"""
    try:
        rsi_score = (df['RSI'] - 50) / 50  # Normalize RSI
        macd_score = np.where(df['MACD'] > df['MACD_Signal'], 1, -1)
        stoch_score = (df['Stoch_K'] - 50) / 50
        
        momentum_score = (rsi_score + macd_score + stoch_score) / 3
        return momentum_score.fillna(0)
    except:
        return pd.Series(0, index=df.index)

def generate_ml_signal(df):
    """Generate ML-based signal using price patterns"""
    try:
        if not SKLEARN_AVAILABLE or len(df) < 50:
            return pd.Series(0, index=df.index)
        
        # Prepare features only if sklearn is available
        features = ['RSI', 'MACD', 'BB_Position', 'Volume_Ratio', 'Trend_Strength']
        feature_data = df[features].fillna(0)
        
        # Simple signal based on feature combination
        signal_strength = (
            (feature_data['RSI'] > 60).astype(int) +
            (feature_data['MACD'] > 0).astype(int) +
            (feature_data['BB_Position'] > 0.8).astype(int) +
            (feature_data['Volume_Ratio'] > 1.5).astype(int) +
            (feature_data['Trend_Strength'] > 0.7).astype(int)
        ) / 5
        
        return signal_strength
    except Exception as e:
        print(f"ML signal error: {e}")
        return pd.Series(0, index=df.index)
    
    #def scan_all_signal_types(equity_symbols, option_underlyings, scalping_symbols, timeframes):
    #"""Comprehensive scanning for all signal types"""
    #all_signals = []
    
    #try:
        # 1. Equity signals
        #equity_signals = scan_symbols_enhanced(equity_symbols, timeframes)
        #for signal in equity_signals:
            #signal['type'] = 'equity'
        #all_signals.extend(equity_signals)
        
        # 2. Option signals
        #option_signals = generate_option_signals(option_underlyings)
        #all_signals.extend(option_signals)
        
        # 3. Scalping signals (faster timeframes)
        #scalping_timeframes = ['1m', '3m', '5m']
        #scalping_signals = generate_scalping_signals(scalping_symbols, scalping_timeframes)
        #all_signals.extend(scalping_signals)
        
        #print(f"📊 Generated: {len(equity_signals)} equity, {len(option_signals)} option, {len(scalping_signals)} scalping signals")
        
    #except Exception as e:
        #print(f"Error in comprehensive scanning: {e}")
    
    #return all_signals
    
def calculate_advanced_signal_strength(hard_hits, soft_hits, df, market_conditions=None):
    """Enhanced signal strength calculation"""
    base_strength = 35
    
    # Base scoring
    strength = base_strength + (len(hard_hits) * 12) + (len(soft_hits) * 4)
    
    # Confluence bonuses
    if 'MACD' in hard_hits and 'RSI' in hard_hits:
        strength += 15
    if 'Volume' in hard_hits and 'Supertrend' in hard_hits:
        strength += 12
    if 'EMA Crossover' in hard_hits:
        strength += 18
    if 'Pattern' in hard_hits:
        strength += 10
    
    # Technical factor bonuses
    latest = df.iloc[-1]
    
    # Trend alignment bonus
    if latest.get('Trend_Strength', 0) > 0.8:
        strength += 8
    
    # Volume confirmation
    if latest.get('Volume_Ratio', 1) > 2.5:
        strength += 10
    elif latest.get('Volume_Ratio', 1) > 1.8:
        strength += 5
    
    # Momentum alignment
    if latest.get('Momentum_Score', 0) > 0.7:
        strength += 8
    
    # Volatility consideration
    if latest.get('BB_Width', 10) < 5:  # Low volatility
        strength += 5
    elif latest.get('BB_Width', 10) > 20:  # High volatility
        strength -= 3
    
    # Market structure bonus
    if latest.get('Higher_High', False) and latest.get('Higher_Low', False):
        strength += 6
    
    # Pattern recognition bonus
    pattern_bonus = (
        latest.get('Hammer', 0) * 5 +
        latest.get('Morning_Star', 0) * 8 +
        latest.get('Engulfing', 0) * 6
    )
    strength += pattern_bonus
    
    # Divergence penalty/bonus
    if latest.get('RSI_Divergence', 0) < 0:  # Bearish divergence
        strength -= 10
    elif latest.get('RSI_Divergence', 0) > 0:  # Bullish divergence
        strength += 12
    
    return min(100, max(0, strength))

def calculate_trading_levels(entry_price, atr, timeframe, signal_type="Buy"):
    """Calculate comprehensive trading levels with multiple targets and trailing SL"""
    try:
        entry = float(entry_price)
        atr = float(atr) if atr else entry * 0.02  # Default 2% if no ATR
        
        # Timeframe-based multipliers
        if timeframe in ['1m', '3m', '5m']:  # Scalping
            target_multiplier = 1.0
            stop_multiplier = 0.8
        elif timeframe in ['15m', '30m', '1h']:  # Intraday  
            target_multiplier = 1.5
            stop_multiplier = 1.0
        else:  # Swing/Position
            target_multiplier = 2.0
            stop_multiplier = 1.2
        
        # Calculate levels based on signal strength
        if signal_type == "Strong Buy":
            # More aggressive targets for strong signals
            target1 = entry + (atr * target_multiplier * 1.5)
            target2 = entry + (atr * target_multiplier * 2.5) 
            target3 = entry + (atr * target_multiplier * 4.0)
            stop_loss = entry - (atr * stop_multiplier * 1.2)
            trailing_sl = entry - (atr * stop_multiplier * 0.8)
        elif signal_type == "Buy":
            # Standard targets
            target1 = entry + (atr * target_multiplier * 1.0)
            target2 = entry + (atr * target_multiplier * 2.0)
            target3 = entry + (atr * target_multiplier * 3.0)
            stop_loss = entry - (atr * stop_multiplier * 1.0)
            trailing_sl = entry - (atr * stop_multiplier * 0.7)
        else:  # Quick Buy / Scalping
            # Conservative targets
            target1 = entry + (atr * target_multiplier * 0.8)
            target2 = entry + (atr * target_multiplier * 1.5)
            target3 = entry + (atr * target_multiplier * 2.5)
            stop_loss = entry - (atr * stop_multiplier * 0.8)
            trailing_sl = entry - (atr * stop_multiplier * 0.6)
        
        # Calculate Risk:Reward ratio
        risk = abs(entry - stop_loss)
        reward = abs(target1 - entry)
        risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
        
        return {
            'entry': round(entry, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2), 
            'target3': round(target3, 2),
            'exit': round(target1, 2),  # For backward compatibility
            'stoploss': round(stop_loss, 2),
            'trailingSL': round(trailing_sl, 2),
            'riskReward': risk_reward
        }
        
    except Exception as e:
        print(f"Error calculating trading levels: {e}")
        # Return safe defaults
        entry = float(entry_price) if entry_price else 1000
        return {
            'entry': round(entry, 2),
            'target1': round(entry * 1.02, 2),
            'target2': round(entry * 1.04, 2),
            'target3': round(entry * 1.06, 2),
            'exit': round(entry * 1.02, 2),
            'stoploss': round(entry * 0.98, 2),
            'trailingSL': round(entry * 0.985, 2),
            'riskReward': 2.0
        }

def generate_professional_signals(df, symbol, timeframe):
    """Generate institutional-grade trading signals with complete price levels"""
    if len(df) < 50:
        return []

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    
    signals = []
    hard_hits = []
    soft_hits = []
    signal_metadata = {}
    
    try:
        # Your existing signal logic here...
        # (Keep all your current MACD, RSI, EMA, Volume analysis)
        
        # After determining signal type and strength...
        if len(hard_hits) >= 1 or len(soft_hits) >= 3:  # If we have a valid signal
            
            # Determine signal type
            if len(hard_hits) >= 3:
                signal_type = "Strong Buy"
            elif len(hard_hits) >= 2:
                signal_type = "Buy"  
            else:
                signal_type = "Quick Buy"
            
            # Calculate entry price
            entry_price = latest['Close']
            
            # Get ATR for calculations
            atr = latest.get('ATR', latest['Close'] * 0.02)
            
            # Calculate ALL trading levels
            trading_levels = calculate_trading_levels(entry_price, atr, timeframe, signal_type)
            
            # Calculate strength (your existing logic)
            strength = calculate_advanced_signal_strength(hard_hits, soft_hits, df)
            
            # Only generate signal if meets minimum criteria
            min_strength = 78 if signal_type == "Strong Buy" else 65 if signal_type == "Buy" else 50
            
            if strength >= min_strength:
                signal = {
                    "symbol": symbol,
                    "strategy": " + ".join((hard_hits + soft_hits)[:4]),
                    "strategyTags": hard_hits + soft_hits,
                    "timeframe": timeframe,
                    "type": determine_signal_category(timeframe, latest),
                    "signalType": signal_type,
                    "price": round(float(latest['Close']), 2),
                    "change": round(float(latest['Close'] - previous['Close']), 2),
                    "changePercent": round(float((latest['Close'] - previous['Close']) / previous['Close'] * 100), 2),
                    "volume": int(latest.get('Volume', 0)),
                    "strength": strength,
                    "confidence": calculate_confidence_score(latest, hard_hits, soft_hits),
                    
                    # ALL TRADING LEVELS - COMPLETE
                    "entry": trading_levels['entry'],
                    "exit": trading_levels['exit'],           # Target 1 (for compatibility)
                    "target1": trading_levels['target1'],     # Target 1
                    "target2": trading_levels['target2'],     # Target 2  
                    "target3": trading_levels['target3'],     # Target 3
                    "stoploss": trading_levels['stoploss'],   # Stop Loss
                    "trailingSL": trading_levels['trailingSL'], # Trailing Stop Loss
                    "riskReward": trading_levels['riskReward'], # Risk:Reward Ratio
                    
                    # Additional data
                    "indicators": {
                        "rsi": round(latest['RSI'], 2),
                        "macd": round(latest['MACD'], 4),
                        "signal_line": round(latest['MACD_Signal'], 4),
                        "ema_8": round(latest['EMA_8'], 2),
                        "ema_20": round(latest['EMA_20'], 2),
                        "supertrend": bool(latest['Supertrend']),
                        "volume_ratio": round(latest.get('Volume_Ratio', 1), 2),
                        "atr": round(atr, 2)
                    },
                    "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S') if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
                }
                
                signals.append(signal)
                
    except Exception as e:
        print(f"❌ Professional signal error for {symbol} ({timeframe}):", e)
    
    return signals

def determine_signal_category(timeframe, latest_data):
    """Determine if signal is equity, option, or scalping"""
    if timeframe in ['1m', '3m', '5m']:
        return "scalping"
    elif latest_data.get('Volume_Ratio', 1) > 3 and timeframe in ['15m', '30m']:
        return "option"  # High volume short-term could be options
    else:
        return "equity"

def calculate_confidence_score(latest_data, hard_hits, soft_hits):
    """Calculate confidence score for the signal"""
    base_confidence = 60
    
    # Technical confluence
    confidence = base_confidence + (len(hard_hits) * 8) + (len(soft_hits) * 3)
    
    # Volume confirmation
    volume_ratio = latest_data.get('Volume_Ratio', 1)
    if volume_ratio > 2:
        confidence += 10
    elif volume_ratio > 1.5:
        confidence += 5
    
    # Trend strength
    trend_strength = latest_data.get('Trend_Strength', 0.5)
    confidence += int(trend_strength * 15)
    
    # Volatility consideration (prefer medium volatility)
    bb_width = latest_data.get('BB_Width', 10)
    if 8 <= bb_width <= 15:  # Optimal range
        confidence += 5
    elif bb_width < 5 or bb_width > 25:
        confidence -= 3
    
    return min(95, max(40, confidence))

def scan_symbols_enhanced(symbols, timeframes):
    """Enhanced symbol scanning with professional strategies"""
    global live_signals
    live_signals = []
    
    total_symbols = len(symbols) * len(timeframes)
    processed = 0
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                processed += 1
                print(f"🔍 Scanning {symbol} ({timeframe}) - {processed}/{total_symbols}")
                
                # Determine data period and interval
                if timeframe == "1d":
                    period = "1y"
                    interval = "1d"
                elif timeframe == "1h":
                    period = "2mo"
                    interval = "1h"
                elif timeframe == "30m":
                    period = "1mo"
                    interval = "30m"
                elif timeframe == "15m":
                    period = "10d"
                    interval = "15m"
                elif timeframe == "5m":
                    period = "5d"
                    interval = "5m"
                elif timeframe == "3m":
                    period = "2d"
                    interval = "3m"
                else:  # 1m
                    period = "1d"
                    interval = "1m"
                
                # Download data
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if df.empty or len(df) < 50:
                    print(f"⚠️ Insufficient data for {symbol} ({timeframe})")
                    continue
                
                # Calculate advanced indicators
                df = calculate_advanced_indicators(df)
                
                # Generate professional signals
                signals = generate_professional_signals(df, symbol, timeframe)
                live_signals.extend(signals)
                
                if signals:
                    print(f"✅ Found {len(signals)} signals for {symbol} ({timeframe})")
                
            except Exception as e:
                print(f"❌ Error scanning {symbol} ({timeframe}): {e}")
                continue
    
    # Sort signals by strength
    live_signals.sort(key=lambda x: x.get('strength', 0), reverse=True)
    
    print(f"🎯 Total signals generated: {len(live_signals)}")
    return live_signals

def get_signals():
    """Return current live signals"""
    return live_signals

def filter_signals_advanced(min_strength=60, signal_types=None, timeframes=None, 
                           symbols=None, min_confidence=None, categories=None):
    """Advanced signal filtering with multiple criteria"""
    filtered = live_signals.copy()
    
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
    
    # Filter by confidence
    if min_confidence:
        filtered = [s for s in filtered if s.get('confidence', 0) >= min_confidence]
    
    # Filter by categories (equity, option, scalping)
    if categories:
        filtered = [s for s in filtered if s.get('type') in categories]
    
    return filtered

def get_advanced_analytics():
    """Comprehensive signal analytics"""
    if not live_signals:
        return {
            "total_signals": 0,
            "performance_metrics": {},
            "risk_analysis": {},
            "market_outlook": "Neutral"
        }
    
    analytics = {
        "total_signals": len(live_signals),
        "by_strength": {},
        "by_type": {},
        "by_timeframe": {},
        "by_category": {},
        "avg_strength": sum(s.get('strength', 0) for s in live_signals) / len(live_signals),
        "avg_confidence": sum(s.get('confidence', 0) for s in live_signals) / len(live_signals),
        "risk_reward_avg": 0,
        "top_strategies": {},
        "market_sentiment": calculate_market_sentiment()
    }
    
    # Strength distribution
    for signal in live_signals:
        strength = signal.get('strength', 0)
        if strength >= 85:
            key = "85+"
        elif strength >= 75:
            key = "75-84"
        elif strength >= 65:
            key = "65-74"
        else:
            key = "50-64"
        analytics["by_strength"][key] = analytics["by_strength"].get(key, 0) + 1
    
    # Signal type distribution
    for signal in live_signals:
        sig_type = signal.get('signalType', 'Unknown')
        analytics["by_type"][sig_type] = analytics["by_type"].get(sig_type, 0) + 1
    
    # Timeframe distribution
    for signal in live_signals:
        timeframe = signal.get('timeframe', 'Unknown')
        analytics["by_timeframe"][timeframe] = analytics["by_timeframe"].get(timeframe, 0) + 1
    
    # Category distribution
    for signal in live_signals:
        category = signal.get('type', 'Unknown')
        analytics["by_category"][category] = analytics["by_category"].get(category, 0) + 1
    
    # Risk-reward analysis
    rr_ratios = [s.get('riskReward', 0) for s in live_signals if s.get('riskReward')]
    if rr_ratios:
        analytics["risk_reward_avg"] = round(sum(rr_ratios) / len(rr_ratios), 2)
    
    # Top strategies
    strategy_count = {}
    for signal in live_signals:
        for tag in signal.get('strategyTags', []):
            strategy_count[tag] = strategy_count.get(tag, 0) + 1
    
    analytics["top_strategies"] = dict(sorted(strategy_count.items(), 
                                            key=lambda x: x[1], reverse=True)[:10])
    
    return analytics

def calculate_market_sentiment():
    """Calculate overall market sentiment from signals"""
    if not live_signals:
        return "Neutral"
    
    # Count signal types
    strong_buy = len([s for s in live_signals if s.get('signalType') == 'Strong Buy'])
    buy = len([s for s in live_signals if s.get('signalType') == 'Buy'])
    watchlist = len([s for s in live_signals if s.get('signalType') == 'Watchlist'])
    
    total = len(live_signals)
    strong_buy_pct = (strong_buy / total) * 100
    buy_pct = (buy / total) * 100
    
    if strong_buy_pct > 30:
        return "Very Bullish"
    elif strong_buy_pct + buy_pct > 60:
        return "Bullish"
    elif strong_buy_pct + buy_pct > 40:
        return "Moderately Bullish"
    elif strong_buy_pct + buy_pct > 20:
        return "Neutral"
    else:
        return "Cautious"

def run_backtesting(symbol, timeframe, strategy_tags, days=30):
    """Run backtesting for specific strategy"""
    try:
        # Download historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=timeframe)
        
        if df.empty:
            return None
        
        # Calculate indicators
        df = calculate_advanced_indicators(df)
        
        # Simulate trades
        trades = []
        position = None
        
        for i in range(50, len(df)):  # Start after indicators are ready
            current_data = df.iloc[:i+1]
            signals = generate_professional_signals(current_data, symbol, timeframe)
            
            if signals and not position:
                # Enter position
                signal = signals[0]
                if any(tag in signal['strategyTags'] for tag in strategy_tags):
                    position = {
                        'entry_price': signal['entry'],
                        'stop_loss': signal['stoploss'],
                        'target': signal['exit'],
                        'entry_date': df.index[i],
                        'signal': signal
                    }
            
            elif position:
                # Check exit conditions
                current_price = df.iloc[i]['Close']
                
                if current_price <= position['stop_loss']:
                    # Stop loss hit
                    trades.append({
                        'entry': position['entry_price'],
                        'exit': current_price,
                        'pnl': current_price - position['entry_price'],
                        'pnl_pct': ((current_price - position['entry_price']) / position['entry_price']) * 100,
                        'exit_reason': 'Stop Loss',
                        'days_held': (df.index[i] - position['entry_date']).days
                    })
                    position = None
                
                elif current_price >= position['target']:
                    # Target hit
                    trades.append({
                        'entry': position['entry_price'],
                        'exit': current_price,
                        'pnl': current_price - position['entry_price'],
                        'pnl_pct': ((current_price - position['entry_price']) / position['entry_price']) * 100,
                        'exit_reason': 'Target',
                        'days_held': (df.index[i] - position['entry_date']).days
                    })
                    position = None
        
        # Calculate performance metrics
        if trades:
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades) * 100
            avg_win = np.mean([t['pnl_pct'] for t in trades if t['pnl'] > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t['pnl_pct'] for t in trades if t['pnl'] < 0]) if losing_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
                'trades': trades[-10:]  # Last 10 trades
            }
        
        return None
        
    except Exception as e:
        print(f"Backtesting error: {e}")
        return None

def generate_option_signals(underlying_symbols, expiry_dates=None):
    """Generate option-specific signals"""
    option_signals = []
    
    for symbol in underlying_symbols:
        try:
            # Get underlying data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="10d", interval="15m")
            
            if df.empty:
                continue
            
            df = calculate_advanced_indicators(df)
            latest = df.iloc[-1]
            
            # Option-specific criteria
            if (latest['Volume_Ratio'] > 2.5 and 
                latest['RSI'] > 60 and 
                latest['MACD'] > latest['MACD_Signal']):
                
                # Generate call option signal
                strike_price = round(latest['Close'] * 1.02, 0)  # 2% OTM
                
                option_signal = {
                    "symbol": f"{symbol.replace('.NS', '')}{strike_price}CE",
                    "underlying": symbol,
                    "strike": strike_price,
                    "type": "option",
                    "optionType": "CE",
                    "expiry": "WEEKLY",  # Default to weekly
                    "strategy": "Volume Breakout + Momentum",
                    "strategyTags": ["Volume Breakout", "RSI Strong", "MACD Bullish"],
                    "timeframe": "15m",
                    "signalType": "Buy",
                    "strength": calculate_advanced_signal_strength(
                        ["Volume Breakout", "RSI Strong"], 
                        ["MACD Bullish"], 
                        df
                    ),
                    "entry": round(latest['Close'] * 0.03, 2),  # Estimated option premium
                    "target1": round(latest['Close'] * 0.06, 2),
                    "target2": round(latest['Close'] * 0.10, 2),
                    "stoploss": round(latest['Close'] * 0.015, 2),
                    "iv": round(np.random.uniform(15, 40), 2),  # Simulated IV
                    "delta": round(np.random.uniform(0.3, 0.7), 3),  # Simulated Delta
                    "volume": int(latest.get('Volume', 0)),
                    "timestamp": datetime.now().isoformat()
                }
                
                option_signals.append(option_signal)
                
        except Exception as e:
            print(f"Option signal error for {symbol}: {e}")
            continue
    
    return option_signals

def generate_scalping_signals(symbols, focus_timeframes=['1m', '3m', '5m']):
    """Generate scalping-specific signals"""
    scalping_signals = []
    
    for symbol in symbols:
        for timeframe in focus_timeframes:
            try:
                ticker = yf.Ticker(symbol)
                
                if timeframe == '1m':
                    period = "1d"
                elif timeframe == '3m':
                    period = "2d"
                else:  # 5m
                    period = "3d"
                
                df = ticker.history(period=period, interval=timeframe)
                
                if df.empty or len(df) < 20:
                    continue
                
                df = calculate_advanced_indicators(df)
                latest = df.iloc[-1]
                previous = df.iloc[-2]
                
                # Scalping-specific criteria (quick momentum)
                if (latest['EMA_8'] > latest['EMA_20'] and
                    previous['EMA_8'] <= previous['EMA_20'] and
                    latest['Volume_Ratio'] > 1.8 and
                    latest['RSI'] > 55):
                    
                    scalping_signal = {
                        "symbol": symbol,
                        "type": "scalping",
                        "category": "scalping",
                        "strategy": "EMA Cross + Volume",
                        "strategyTags": ["EMA Cross", "Volume Surge", "Quick Momentum"],
                        "timeframe": timeframe,
                        "signalType": "Quick Buy",
                        "strength": calculate_advanced_signal_strength(
                            ["EMA Cross", "Volume Surge"], 
                            ["Quick Momentum"], 
                            df
                        ),
                        "entry": round(latest['Close'], 2),
                        "target1": round(latest['Close'] * 1.005, 2),  # 0.5% target
                        "target2": round(latest['Close'] * 1.01, 2),   # 1% target
                        "stoploss": round(latest['Close'] * 0.995, 2), # 0.5% stop
                        "duration": "5-15min",
                        "volume": int(latest.get('Volume', 0)),
                        "price": round(latest['Close'], 2),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    scalping_signals.append(scalping_signal)
                    
            except Exception as e:
                print(f"Scalping signal error for {symbol} ({timeframe}): {e}")
                continue
    
    return scalping_signals

# Export all functions
__all__ = [
    "scan_symbols_enhanced",
    "generate_professional_signals", 
    "get_signals",
    "get_advanced_analytics",
    "filter_signals_advanced",
    "calculate_advanced_indicators",
    "calculate_advanced_signal_strength",
    "run_backtesting",
    "generate_option_signals",
    "generate_scalping_signals",
    "calculate_market_sentiment"
]

def background_scanner():
    """LIVE background scanner that generates real-time signals - CORE FUNCTION"""
    global cached_signals, cached_options, cached_scalping, last_scan_time, bot_state
    
    while True:
        try:
            print("Starting LIVE signal scan...")
            current_time = datetime.now()
            market_open = is_market_open()
            
            bot_state.scan_status = "scanning"
            
            # Generate LIVE equity signals
            equity_signals = []
            symbols_to_scan = NIFTY_50_SYMBOLS[:12]  # Top 12 for faster scanning
            
            print(f"Scanning {len(symbols_to_scan)} symbols for live signals...")
            
            for symbol in symbols_to_scan:
                try:
                    data = get_live_stock_data(symbol, period="5d", interval="15m")
                    if data is not None:
                        data_with_indicators = calculate_technical_indicators(data)
                        signals = analyze_stock_signals(symbol, data_with_indicators)
                        equity_signals.extend(signals)
                        if signals:
                            print(f"Scanned {symbol}: {len(signals)} signals")
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
            
            # Generate LIVE option signals
            print("Generating live option signals...")
            option_signals = generate_live_option_signals()
            
            # Generate LIVE scalping signals
            print("Generating live scalping signals...")
            scalping_signals = generate_live_scalping_signals()
            
            # Sort signals by strength
            equity_signals = sorted(equity_signals, key=lambda x: x.get('strength', 0), reverse=True)[:10]
            option_signals = sorted(option_signals, key=lambda x: x.get('strength', 0), reverse=True)[:6]
            scalping_signals = sorted(scalping_signals, key=lambda x: x.get('strength', 0), reverse=True)[:8]
            
            # Update global cache
            cached_signals = equity_signals
            cached_options = option_signals
            cached_scalping = scalping_signals
            last_scan_time = current_time
            
            # Update bot state
            bot_state.cached_signals = equity_signals
            bot_state.cached_options = option_signals
            bot_state.cached_scalping = scalping_signals
            bot_state.last_scan_time = current_time
            bot_state.scan_status = "completed"
            bot_state.performance_metrics = calculate_performance_metrics(
                equity_signals + option_signals + scalping_signals
            )
            
            print(f"SCAN DONE: {len(equity_signals)} equity | {len(option_signals)} options | {len(scalping_signals)} scalping")
            
            # ✅ Safe high-priority alert block
            try:
                high_priority_signals = [
                    s for s in equity_signals + option_signals + scalping_signals
                    if s.get('strength', 0) >= 85
                ]
                if high_priority_signals:
                    for signal in high_priority_signals[:2]:
                        try:
                            send_telegram_alert_internal(signal)
                            print(f"Alert sent for {signal['symbol']} (Strength: {signal['strength']})")
                        except Exception as e:
                            print(f"Alert sending failed: {e}")
            except Exception as e:
                print(f"High-priority alert logic failed: {e}")
                
        except Exception as e:
            print(f"Background scanner error: {e}")
            bot_state.scan_status = "error"
            
        # Add delay to prevent excessive CPU usage
        print("Waiting before next scan...")
        time.sleep(30)  # Wait 30 seconds before next scan

        # ✅ Restore get_signal_data() for app.py compatibility
def get_signal_data():
    """Returns latest signals from cache"""
    return {
        "equity": cached_signals,
        "options": cached_options,
        "scalping": cached_scalping,
        "last_updated": last_scan_time.strftime("%Y-%m-%d %H:%M:%S") if last_scan_time else None
    }
