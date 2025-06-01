from flask import Flask, jsonify, request
from firebase_sync import log_trade_to_firebase, fetch_all_trades_from_firebase
from strategies import generate_signal_for_symbol
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return "V3k AI Backend Running"

@app.route("/get-signals", methods=["GET"])
def get_signals():
    # Example hardcoded symbol list; replace with your own logic
    symbols = ["RELIANCE.NS", "SBIN.NS", "INFY.NS"]
    signals = []

    for symbol in symbols:
        try:
            signal = generate_signal_for_symbol(symbol)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
    
    return jsonify(signals)

@app.route("/log-trade", methods=["POST"])
def log_trade():
    trade_data = request.get_json()
    if not trade_data:
        return jsonify({"error": "Invalid payload"}), 400
    
    try:
        log_trade_to_firebase(trade_data)
        return jsonify({"message": "Trade logged successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/performance-report", methods=["GET"])
def performance_report():
    trades = fetch_all_trades_from_firebase()
    if not trades:
        return jsonify({"message": "No trades found"}), 200

    df = pd.DataFrame(trades)
    if 'result' not in df.columns or 'strategy' not in df.columns:
        return jsonify({"message": "Incomplete trade data"}), 400

    accuracy = (
        df.groupby("strategy")["result"]
        .value_counts(normalize=True)
        .unstack()
        .fillna(0)
        .get("Win", pd.Series(dtype=float))
        .round(2)
        .multiply(100)
        .to_dict()
    )

    total_pnl = df["pnl"].sum()
    trade_count = len(df)

    return jsonify({
        "accuracy": accuracy,
        "total_pnl": total_pnl,
        "trade_count": trade_count,
        "last_updated": pd.Timestamp.now().isoformat()
    })

if __name__ == "__main__":
    app.run(debug=False)
