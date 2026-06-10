from firebase_admin import db
import datetime
import time

def track_outcomes():
    print("📊 Signal Outcome Tracker started...")
    ref = db.reference('/logs')

    while True:
        try:
            logs = ref.get()
            if logs:
                for key, entry in logs.items():
                    if entry.get("status") == "executed" and "close_price" not in entry:
                        # Simulate outcome update (you'll replace this with real exit logic)
                        simulated_close_price = float(entry.get("price", 0)) * 1.01
                        entry["close_price"] = round(simulated_close_price, 2)
                        entry["status"] = "closed"
                        entry["close_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ref.child(key).set(entry)
                        print(f"🔁 Trade outcome updated for: {entry['symbol']}")
        except Exception as e:
            print("⚠️ Tracker Error:", e)

        time.sleep(60)

if __name__ == "__main__":
    track_outcomes()
