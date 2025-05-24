from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

def calculate_supertrend(df, period=10, multiplier=3):
    df = df.copy()
    df['ATR'] = df['High'].rolling(window=period).max() - df['Low'].rolling(window=period).min()
    df['UpperBand'] = ((df['High'] + df['Low']) / 2) + multiplier * df['ATR']
    df['LowerBand'] = ((df['High'] + df['Low']) / 2) - multiplier * df['ATR']
    df['Supertrend'] = df['Close']
    return df

def calculate_macd(df):
    df = df.copy()
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["SignalLine"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def scan_stock(symbol):
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if data.empty or len(data) < 35:
            return None

        data.reset_index(inplace=True)
        data.columns = [col.capitalize() for col in data.columns]

        data = calculate_macd(data)
        data = calculate_supertrend(data)

        latest = data.iloc[-1]
        previous = data.iloc[-2]

        signal = None
        if latest["MACD"] > latest["SignalLine"] and previous["MACD"] <= previous["SignalLine"]:
            signal = {
                "symbol": symbol,
                "type": "Buy",
                "price": round(latest["Close"], 2),
                "strategy": "MACD Crossover",
                "timeframe": "15min"
            }
        elif latest["MACD"] < latest["SignalLine"] and previous["MACD"] >= previous["SignalLine"]:
            signal = {
                "symbol": symbol,
                "type": "Sell",
                "price": round(latest["Close"], 2),
                "strategy": "MACD Crossover",
                "timeframe": "15min"
            }
        return signal
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        return None

@app.route("/get-signals")
def get_signals():
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    all_signals = []

    for symbol in symbols:
        signal = scan_stock(symbol)
        if signal:
            all_signals.append(signal)

    return jsonify({"signals": all_signals})

@app.route("/")
def home():
    return jsonify({"status": "ok"})
