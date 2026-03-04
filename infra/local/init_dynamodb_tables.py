import os
import json
import boto3
import botocore.exceptions

# --------- CONFIGURATION ---------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
TABLE_FILE = os.getenv("TABLE_FILE", "dynamodb-tables.json")

# --------- CREATE TABLES ---------
def create_tables(dynamodb, table_file):
    with open(table_file, "r") as f:
        table_schemas = json.load(f)
    
    for table_name, table_params in table_schemas.items():
        try:
            print(f"Creating {table_name}...")
            table = dynamodb.create_table(**table_params)
            
            # Only wait if we actually triggered a creation
            print(f"Waiting for {table_name} to become active...")
            table.wait_until_exists()
            print(f"Table {table_name} created successfully.")
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {table_name} already exists. Skipping.")
            else:
                # Re-raise other unexpected errors
                print(f"Unexpected error creating {table_name}")
                raise e
            
def init_db():
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
    )
    create_tables(dynamodb, TABLE_FILE)
