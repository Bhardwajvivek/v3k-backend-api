from flask import Flask, jsonify, request
from flask_cors import CORS
from strategies import scan_symbols, get_signals
import threading
import time
import json
import os

app = Flask(__name__)
CORS(app)

# 🔁 Auto-refreshing signal scanner loop
symbols = []
timeframes = ["5m", "15m", "1d"]

# Load from CSV or fallback to hardcoded Nifty 50 sample
if os.path.exists("nifty.csv"):
    with open("nifty.csv", "r") as f:
        symbols = [line.strip() for line in f.readlines() if line.strip()]
else:
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

def signal_refresher():
    while True:
        try:
            print("🔍 Scanning signals...")
            scan_symbols(symbols, timeframes)
        except Exception as e:
            print("⚠️ Error in refresher loop:", str(e))
        time.sleep(60)  # Refresh every 60 seconds

@app.route("/get-signals", methods=["GET"])
def get_all_signals():
    return jsonify(get_signals())

@app.route("/", methods=["GET"])
def home():
    return "✅ V3k AI Backend is Running!"

if __name__ == "__main__":
    # 🔁 Start scanning in background
    t = threading.Thread(target=signal_refresher)
    t.daemon = True
    t.start()
    
    app.run(debug=True)
