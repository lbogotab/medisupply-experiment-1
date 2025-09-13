import boto3
from flask import current_app

def get_sqs_client():
    url = current_app.config["SQS_QUEUE_URL"]
    if not url:
        return None, ""
    client = boto3.client("sqs", region_name=current_app.config["AWS_REGION"])
    return client, url