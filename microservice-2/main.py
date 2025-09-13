from flask import Flask, jsonify
import os
import json
import threading
import time
import signal
import sys

# SQS (opcional): el worker se enciende solo si hay URL
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/726264870413/medisupply-events")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
WAIT_TIME     = int(os.getenv("SQS_WAIT_TIME", "20"))          # long polling
MAX_MESSAGES  = int(os.getenv("SQS_MAX_MESSAGES", "10"))         # 1..10
VISIBILITY    = int(os.getenv("SQS_VISIBILITY_TIMEOUT", "60"))  # > tiempo de proceso

app = Flask(__name__)

worker_thread = None
stop_event = threading.Event()

@app.route("/sales")
def home():
    return "microservice 2"

@app.route("/health")
def health():
    # Señal simple de vida; opcionalmente podrías exponer métricas del worker aquí
    status = {
        "status": "healthy",
        "sqs_enabled": bool(SQS_QUEUE_URL),
        "queue_url": SQS_QUEUE_URL if bool(SQS_QUEUE_URL) else None,
    }
    return jsonify(status), 200


def _sqs_worker_loop():
    #Hilo en segundo plano que hace polling a SQS y procesa mensajes.
    if not SQS_QUEUE_URL:
        print("[sales-worker] SQS_QUEUE_URL no definido; worker apagado", file=sys.stderr)
        return

    try:
        import boto3
        from botocore.config import Config
    except Exception as e:
        print(f"[sales-worker] boto3 no disponible: {e}", file=sys.stderr)
        return

    sqs = boto3.client(
        "sqs",
        region_name=AWS_REGION,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )

    print(f"[sales-worker] Escuchando cola: {SQS_QUEUE_URL}")

    while not stop_event.is_set():
        try:
            resp = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=MAX_MESSAGES,
                WaitTimeSeconds=WAIT_TIME,
                VisibilityTimeout=VISIBILITY,
            )
            messages = resp.get("Messages", [])
            if not messages:
                # Espera cuando no hay mensajes
                time.sleep(0.5)
                continue

            for m in messages:
                receipt = m["ReceiptHandle"]
                body_raw = m.get("Body", "{}")
                try:
                    body = json.loads(body_raw)
                except Exception:
                    body = {"_raw": body_raw}

                # Lógica de negocio simulada
                print(f"[sales-worker] Procesando mensaje: {body}")
                time.sleep(1)  # Simula trabajo

                # Borrar el mensaje de la cola
                try:
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
                except Exception as e:
                    print(f"[sales-worker] Error al borrar mensaje: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[sales-worker] Error en receive loop: {e}", file=sys.stderr)
            time.sleep(1)


def _start_worker_once():
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=_sqs_worker_loop, daemon=True)
        worker_thread.start()


def _graceful_stop(*_args):
    stop_event.set()


# Arranque del worker antes de exponer HTTP
_start_worker_once()
signal.signal(signal.SIGTERM, _graceful_stop)
signal.signal(signal.SIGINT, _graceful_stop)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
