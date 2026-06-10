from firebase_sync import log_trade_to_firebase
from datetime import datetime
import pandas as pd

test_trade = {
    "symbol": "RELIANCE.NS",
    "strategy": "MACD+RSI",
    "signal_type": "BUY",
    "entry_price": 2800.00,
    "exit_price": 2845.50,
    "pnl": round(2845.50 - 2800.00, 2),
    "result": "Win",
    "timeframe": "15m",
    "timestamp": pd.Timestamp.now().isoformat()
}

log_trade_to_firebase(test_trade)
