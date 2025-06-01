from flask import Flask, jsonify
from firebase_sync import fetch_all_trades_from_firebase
import pandas as pd
import traceback

app = Flask(__name__)

@app.route('/')
def home():
    return "V3k Bot API is Running!"

@app.route("/performance-report", methods=["GET"])
def performance_report():
    try:
        trades = fetch_all_trades_from_firebase()

        if not trades or not isinstance(trades, list):
            return jsonify({"message": "No trades found"}), 200

        df = pd.DataFrame(trades)
        if 'result' not in df.columns or 'strategy' not in df.columns:
            return jsonify({"message": "Incomplete trade data"}), 400

        total = len(df)
        wins = df[df["result"] == "win"].shape[0]
        losses = df[df["result"] == "loss"].shape[0]
        accuracy = (wins / total) * 100 if total else 0

        strategy_stats = df["strategy"].value_counts().to_dict()
        strategy_win_rate = df[df["result"] == "win"]["strategy"].value_counts().to_dict()

        for key in strategy_stats:
            win_count = strategy_win_rate.get(key, 0)
            strategy_stats[key] = {
                "total": strategy_stats[key],
                "wins": win_count,
                "accuracy": round((win_count / strategy_stats[key]) * 100, 2)
            }

        return jsonify({
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "overall_accuracy": round(accuracy, 2),
            "strategy_breakdown": strategy_stats
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
