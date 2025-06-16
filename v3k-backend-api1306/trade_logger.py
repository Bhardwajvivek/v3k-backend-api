# trade_logger.py
import datetime
from firebase_sync import log_trade_to_firebase

def log_trade(signal, result="PENDING", tag="manual", comment=""):
    trade_data = {
        "symbol": signal.get("symbol"),
        "strategy": signal.get("strategy"),
        "type": signal.get("type"),
        "timeframe": signal.get("timeframe"),
        "price": signal.get("price"),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "result": result,  # PENDING, WIN, LOSS
        "tag": tag,         # manual, auto, re-entry, user-tagged, etc.
        "comment": comment,
    }
    log_trade_to_firebase(trade_data)
    print("📘 Trade logged:", trade_data)
