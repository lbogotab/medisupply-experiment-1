from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_data():
    sample_data = {
        'id': 1,
        'name': 'Sample Item',
        'description': 'This is a sample item.'
    }
    return jsonify(sample_data), 201

if __name__ == '__main__':
    app.run(debug=True)