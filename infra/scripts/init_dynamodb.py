# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "boto3",
# ]
# ///

import os
import json
import boto3
import botocore.exceptions

def create_tables(dynamodb, table_file):
    with open(table_file, "r") as f:
        table_schemas = json.load(f)
    
    for table_name, table_params in table_schemas.items():
        try:
            print(f"Creating {table_name}...")
            table = dynamodb.create_table(**table_params)
            
            print(f"Waiting for {table_name} to become active...")
            table.wait_until_exists()
            print(f"Table {table_name} created successfully.")
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {table_name} already exists. Skipping.")
            else:
                print(f"Unexpected error creating {table_name}")
                raise e
            
if __name__ == "__main__":
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    dynamodb_endpoint = os.getenv("DYNAMODB_ENDPOINT")
    table_file = os.getenv("TABLE_FILE")

    print(f"Connecting to DynamoDB at {dynamodb_endpoint}...")
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=dynamodb_endpoint,
        region_name=aws_region,
    )
    create_tables(dynamodb, table_file)