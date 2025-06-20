# option_chain_utils.py
# Utility for fetching Option Chain data and generating option trade signals

import requests
import json
import datetime

NSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Accept-Language': 'en-IN',
    'Connection': 'keep-alive',
}

NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"


def fetch_nse_option_chain(symbol="NIFTY"):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol.upper()}"
        session = requests.Session()
        session.headers.update(NSE_HEADERS)
        # First request to get cookies
        session.get("https://www.nseindia.com")
        response = session.get(url)
        data = response.json()
        return data.get('records', {}).get('data', [])
    except Exception as e:
        print("Error fetching NSE option chain:", e)
        return []


def parse_option_chain_data(data):
    ce_oi_total = 0
    pe_oi_total = 0
    ce_oi_change = 0
    pe_oi_change = 0
    max_pain = None
    option_signals = []

    for entry in data:
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
    return option_signals, pcr


def get_option_signals(symbol="NIFTY"):
    raw_data = fetch_nse_option_chain(symbol)
    if not raw_data:
        return []
    signals, pcr = parse_option_chain_data(raw_data)
    print(f"✔ Fetched option signals for {symbol} | PCR: {pcr}")
    return signals
