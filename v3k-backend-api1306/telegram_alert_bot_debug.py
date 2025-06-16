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
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            print("✅ Telegram alert sent.")
        else:
            print("❌ Failed to send Telegram alert:", response.text)
    except Exception as e:
        print("❌ Telegram Error:", e)

def format_signal(sig):
    return f"""
📡 *V3k AI Signal Alert* 📡

*Symbol:* {sig['symbol']}
*Strategy:* {sig['strategy']}
*Type:* {sig.get('type', 'N/A')}
*Timeframe:* {sig['timeframe']}
*Price:* ₹{sig['price']}
*Strength:* {sig['strength']}%
"""

def run_alert_loop():
    print("🚀 Telegram Alert Bot Started")
    send_telegram_message("🧪 Test message from V3k Bot. If you see this, alerts are working!")

    while True:
        try:
            res = requests.get(API_URL, timeout=10)
            if res.status_code != 200:
                print(f"⚠️ Error fetching signals: {res.status_code}")
                time.sleep(60)
                continue

            data = res.json()
            signals = data.get("signals", []) if isinstance(data, dict) else data

            new_alerts = 0
            for sig in signals:
                uid = f"{sig['symbol']}|{sig['strategy']}|{sig['timeframe']}"
                if uid not in sent_signals:
                    send_telegram_message(format_signal(sig))
                    sent_signals.add(uid)
                    new_alerts += 1

            print(f"📈 New alerts sent: {new_alerts} | Total tracked: {len(sent_signals)}")

        except Exception as e:
            print("❌ Signal fetch error:", e)

        time.sleep(60)

if __name__ == "__main__":
    run_alert_loop()
