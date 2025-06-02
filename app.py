from flask import Flask, jsonify
from flask_cors import CORS
from firebase_sync import log_trade_to_firebase, fetch_all_trades_from_firebase
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "🔥 V3k AI Trading Bot Backend is running!"

@app.route("/performance-report", methods=["GET"])
def performance_report():
    trades = fetch_all_trades_from_firebase()
    
    if not trades:
        return jsonify({"message": "No trades found"}), 200

    df = pd.DataFrame(trades)

    # Check required fields
    if 'result' not in df.columns or 'strategy' not in df.columns:
        return jsonify({"message": "Incomplete trade data"}), 400

    # Calculate win-rate per strategy
    summary = df.groupby("strategy")["result"].value_counts().unstack(fill_value=0)
    summary["Total"] = summary.sum(axis=1)
    summary["Success %"] = round(100 * summary.get("Win", 0) / summary["Total"], 2)

    report = summary.reset_index().to_dict(orient="records")
    return jsonify(report)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
