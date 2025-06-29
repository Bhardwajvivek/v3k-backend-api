import random
import numpy as np
import json
from datetime import datetime

# Define available strategies
strategies = [
    "MACD + RSI", "Supertrend + Pivot", "Volume Spike + EMA Crossover",
    "Momentum Ignition", "LSTM Forecast + MACD", "EMA 8/20 + MA200", "News Sentiment + Breakout"
]

# Simulated reward tracker (could also load from history)
strategy_performance = {s: {"wins": 0, "losses": 0} for s in strategies}

def simulate_trade_result(strategy_name):
    """
    Simulates a trade result for a given strategy.
    Returns 'win' or 'loss' based on weighted logic.
    """
    # Give some bias for popular / trusted strategies
    base_prob = 0.6 if "MACD" in strategy_name or "Supertrend" in strategy_name else 0.5

    # Random modifier for variation
    variation = random.uniform(-0.15, 0.15)
    win_probability = base_prob + variation

    result = "win" if random.random() < win_probability else "loss"

    # Update the stats
    if strategy_name in strategy_performance:
        if result == "win":
            strategy_performance[strategy_name]["wins"] += 1
        else:
            strategy_performance[strategy_name]["losses"] += 1

    return result

def run_rl_simulation(cycles=100):
    """
    Runs the RL logic for N cycles and logs outcomes.
    """
    for _ in range(cycles):
        strategy = random.choice(strategies)
        outcome = simulate_trade_result(strategy)

    print("✅ RL Simulation Complete.")
    print("📊 Final Performance Summary:")
    for s, stats in strategy_performance.items():
        total = stats['wins'] + stats['losses']
        winrate = (stats['wins'] / total * 100) if total > 0 else 0
        print(f"→ {s}: {stats['wins']}W / {stats['losses']}L (Winrate: {winrate:.1f}%)")

def get_best_strategies(threshold=60):
    """
    Returns strategies with winrate above threshold.
    """
    best = []
    for s, stats in strategy_performance.items():
        total = stats["wins"] + stats["losses"]
        if total == 0:
            continue
        winrate = (stats["wins"] / total) * 100
        if winrate >= threshold:
            best.append({"strategy": s, "winrate": round(winrate, 2)})
    return best

def save_rl_report():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"rl_report_{now}.json", "w") as f:
        json.dump(strategy_performance, f, indent=4)
    print(f"📁 Saved RL performance report: rl_report_{now}.json")

# Test
if __name__ == "__main__":
    run_rl_simulation(150)
    print("\n📌 Recommended Strategies:")
    print(get_best_strategies(threshold=60))
    save_rl_report()
