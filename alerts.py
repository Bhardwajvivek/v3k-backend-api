# alerts.py ✅

import requests

# Replace with your actual bot token and chat ID
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_alert_internal(signal):
    """Send a formatted signal alert to your Telegram bot"""
    try:
        message = (
            f"📢 *New Trading Signal!*\n\n"
            f"*Symbol:* {signal.get('symbol', 'N/A')}\n"
            f"*Type:* {signal.get('type', 'N/A')}\n"
            f"*Strength:* {signal.get('strength', 'N/A')}%\n"
            f"*Timeframe:* {signal.get('timeframe', 'N/A')}\n"
            f"*Reasons:* {', '.join(signal.get('reasons', []))}"
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Telegram error: {response.text}")
        else:
            print("✅ Telegram alert sent")

    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")
