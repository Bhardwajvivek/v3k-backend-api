from flask import Flask, jsonify
from flask_cors import CORS
from strategies import scan_symbols
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "V3k AI Trading Bot API is Live"

@app.route("/get-signals")
def get_signals():
    try:
        stock_list = pd.read_csv("nifty.csv")['Symbol'].tolist()
        signals = scan_symbols(stock_list)
        return jsonify(signals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
