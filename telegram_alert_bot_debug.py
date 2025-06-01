
import requests
import time

BOT_TOKEN = '8130024944:AAHPp7S8RqjTWWF3O71SvlByu6XVkeBdPUk'
USER_ID = '5702457196'
API_URL = 'http://127.0.0.1:5000/get-signals'
sent_signals = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': USER_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=data)
        print("📤 Telegram sent:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error sending message:", e)

def format_signal(sig):
    return f"""
📡 *V3k AI Signal Alert* 📡

*Symbol:* {sig['symbol']}
*Strategy:* {sig['strategy']}
*Type:* {sig['type']}
*Timeframe:* {sig['timeframe']}
*Price:* ₹{sig['price']}
*Strength:* {sig['strength']}%
"""

def run_alert_loop():
    print("🚀 Telegram Alert Bot Started")
    # Always send a test message once
    send_telegram_message("🧪 Test message from V3k Bot. If you see this, alerts are working!")

    while True:
        try:
            res = requests.get(API_URL)
            signals = res.json()

            for sig in signals:
                uid = f"{sig['symbol']}|{sig['strategy']}|{sig['timeframe']}"
                if uid not in sent_signals:
                    message = format_signal(sig)
                    send_telegram_message(message)
                    sent_signals.add(uid)

        except Exception as e:
            print("❌ Fetch error:", e)

        time.sleep(60)

if __name__ == "__main__":
    run_alert_loop()
