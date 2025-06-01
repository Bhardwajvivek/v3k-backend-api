import os
import firebase_admin
from firebase_admin import credentials, firestore

# ✅ Check if Firebase key exists before initializing
if os.path.exists("firebase/serviceAccountKey.json"):
    cred = credentials.Certificate("firebase/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    firebase_enabled = True
else:
    print("⚠️ Firebase key not found — Firebase logging will be disabled.")
    firebase_enabled = False

def log_trade_to_firebase(trade_data):
    if not firebase_enabled:
        return
    try:
        db.collection("trade_logs").add(trade_data)
        print(f"✅ Trade logged to Firebase: {trade_data}")
    except Exception as e:
        print(f"❌ Firebase logging failed: {e}")

def fetch_all_trades_from_firebase():
    if not firebase_enabled:
        return []
    try:
        trades = db.collection("trade_logs").stream()
        return [t.to_dict() for t in trades]
    except Exception as e:
        print(f"❌ Firebase fetch failed: {e}")
        return []
