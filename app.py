from flask import Flask, jsonify
from firebase_sync import fetch_all_trades_from_firebase
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return "V3k Backend API is Live!"

@app.route("/performance-report", methods=["GET"])
def performance_report():
    try:
        trades = fetch_all_trades_from_firebase()
        if not trades:
            return jsonify({"message": "No trades found"}), 200

        df = pd.DataFrame(trades)
        if 'result' not in df.columns or 'strategy' not in df.columns:
            return jsonify({"message": "Incomplete trade data"}), 400

        summary = (
            df.groupby(['strategy', 'result'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .to_dict(orient="records")
        )
        return jsonify(summary)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(debug=True)
