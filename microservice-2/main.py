from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/sales")
def home():
    return "microservice 2"

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
