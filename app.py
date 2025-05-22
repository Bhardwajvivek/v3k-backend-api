from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

# ✅ Health route
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

# ✅ Example signal route (temporary test)
@app.route("/get-signals", methods=["GET"])
def get_signals():
    signals = [
        {
            "symbol": "RELIANCE",
            "type": "Buy",
            "price": 2850,
            "strategy": "MACD + Supertrend",
            "timeframe": "15min",
        },
        {
            "symbol": "BANKNIFTY",
            "type": "Sell",
            "price": 48200,
            "strategy": "Pivot Breakdown",
            "timeframe": "5min",
        }
    ]
    return jsonify({"signals": signals})

# ✅ Run if local (ignored by gunicorn in Render)
if __name__ == "__main__":
    app.run(debug=True)
