# option_chain_utils.py – Option Signal Generator with Max Pain and Expiry Filters

import requests
import json
import datetime

NSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-IN',
    'Connection': 'keep-alive',
}

BASE_URL = "https://www.nseindia.com"
CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

def fetch_nse_option_chain(symbol="NIFTY"):
    try:
        session = requests.Session()
        session.headers.update(NSE_HEADERS)
        session.get(BASE_URL)
        response = session.get(CHAIN_URL.format(symbol=symbol.upper()))
        data = response.json()
        return data.get("records", {})
    except Exception as e:
        print("❌ Error fetching NSE option chain:", e)
        return {}

def calculate_max_pain(data):
    pain = {}
    for entry in data:
        strike = entry.get("strikePrice")
        ce_oi = entry.get("CE", {}).get("openInterest", 0)
        pe_oi = entry.get("PE", {}).get("openInterest", 0)
        total_pain = 0
        for inner in data:
            inner_strike = inner.get("strikePrice")
            inner_ce_oi = inner.get("CE", {}).get("openInterest", 0)
            inner_pe_oi = inner.get("PE", {}).get("openInterest", 0)
            total_pain += abs(strike - inner_strike) * (inner_ce_oi + inner_pe_oi)
        pain[strike] = total_pain
    return min(pain, key=pain.get) if pain else None

def parse_option_chain_data(data):
    ce_oi_total = 0
    pe_oi_total = 0
    ce_oi_change = 0
    pe_oi_change = 0
    option_signals = []

    all_data = data.get("data", [])
    expiry_dates = data.get("expiryDates", [])
    if not all_data or not expiry_dates:
        return [], 0, None

    # Use nearest expiry
    nearest_expiry = expiry_dates[0]
    filtered = [d for d in all_data if d.get("expiryDate") == nearest_expiry]

    # Max Pain
    max_pain = calculate_max_pain(filtered)

    for entry in filtered:
        strike = entry.get("strikePrice")
        ce = entry.get("CE", {})
        pe = entry.get("PE", {})

        ce_oi = ce.get("openInterest", 0)
        pe_oi = pe.get("openInterest", 0)
        ce_chg = ce.get("changeinOpenInterest", 0)
        pe_chg = pe.get("changeinOpenInterest", 0)

        ce_oi_total += ce_oi
        pe_oi_total += pe_oi
        ce_oi_change += ce_chg
        pe_oi_change += pe_chg

        # Signal logic
        if ce_oi > 0 and pe_oi > 0:
            signal_strength = round((pe_oi - ce_oi) / max(pe_oi, ce_oi) * 100, 2)
            if signal_strength > 20:
                option_signals.append({
                    "symbol": f"{strike} CE vs PE",
                    "type": "option",
                    "signalType": "Call Buy",
                    "strategyTags": ["OI Trend", "PCR > 1"],
                    "price": strike,
                    "volume": ce_oi,
                    "strength": signal_strength,
                    "sparkline": [],
                    "timeframe": "option",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            elif signal_strength < -20:
                option_signals.append({
                    "symbol": f"{strike} PE vs CE",
                    "type": "option",
                    "signalType": "Put Buy",
                    "strategyTags": ["OI Trend", "PCR < 1"],
                    "price": strike,
                    "volume": pe_oi,
                    "strength": abs(signal_strength),
                    "sparkline": [],
                    "timeframe": "option",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total else 0
    return option_signals, pcr, max_pain

def get_option_signals(symbol="NIFTY"):
    raw = fetch_nse_option_chain(symbol)
    if not raw:
        return []
    signals, pcr, max_pain = parse_option_chain_data(raw)
    print(f"✔ Option signals for {symbol} | PCR: {pcr} | Max Pain: {max_pain}")
    return {
        "signals": signals,
        "pcr": pcr,
        "max_pain": max_pain
    }
