import firebase_admin
from firebase_admin import credentials, firestore

# Load the service account key and initialize Firebase
cred = credentials.Certificate("firebase/serviceAccountKey.json")

# Avoid re-initializing if already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to log trade data
def log_trade_to_firebase(trade_data):
    try:
        doc_ref = db.collection("trade_logs").document()
        doc_ref.set(trade_data)
        print("✅ Trade logged to Firebase:", trade_data)
    except Exception as e:
        print("❌ Firebase logging failed:", e)

# Function to retrieve all trades (for future performance report)
def fetch_all_trades_from_firebase():
    try:
        trades = db.collection("trade_logs").stream()
        return [doc.to_dict() for doc in trades]
    except Exception as e:
        print("❌ Fetch trades failed:", e)
        return []
