from flask import Flask, jsonify
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_supertrend(data, period=7, multiplier=3):
    hl2 = (data['High'] + data['Low']) / 2
    atr = data['High'].rolling(period).max() - data['Low'].rolling(period).min()
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)

    supertrend = [True] * len(data)
    for i in range(1, len(data)):
        if data['Close'][i] > upper_band[i - 1]:
            supertrend[i] = True
        elif data['Close'][i] < lower_band[i - 1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i - 1]
    return supertrend

@app.route("/get-signals", methods=["GET"])
def get_signals():
    symbols = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "SBIN.NS", "ICICIBANK.NS"]
    results = []

    for symbol in symbols:
        df = yf.download(symbol, interval="1d", period="15d")
        if df.empty or len(df) < 10:
            continue

        df["MACD"], df["Signal"] = calculate_macd(df)
        df["Supertrend"] = calculate_supertrend(df)

        if (
            df["MACD"].iloc[-2] < df["Signal"].iloc[-2]
            and df["MACD"].iloc[-1] > df["Signal"].iloc[-1]
            and df["Supertrend"].iloc[-1] == True
        ):
            results.append({
                "symbol": symbol.replace(".NS", ""),
                "type": "Buy",
                "price": round(df["Close"].iloc[-1], 2),
                "strategy": "MACD + Supertrend",
                "timeframe": "1d"
            })

    return jsonify({"signals": results})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
