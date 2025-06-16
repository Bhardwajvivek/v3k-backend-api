from flask import Flask, jsonify
from nsepython import nse_get_index_quote

app = Flask(__name__)

@app.route('/get-signals')
def get_signals():
    try:
        quote = nse_get_index_quote("NIFTY 50")
        return jsonify({"index": quote}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
