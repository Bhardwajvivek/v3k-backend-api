from flask import Flask, jsonify
from flask_cors import CORS
from strategies import generate_all_signals

app = Flask(__name__)
CORS(app)

@app.route("/get-signals", methods=["GET"])
def get_signals():
    try:
        signals = generate_all_signals()
        return jsonify({"status": "success", "data": signals})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/")
def home():
    return "V3k AI Trading Bot API is live."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
