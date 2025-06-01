import os
import json

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    FIREBASE_AVAILABLE = True

    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

    db = firestore.client()

except Exception as e:
    print(f"⚠️ Firebase setup failed: {e}")
    FIREBASE_AVAILABLE = False
    db = None

def log_trade_to_firebase(trade_data):
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase not available. Skipping logging.")
        return
    db.collection("trades").add(trade_data)

def fetch_all_trades_from_firebase():
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase not available. Returning empty list.")
        return []
    trades_ref = db.collection("trades")
    docs = trades_ref.stream()
    return [doc.to_dict() for doc in docs]
