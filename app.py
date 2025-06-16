# app.py  —  V3k Backend  (2025-06-16)

from flask import Flask, jsonify
from flask_cors import CORS
import traceback
from datetime import datetime
import threading
import time
import logging

# === Import your signal + index logic ===
from strategies import scan_symbols_enhanced  # ← make sure this exists
from nsepython import nse_get_index_quote     # optional – catches import error

# ──────────────────────────────────────────────────────────────
#  Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("v3k-backend")

# ──────────────────────────────────────────────────────────────
#  Flask App
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ──────────────────────────────────────────────────────────────
#  Globals
# ──────────────────────────────────────────────────────────────
cached_signals = []
last_scan_time = None
AUTO_REFRESH = True                  # set False if you only want on-demand scans
SCAN_INTERVAL_SEC = 300              # 5-minute background refresh

NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "KOTAKBANK.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS",
    "BAJFINANCE.NS", "LT.NS", "HCLTECH.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "TATAMOTORS.NS", "TECHM.NS",
    "COALINDIA.NS", "GRASIM.NS", "HINDALCO.NS", "INDUSINDBK.NS", "M&M.NS"
]

# ──────────────────────────────────────────────────────────────
#  Background Scanner
# ──────────────────────────────────────────────────────────────
def background_scanner():
    global cached_signals, last_scan_time
    threading.current_thread().name = "V3kScanner"
    while AUTO_REFRESH:
        try:
            logger.info("🔍  Scanning symbols for live signals …")
            signals = scan_symbols_enhanced(NIFTY_50, ["5m", "15m", "1d"])
            cached_signals = signals
            last_scan_time = datetime.utcnow()
            logger.info(f"✅  Scan complete — {len(signals)} signals.")
        except Exception as e:
            logger.error("Scan error:")
            logger.error(traceback.format_exc())
        time.sleep(SCAN_INTERVAL_SEC)

# Start scanner once server begins serving requests (works with Gunicorn)
@app.before_first_request
def launch_background_scanner():
    if AUTO_REFRESH and not any(t.name == "V3kScanner" for t in threading.enumerate()):
        logger.info("🔁  Starting background scanner …")
        threading.Thread(target=background_scanner, daemon=True).start()

# ──────────────────────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────────────────────
@app.route("/")
def root():
    return "✅ V3k Backend Running"

@app.route("/get-signals")
def api_get_signals():
    global cached_signals, last_scan_time

    # On very first call (cold start) run an immediate scan
    if not cached_signals:
        try:
            logger.info("⚡ First-request scan (cold start)")
            cached_signals = scan_symbols_enhanced(NIFTY_50, ["5m", "15m", "1d"])
            last_scan_time = datetime.utcnow()
        except Exception as e:
            logger.error("Initial scan failed:")
            logger.error(traceback.format_exc())

    return jsonify({
        "last_scan_time": last_scan_time.isoformat() if last_scan_time else None,
        "signal_count": len(cached_signals),
        "signals": cached_signals
    })

@app.route("/get-live-indices")
def api_get_live_indices():
    try:
        index_list = [
            ("Nifty 50", "NIFTY 50"),
            ("Sensex" , "S&P BSE SENSEX"),
            ("Bank Nifty", "NIFTY BANK"),
            ("Nifty IT", "NIFTY IT"),
            ("Nifty Pharma", "NIFTY PHARMA")
        ]
        res = []
        for label, code in index_list:
            try:
                data = nse_get_index_quote(code)
                res.append({
                    "symbol": label,
                    "price": data["data"][0]["last"],
                    "change": data["data"][0]["variation"]
                })
            except Exception:
                continue
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-market-news")
def api_get_market_news():
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

# ──────────────────────────────────────────────────────────────
#  Manual Run (local dev)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if AUTO_REFRESH:
        launch_background_scanner()
    app.run(host="0.0.0.0", port=5000, debug=False)
