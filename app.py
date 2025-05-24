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

def calculate_supertrend(df, period=7, multiplier=3):
    df = df.copy()

    # Calculate ATR
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift())
    df['L-PC'] = abs(df['Low'] - df['Close'].shift())
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(period).mean()

    # Calculate upper and lower bands
    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])

    # Initialize Supertrend
    df['Supertrend'] = True
    for i in range(1, len(df)):
        curr_close = df['Close'].iloc[i]
        prev_close = df['Close'].iloc[i - 1]
        prev_supertrend = df['Supertrend'].iloc[i - 1]

        if curr_close > df['UpperBand'].iloc[i - 1]:
            df['Supertrend'].iloc[i] = True
        elif curr_close < df['LowerBand'].iloc[i - 1]:
            df['Supertrend'].iloc[i] = False
        else:
            df['Supertrend'].iloc[i] = prev_supertrend

            if prev_supertrend and df['LowerBand'].iloc[i] < df['LowerBand'].iloc[i - 1]:
                df['LowerBand'].iloc[i] = df['LowerBand'].iloc[i - 1]
            if not prev_supertrend and df['UpperBand'].iloc[i] > df['UpperBand'].iloc[i - 1]:
                df['UpperBand'].iloc[i] = df['UpperBand'].iloc[i - 1]

    return df['Supertrend']

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
