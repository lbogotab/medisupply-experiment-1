import os

class Config:
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DDB_TABLE  = os.getenv("DDB_TABLE",  "medisupply-testing")
    # SQS
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
    ENABLE_SQS_PUBLISH = os.getenv("ENABLE_SQS_PUBLISH", "false").lower() == "true"