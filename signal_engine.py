# signal_engine.py

import traceback
from utils import (
    get_live_stock_data,
    calculate_technical_indicators,
    analyze_stock_signals,
    calculate_performance_metrics,
    generate_live_option_signals,
    generate_live_scalping_signals,
    is_market_open
)
from alerts import send_telegram_alert_internal
from constants import NIFTY_50_SYMBOLS
from datetime import datetime
import time as time_module

# Global signal cache and state
cached_signals = []
cached_options = []
cached_scalping = []
last_scan_time = None

class BotState:
    def __init__(self):
        self.cached_signals = []
        self.cached_options = []
        self.cached_scalping = []
        self.last_scan_time = None
        self.performance_metrics = {}
        self.scan_status = "idle"

bot_state = BotState()

def get_signal_data():
    return {
        "signals": cached_signals,
        "options": cached_options,
        "scalping": cached_scalping,
        "last_scan_time": last_scan_time,
        "status": bot_state.scan_status,
        "metrics": bot_state.performance_metrics
    }

def background_scanner():
    """LIVE background scanner that generates real-time signals"""
    global cached_signals, cached_options, cached_scalping, last_scan_time, bot_state

    while True:
        try:
            print("🔄 Starting LIVE signal scan...")
            current_time = datetime.now()
            market_open = is_market_open()

            bot_state.scan_status = "scanning"

            equity_signals = []
            symbols_to_scan = NIFTY_50_SYMBOLS[:12]  # Optimize for speed

            print(f"📊 Scanning {len(symbols_to_scan)} symbols...")
            for symbol in symbols_to_scan:
                try:
                    data = get_live_stock_data(symbol, period="5d", interval="15m")
                    if data is not None:
                        indicators = calculate_technical_indicators(data)
                        signals = analyze_stock_signals(symbol, indicators)
                        equity_signals.extend(signals)
                        if signals:
                            print(f"✅ {symbol}: {len(signals)} signals")
                except Exception as e:
                    print(f"❌ Error scanning {symbol}: {e}")

            print("🟢 Generating live option signals...")
            option_signals = generate_live_option_signals()

            print("🔵 Generating live scalping signals...")
            scalping_signals = generate_live_scalping_signals()

            # Sort by strength
            equity_signals = sorted(equity_signals, key=lambda x: x.get('strength', 0), reverse=True)[:10]
            option_signals = sorted(option_signals, key=lambda x: x.get('strength', 0), reverse=True)[:6]
            scalping_signals = sorted(scalping_signals, key=lambda x: x.get('strength', 0), reverse=True)[:8]

            # Update caches
            cached_signals = equity_signals
            cached_options = option_signals
            cached_scalping = scalping_signals
            last_scan_time = current_time

            bot_state.cached_signals = equity_signals
            bot_state.cached_options = option_signals
            bot_state.cached_scalping = scalping_signals
            bot_state.last_scan_time = current_time
            bot_state.scan_status = "completed"
            bot_state.performance_metrics = calculate_performance_metrics(equity_signals + option_signals + scalping_signals)

            print(f"✅ Scan completed - Equity: {len(equity_signals)}, Options: {len(option_signals)}, Scalping: {len(scalping_signals)}")

            # High priority alert logic
            try:
                high_priority = [s for s in equity_signals + option_signals + scalping_signals if s.get('strength', 0) >= 85]
                for sig in high_priority[:2]:
                    try:
                        send_telegram_alert_internal(sig)
                        print(f"📢 Alert sent for {sig['symbol']} (Strength: {sig['strength']})")
                    except Exception as e:
                        print(f"❌ Alert send error: {e}")
            except Exception as e:
                print(f"❌ High-priority alert logic error: {e}")

        except Exception as e:
            print(f"❌ Background scanner error: {e}")
            print(traceback.format_exc())
            bot_state.scan_status = "error"

        # Sleep before next scan
        time_module.sleep(30 if market_open else 120)
