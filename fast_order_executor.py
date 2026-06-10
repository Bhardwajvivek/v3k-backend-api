from kiteconnect import KiteConnect
import json
import time
import requests
from datetime import datetime
import pandas as pd
from firebase_sync import log_trade_to_firebase  # ✅ Firebase connected

# ✅ Log a test trade to Firebase
test_trade = {
    "symbol": "RELIANCE.NS",
    "strategy": "MACD+RSI",
    "signal_type": "BUY",
    "entry_price": 2800.00,
    "exit_price": 2845.50,
    "pnl": 45.50,
    "result": "Win",
    "timeframe": "15m",
    "timestamp": pd.Timestamp.now().isoformat()
}
try:
    log_trade_to_firebase(test_trade)
    print("✅ Test trade logged to Firebase:", test_trade)
except Exception as e:
    print("❌ Firebase Test Logging Failed:", e)

# ⚙️ Zerodha Order Execution Begins...
api_key = "l9y0a5vozuozcjw4"
with open("access_token.txt", "r") as f:
    access_token = f.read().strip()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

SIGNAL_API = "https://v3k-backend-api.onrender.com/get-signals"
executed = set()

def place_order(signal):
    try:
        symbol = signal["symbol"].replace(".NS", "")
        direction = signal.get("direction", "BUY")
        quantity = 1

        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY if direction == "BUY" else kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS
        )

        trade_data = {
            "symbol": symbol,
            "direction": direction,
            "quantity": quantity,
            "strategy": signal.get("strategy", ""),
            "price": signal.get("price", 0),
            "timeframe": signal.get("timeframe", ""),
            "status": "executed",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        log_trade_to_firebase(trade_data)
        print(f"✅ Order Placed: {symbol} ({direction}) — Order ID: {order_id}")
        return order_id

    except Exception as e:
        print(f"❌ Order Error for {signal['symbol']}: {e}")
        return None

def run_executor():
    while True:
        try:
            res = requests.get(SIGNAL_API)
            signals = res.json()

            for s in signals:
                uid = f"{s['symbol']}_{s['timeframe']}_{s['strength']}"
                if s.get('strength', 0) >= 75 and uid not in executed:
                    order = place_order(s)
                    if order:
                        executed.add(uid)
        except Exception as e:
            print("⚠️ Executor Loop Error:", e)

        time.sleep(30)

if __name__ == "__main__":
    run_executor()
