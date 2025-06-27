from firebase_sync import log_trade_to_firebase

# Sample trade data to test Firebase logging
sample_trade = {
    "symbol": "RELIANCE.NS",
    "order_type": "BUY",
    "price": 2950.00,
    "quantity": 5,
    "status": "Executed",
    "strategy": "MACD + RSI + Supertrend",
    "time": "2025-06-01 15:30:00"
}

# Call the logger function
log_trade_to_firebase(sample_trade)
print("✅ Firebase logging test completed.")
