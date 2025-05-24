
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

def check_macd_crossover(df):
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]

def check_supertrend(df, period=7, multiplier=3):
    atr = df['High'].rolling(window=period).max() - df['Low'].rolling(window=period).min()
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr
    return df['Close'].iloc[-1] > upperband.iloc[-1]

def scan_symbol(symbol):
    try:
        df = yf.download(symbol, interval="15m", period="2d", progress=False)
        if df.empty or len(df) < 30:
            return None

        if check_macd_crossover(df):
            return {
                "symbol": symbol.replace(".NS", ""),
                "type": "Buy",
                "price": round(df['Close'].iloc[-1], 2),
                "strategy": "MACD Crossover",
                "timeframe": "15min"
            }

        if check_supertrend(df):
            return {
                "symbol": symbol.replace(".NS", ""),
                "type": "Buy",
                "price": round(df['Close'].iloc[-1], 2),
                "strategy": "Supertrend Breakout",
                "timeframe": "15min"
            }

        return None
    except Exception as e:
        return None

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

@app.route("/get-signals", methods=["GET"])
def get_signals():
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    results = []
    for sym in symbols:
        result = scan_symbol(sym)
        if result:
            results.append(result)
    return jsonify({"signals": results})

if __name__ == "__main__":
    app.run(debug=True)
