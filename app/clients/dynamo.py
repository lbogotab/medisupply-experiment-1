import boto3
from flask import current_app

def get_table():
    region = current_app.config["AWS_REGION"]
    table_name = current_app.config["DDB_TABLE"]
    ddb = boto3.resource("dynamodb", region_name=region)
    return ddb.Table(table_name)