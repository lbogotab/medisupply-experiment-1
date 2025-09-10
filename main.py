from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/example', methods=['GET'])
def get_data():
    sample_data = {
        'id': 1,
        'name': 'Sample Item',
        'description': 'This is a sample item.'
    }
    return jsonify(sample_data), 201

@app.get("/")
def root():
    return jsonify({"ok": True, "service": "medisupply-dummy"}), 200

@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True)

# Test ROL AWS A