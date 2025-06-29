import pandas as pd
import yfinance as yf
from strategies import scan_symbols, get_signals

# ✅ Load symbols from CSV
def load_symbols_from_csv():
    try:
        df = pd.read_csv("nifty.csv")
        return df['Symbol'].dropna().tolist()
    except Exception as e:
        print("⚠️ Error loading CSV:", e)
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]  # Fallback symbols

# 🧪 Test Watchlist Signals
def test_watchlist_signals():
    symbols = load_symbols_from_csv()
    timeframes = ["5m", "15m", "1d"]

    print("🔍 Scanning for Watchlist signals...\n")
    scan_symbols(symbols, timeframes)

    all_signals = get_signals()

    if not all_signals:
        print("⚠️ No signals found.")
        return

    watchlist_signals = [s for s in all_signals if s.get("type") == "Watchlist"]

    for s in watchlist_signals:
        print(f"📌 {s['symbol']} | {s['timeframe']} | {s['strategy']} | Strength: {s['strength']} | Price: ₹{s['price']}")

if __name__ == "__main__":
    test_watchlist_signals()
