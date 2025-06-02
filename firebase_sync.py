import firebase_admin
from firebase_admin import credentials, firestore
import os

# Path to your service account key
FIREBASE_KEY_PATH = "firebase/serviceAccountKey.json"

# Initialize Firebase
db = None
try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase initialized")
        else:
            print("⚠️ Firebase key not found — Firebase logging will be disabled.")
except Exception as e:
    print("🔥 Error initializing Firebase:", e)

# Log a trade to Firebase
def log_trade_to_firebase(trade_data):
    if db is None:
        print("⚠️ Firebase not available — skipping log.")
        return
    try:
        db.collection("trades").add(trade_data)
        print(f"✅ Trade logged to Firebase: {trade_data['symbol']}")
    except Exception as e:
        print("🔥 Error logging trade to Firebase:", e)

# Fetch all trades from Firebase with safety
def fetch_all_trades_from_firebase():
    if db is None:
        print("⚠️ Firebase not available — cannot fetch trades.")
        return []
    try:
        docs = db.collection("trades").limit(100).stream()  # Adjust limit as needed
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print("🔥 Error fetching trades from Firebase:", e)
        return []
