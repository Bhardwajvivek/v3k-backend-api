import subprocess
import threading
import time

def run_script(path):
    try:
        subprocess.run(["python", path])
    except Exception as e:
        print(f"Error running {path}: {e}")

def main():
    print("🚀 V3k Scheduler starting all modules...")

    # Define script paths
    scripts = [
        "app.py",
        "fast_order_executor.py",
        "signal_outcome_tracker.py"
    ]

    # Start each script in a separate thread
    for script in scripts:
        t = threading.Thread(target=run_script, args=(script,))
        t.start()
        time.sleep(2)

if __name__ == "__main__":
    main()
