from flask import Blueprint, jsonify, request
from botocore.exceptions import ClientError
from app.clients.dynamo import get_table
from app.clients.sqs import get_sqs_client

bp = Blueprint("items", __name__)

@bp.get("/")
def root():
    return jsonify({"ok": True, "service": "medisupply-dummy"}), 200

@bp.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200

@bp.get("/example")
def get_data():
    sample_data = {
        'id': 1,
        'name': 'Sample Item',
        'description': 'Refactored to use Blueprints'
    }
    return jsonify(sample_data), 201

@bp.post("/items")
def put_item():
    data = request.get_json(force=True) or {}
    if "id" not in data:
        return jsonify({"error": "Campo 'id' es obligatorio"}), 400
    try:
        # 1) Guardar en Dynamo
        table = get_table()
        table.put_item(Item=data)

        # 2) (Opcional) Publicar a SQS si está habilitado
        queued = None
        from flask import current_app
        if current_app.config["ENABLE_SQS_PUBLISH"]:
            sqs, url = get_sqs_client()
            if sqs and url:
                try:
                    payload = {
                        "type": "order_created",
                        "id": data["id"],
                        "payload": data,
                    }
                    sqs.send_message(QueueUrl=url, MessageBody=jsonify(payload).data.decode())
                    queued = True
                except Exception:
                    queued = False

        return jsonify({"ok": True, "saved": data, "queued": queued}), 201
    except ClientError as e:
        return jsonify({"ok": False, "error": e.response.get("Error")}), 500

@bp.get("/items/<item_id>")
def get_item(item_id):
    try:
        table = get_table()
        res = table.get_item(Key={"id": item_id})
        if "Item" not in res:
            return jsonify({"ok": False, "error": "not_found"}), 404
        return jsonify(res["Item"]), 200
    except ClientError as e:
        return jsonify({"ok": False, "error": e.response.get("Error")}), 500