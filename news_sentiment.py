from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Bot
from strategies import scan_symbols, get_signals
from news_sentiment import fetch_sentiment_score
import pandas as pd
import traceback

# Flask app setup
app = Flask(__name__)
CORS(app)

# Telegram bot setup
TELEGRAM_API_TOKEN = "7685961335:AAGwpUiRpKpIpUZh3w1PQVWElFO0fIYyHEs"
TELEGRAM_CHAT_ID = "6955435826"
bot = Bot(token=TELEGRAM_API_TOKEN)

# Telegram send helper
def send_telegram_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        print("✅ Telegram alert sent.")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")

@app.route("/")
def index():
    return "🔥 V3k AI Trading Bot Backend is running!"

@app.route("/get-signals", methods=["GET"])
def get_live_signals():
    try:
        symbols = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
        timeframes = ["5m", "15m", "1d"]

        signals = scan_symbols(symbols, timeframes)

        if signals:
            send_telegram_alert(f"📡 *New Signals Generated:*\n\n{', '.join([s['symbol'] for s in signals])}")

        return jsonify({"signals": signals})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/send-telegram", methods=["POST"])
def send_telegram_from_frontend():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        message = f"""
📡 *Manual Signal Alert* (via Dashboard)

*Symbol:* {data.get('symbol')}
*Strategy:* {data.get('strategy')}
*Timeframe:* {data.get('timeframe')}
*Price:* ₹{data.get('price')}
"""
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        return jsonify({"message": "Alert sent to Telegram!"})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/get-sentiment", methods=["POST"])
def get_sentiment():
    try:
        data = request.get_json()
        symbol = data.get("symbol")
        if not symbol:
            return jsonify({"error": "No symbol provided"}), 400

        sentiment = fetch_sentiment_score(symbol)
        return jsonify(sentiment)
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

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
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
