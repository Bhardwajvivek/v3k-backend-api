from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from datetime import datetime
import threading
import time
import logging
import os

# Import your strategies and utils
from strategies import scan_symbols_enhanced, get_signals

# Optional: if using nsepython for index data
from nsepython import nse_get_index_quote

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = Flask(__name__)
CORS(app)

# Globals
cached_signals = []
last_scan_time = None
auto_refresh_enabled = True

# Scan config
NIFTY_50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "KOTAKBANK.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS",
    "BAJFINANCE.NS", "LT.NS", "HCLTECH.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "TATAMOTORS.NS", "TECHM.NS",
    "COALINDIA.NS", "GRASIM.NS", "HINDALCO.NS", "INDUSINDBK.NS", "M&M.NS"
]

# Background scan thread
def background_scanner():
    global cached_signals, last_scan_time
    while auto_refresh_enabled:
        try:
            logger.info("🔍 Scanning symbols for live signals...")
            signals = scan_symbols_enhanced(NIFTY_50_SYMBOLS, ["5m", "15m", "1d"])
            cached_signals = signals
            last_scan_time = datetime.now()
            logger.info(f"✅ Found {len(signals)} signals.")
        except Exception as e:
            logger.error(f"Scan error: {e}")
            logger.error(traceback.format_exc())
        time.sleep(300)  # Every 5 mins

# Routes
@app.route("/get-signals", methods=["GET"])
def api_get_signals():
    return jsonify({
        "signals": cached_signals,
        "last_scan_time": last_scan_time.isoformat() if last_scan_time else None,
        "signal_count": len(cached_signals)
    })

@app.route("/get-live-indices", methods=["GET"])
def get_live_indices():
    try:
        index_list = [
            ("Nifty 50", "NIFTY 50"),
            ("Sensex", "S&P BSE SENSEX"),
            ("Bank Nifty", "NIFTY BANK"),
            ("Nifty IT", "NIFTY IT"),
            ("Nifty Pharma", "NIFTY PHARMA")
        ]
        result = []
        for label, code in index_list:
            try:
                data = nse_get_index_quote(code)
                result.append({
                    "symbol": label,
                    "price": data["data"][0]["last"],
                    "change": data["data"][0]["variation"]
                })
            except Exception:
                continue
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-market-news", methods=["GET"])
def get_market_news():
    try:
        return jsonify([
            {
                "title": "Man Buys ₹70,000 Ford After Dealership 'Played With the Numbers'",
                "url": "https://www.motor1.com/news/761946/ford-buyers-regret/",
                "source": "Motor1"
            },
            {
                "title": "Executives converge on Washington to halt Trump’s foreign investment tax",
                "url": "https://www.ft.com/content/e2525100-e432-4987-8b7d-e6f6b32154fe",
                "source": "Financial Times"
            },
            {
                "title": "Meta in Talks for Scale AI Investment That Could Top $10 Billion",
                "url": "https://www.bloomberg.com/news/articles/2025-06-08/meta-in-talks-for-scale-ai-investment",
                "source": "Bloomberg"
            }
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-trade-logs", methods=["GET"])
def get_trade_logs():
    try:
        dummy_logs = [
            {"symbol": "RELIANCE.NS", "action": "BUY", "price": 1448.8, "time": datetime.now().isoformat()},
            {"symbol": "TCS.NS", "action": "SELL", "price": 3423.0, "time": datetime.now().isoformat()}
        ]
        return jsonify(dummy_logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-strategy-accuracy", methods=["GET"])
def get_strategy_accuracy():
    try:
        dummy_stats = [
            {"strategy": "MACD Bullish Cross", "accuracy": 78.3, "backtests": 125},
            {"strategy": "Supertrend Bullish", "accuracy": 83.1, "backtests": 140},
            {"strategy": "RSI Bullish", "accuracy": 74.5, "backtests": 95}
        ]
        return jsonify(dummy_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Start server + scanner
if __name__ == "__main__":
    if auto_refresh_enabled:
        threading.Thread(target=background_scanner, daemon=True).start()
        logger.info("🔁 Background scanner started.")
    
    port = int(os.environ.get("PORT", 10000))  # Render sets this automatically
    app.run(host="0.0.0.0", port=port, debug=False)