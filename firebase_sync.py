import os
import firebase_admin
from firebase_admin import credentials, firestore

firebase_initialized = False
db = None

try:
    cred_path = os.path.join(os.path.dirname(__file__), 'firebase', 'serviceAccountKey.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_initialized = True
    else:
        print("⚠️ Firebase key not found — Firebase logging will be disabled.")
except Exception as e:
    print(f"🔥 Firebase initialization error: {e}")

def fetch_all_trades_from_firebase():
    if not firebase_initialized or db is None:
        return []
    try:
        trades_ref = db.collection("trades")
        docs = trades_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []
