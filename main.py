from flask import Flask, jsonify, request
import os
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)

# Config DynamoDB: usa IRSA (sin keys); region explícita y nombre de tabla por ENV
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DDB_TABLE = os.environ.get("DDB_TABLE", "medisupply-demo")
ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = ddb.Table(DDB_TABLE)

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

# Crear/actualizar
@app.post("/items")
def put_item():
  data = request.get_json(force=True) or {}
  if "id" not in data:
    return jsonify({"error": "Campo 'id' es obligatorio"}), 400
  try:
    table.put_item(Item=data)
    return jsonify({"ok": True, "saved": data}), 201
  except ClientError as e:
    return jsonify({"ok": False, "error": e.response["Error"]}), 500

# Obtener un item por id
@app.get("/items/<item_id>")
def get_item(item_id):
  try:
    res = table.get_item(Key={"id": item_id})
    if "Item" not in res:
      return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify(res["Item"]), 200
  except ClientError as e:
    return jsonify({"ok": False, "error": e.response["Error"]}), 500

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8080, debug=True)

# Deploy Image
