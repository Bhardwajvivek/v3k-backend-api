import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

def get_stock_pair_data(symbol1, symbol2, period="6mo", interval="1d"):
    df1 = yf.download(symbol1, period=period, interval=interval, progress=False)['Close']
    df2 = yf.download(symbol2, period=period, interval=interval, progress=False)['Close']
    df = pd.DataFrame({symbol1: df1, symbol2: df2}).dropna()
    return df

def calculate_spread(df, sym1, sym2):
    ratio = df[sym1] / df[sym2]
    spread = ratio - ratio.mean()
    zscore = (spread - spread.mean()) / spread.std()
    return spread, zscore

def detect_stat_arb_opportunity(sym1, sym2, z_threshold=2):
    df = get_stock_pair_data(sym1, sym2)
    if df.empty or len(df) < 30:
        return None

    spread, zscore = calculate_spread(df, sym1, sym2)
    latest_z = zscore.iloc[-1]

    signal = None
    if latest_z > z_threshold:
        signal = {
            "pair": f"{sym1}/{sym2}",
            "type": "SELL Spread",
            "zscore": round(latest_z, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    elif latest_z < -z_threshold:
        signal = {
            "pair": f"{sym1}/{sym2}",
            "type": "BUY Spread",
            "zscore": round(latest_z, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return signal

def scan_pairs(pairs, z_threshold=2):
    print(f"📊 Scanning {len(pairs)} stock pairs for stat arb...")
    opportunities = []
    for sym1, sym2 in pairs:
        try:
            result = detect_stat_arb_opportunity(sym1, sym2, z_threshold)
            if result:
                opportunities.append(result)
                print(f"✅ Opportunity: {result}")
        except Exception as e:
            print(f⚠️ Error processing {sym1}/{sym2}: {e}")
    return opportunities

# Example Usage
if __name__ == "__main__":
    stock_pairs = [
        ("RELIANCE.NS", "ONGC.NS"),
        ("TCS.NS", "INFY.NS"),
        ("HDFCBANK.NS", "ICICIBANK.NS"),
        ("SBIN.NS", "PNB.NS"),
        ("LT.NS", "ADANIENT.NS"),
    ]
    results = scan_pairs(stock_pairs)
