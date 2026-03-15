import sys
sys.path.append("infra/scripts")

import os
from init_connector import register_connector
from init_dynamodb import init_dynamodb

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")
TABLE_FILE = os.getenv("TABLE_FILE")

CONNECT_URL = os.getenv("KAFKA_CONNECT_URL")
DYNAMODB_SINK_CONFIG_FILE = os.getenv("DYNAMODB_SINK_CONFIG_FILE")
DEBEZIUM_SOURCE_CONFIG_FILE = os.getenv("DEBEZIUM_SOURCE_CONFIG_FILE")

if __name__ == "__main__":
    register_connector(connect_url=CONNECT_URL, config_file=DYNAMODB_SINK_CONFIG_FILE)
    register_connector(connect_url=CONNECT_URL, config_file=DEBEZIUM_SOURCE_CONFIG_FILE)
    init_dynamodb(dynamodb_endpoint=DYNAMODB_ENDPOINT, aws_region=AWS_REGION, table_file=TABLE_FILE)