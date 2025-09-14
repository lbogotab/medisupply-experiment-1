import os
import json
from flask import Flask, jsonify, request
import boto3
from botocore.exceptions import BotoCoreError, ClientError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DDB_TABLE_MIRROR = os.getenv("DDB_TABLE_MIRROR", "medisupply-demo-mirror")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DDB_TABLE_MIRROR)

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "micro3-products", "table": DDB_TABLE_MIRROR})

@app.get("/products/example")
def get_example_product():
    example_product = {
        "id": "example",
        "name": "Example Product",
        "description": "This is an example product",
        "price": 9.99
    }
    return jsonify({"ok": True, "item": example_product})

@app.get("/products/items/<item_id>")
def get_item(item_id: str):
    try:
        resp = table.get_item(Key={"id": item_id})
        if "Item" not in resp:
            return jsonify({"ok": False, "error": "NOT_FOUND", "id": item_id}), 404
        return jsonify({"ok": True, "item": resp["Item"]})
    except (BotoCoreError, ClientError) as e:
        return jsonify({"ok": False, "error": "DDB_ERROR", "detail": str(e)}), 500

#Lectura simple paginada (Scan). Solo pruebas
@app.get("/products/items/all")
def get_items_paginated():
    try:
        limit = int(request.args.get("limit", "25"))
        start_key_raw = request.args.get("start_key")
        kwargs = {"Limit": limit}
        if start_key_raw:
            kwargs["ExclusiveStartKey"] = json.loads(start_key_raw)

        resp = table.scan(**kwargs)
        out = {
            "ok": True,
            "count": resp.get("Count", 0),
            "items": resp.get("Items", []),
        }
        lek = resp.get("LastEvaluatedKey")
        if lek:
            out["next_start_key"] = json.dumps(lek)
        return jsonify(out)
    except (ValueError, BotoCoreError, ClientError) as e:
        return jsonify({"ok": False, "error": "SCAN_ERROR", "detail": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)