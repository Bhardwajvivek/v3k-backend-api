from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

def calculate_supertrend(data, period=10, multiplier=3):
    data = data.copy()
    hl2 = (data['High'] + data['Low']) / 2
    atr = data['High'].rolling(period).max() - data['Low'].rolling(period).min()

    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)

    supertrend = [False] * len(data)
    for i in range(1, len(data)):
        try:
            if data['Close'].iloc[i] > upper_band.iloc[i - 1]:
                supertrend[i] = True
            elif data['Close'].iloc[i] < lower_band.iloc[i - 1]:
                supertrend[i] = False
            else:
                supertrend[i] = supertrend[i - 1]
        except Exception:
            supertrend[i] = False

    data['Supertrend'] = supertrend
    return data

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

@app.route("/")
def health_check():
    return jsonify({"status": "ok"})

@app.route("/get-signals")
def get_signals():
    try:
        symbols = ["RELIANCE.NS", "BANKNIFTY.NS"]
        signals = []

        for symbol in symbols:
            df = yf.download(symbol, period="5d", interval="15m")
            if df.empty or 'Close' not in df.columns:
                continue

            df = calculate_supertrend(df)
            macd, signal_line = calculate_macd(df)
            df["MACD"] = macd
            df["Signal_Line"] = signal_line

            last = df.iloc[-1]
            prev = df.iloc[-2]

            # Entry logic
            if (
                last["MACD"] > last["Signal_Line"]
                and last["Supertrend"]
                and prev["MACD"] <= prev["Signal_Line"]
            ):
                signals.append({
                    "symbol": symbol.replace(".NS", ""),
                    "type": "Buy",
                    "price": round(last["Close"], 2),
                    "strategy": "MACD + Supertrend",
                    "timeframe": "15min"
                })
            elif (
                last["MACD"] < last["Signal_Line"]
                and not last["Supertrend"]
                and prev["MACD"] >= prev["Signal_Line"]
            ):
                signals.append({
                    "symbol": symbol.replace(".NS", ""),
                    "type": "Sell",
                    "price": round(last["Close"], 2),
                    "strategy": "MACD + Supertrend",
                    "timeframe": "15min"
                })

        return jsonify({"signals": signals})

    except Exception as e:
        print("Error in /get-signals:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
