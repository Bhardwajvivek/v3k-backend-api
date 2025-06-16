import os
import firebase_admin
from firebase_admin import credentials, firestore, messaging

FIREBASE_KEY_PATH = os.path.join(os.path.dirname(__file__), 'firebase', 'serviceAccountKey.json')

db = None
firebase_initialized = False

# Initialize Firebase
try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_initialized = True
            print("✅ Firebase initialized")
        else:
            print("⚠️ Firebase key not found — Firebase logging will be disabled.")
except Exception as e:
    print(f"🔥 Firebase initialization error: {e}")

# Log a trade to Firebase
def log_trade_to_firebase(trade_data):
    if not firebase_initialized or db is None:
        print("⚠️ Firebase not available — skipping log.")
        return
    try:
        db.collection("trades").add(trade_data)
        print(f"✅ Trade logged to Firebase: {trade_data.get('symbol', 'UNKNOWN')}")
        send_push_alert(trade_data)
    except Exception as e:
        print(f"🔥 Error logging trade to Firebase: {e}")

# Fetch trades
def fetch_all_trades_from_firebase(limit=100):
    if not firebase_initialized or db is None:
        print("⚠️ Firebase not available — cannot fetch trades.")
        return []
    try:
        trades_ref = db.collection("trades").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        docs = trades_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"🔥 Error fetching trades from Firebase: {e}")
        return []

# Push notification to all saved FCM tokens
def send_push_alert(trade_data):
    if not firebase_initialized:
        return
    try:
        tokens_ref = db.collection("device_tokens").stream()
        tokens = [doc.to_dict().get("token") for doc in tokens_ref if doc.to_dict().get("token")]

        if not tokens:
            print("⚠️ No tokens to send push.")
            return

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=f"📈 {trade_data['symbol']} Signal",
                body=f"{trade_data['strategy']} | {trade_data['timeframe']} @ ₹{trade_data['price']}"
            ),
            tokens=tokens
        )

        response = messaging.send_multicast(message)
        print(f"📲 Push sent to {response.success_count}/{len(tokens)} devices")
    except Exception as e:
        print(f"🔥 Error sending push alert: {e}")
