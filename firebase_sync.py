import firebase_admin
from firebase_admin import credentials, firestore

try:
    cred = credentials.Certificate("firebase/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print("⚠️ Firebase initialization failed:", e)
    db = None

def log_trade_to_firebase(trade_data):
    if db:
        try:
            db.collection("trades").add(trade_data)
        except Exception as e:
            print("Error logging trade to Firebase:", e)

def fetch_all_trades_from_firebase():
    if db:
        try:
            trades_ref = db.collection("trades")
            docs = trades_ref.stream()
            trades = [doc.to_dict() for doc in docs]
            return trades
        except Exception as e:
            print("Error fetching trades:", e)
            return []
    else:
        return []
