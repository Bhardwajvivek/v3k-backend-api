from flask import Flask, jsonify
from flask_cors import CORS
from strategies import generate_signals
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/get-signals')
def get_signals():
    try:
        # Load stock symbols from CSV (or hardcode temporarily)
        df = pd.read_csv("nifty.csv")
        symbols = df["Symbol"].tolist()

        signals = generate_signals(symbols)
        return jsonify({ "signals": signals })
    except Exception as e:
        print("Error in /get-signals:", str(e))
        return jsonify({ "signals": [] })

if __name__ == '__main__':
    app.run(debug=True)
