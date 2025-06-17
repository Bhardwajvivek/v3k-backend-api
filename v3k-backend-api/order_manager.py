from firebase_sync import log_trade_to_firebase
from datetime import datetime

class OrderManager:
    def __init__(self):
        self.active_orders = {}

    def track_order(self, signal, order_id):
        symbol = signal.get("symbol")
        if symbol:
            self.active_orders[symbol] = {
                "order_id": order_id,
                "status": "open",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "signal": signal
            }

    def close_order(self, symbol, price):
        if symbol in self.active_orders:
            order = self.active_orders[symbol]
            order["status"] = "closed"
            order["close_price"] = price
            order["close_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_trade_to_firebase(order)
            del self.active_orders[symbol]
