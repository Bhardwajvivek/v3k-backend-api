import time
import json
import pandas as pd
from strategies import scan_symbols, get_signals

# Load symbols from CSV
def load_symbols_from_csv():
    try:
        df = pd.read_csv("nifty.csv")
        return df["Symbol"].dropna().tolist()
    except Exception as e:
        print(f"⚠️ Error loading CSV: {e}")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]  # Fallback

# Save signals to file
def save_signals_to_json(signals, filename="signals.json"):
    try:
        with open(filename, "w") as f:
            json.dump(signals, f, indent=4)
        print(f"✅ Saved {len(signals)} signals to {filename}")
    except Exception as e:
        print(f"⚠️ Error saving signals: {e}")

# Run strategy scan
def run_strategy_scan():
    print("📡 Running V3k Signal Scan...")
    symbols = load_symbols_from_csv()
    timeframes = ["5m", "15m", "1d"]  # intraday + swing

    try:
        scan_symbols(symbols, timeframes)
        signals = get_signals()
        save_signals_to_json(signals)
    except Exception as e:
        print(f"❌ Strategy Scan Error: {e}")

if __name__ == "__main__":
    while True:
        run_strategy_scan()
        print("⏱️ Waiting 60 seconds before next scan...\n")
        time.sleep(60)
