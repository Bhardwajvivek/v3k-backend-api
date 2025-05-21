from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS for frontend connection

@app.route('/signals')
def get_signals():
    return jsonify([
        {
            "symbol": "RELIANCE",
            "type": "Intraday",
            "entry": 2845.50,
            "stop_loss": 2832.00,
            "target": 2865.00,
            "strategy": "MACD + Supertrend"
        },
        {
            "symbol": "BANKNIFTY23000CE",
            "type": "Options",
            "entry": 245.00,
            "stop_loss": 230.00,
            "target": 275.00,
            "strategy": "RSI + Volume Spike"
        }
    ])

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
