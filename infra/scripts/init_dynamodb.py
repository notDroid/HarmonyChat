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
            
def init_dynamodb(dynamodb_endpoint, table_file, aws_region="us-east-1"):
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=dynamodb_endpoint,
        region_name=aws_region,
    )
    create_tables(dynamodb, table_file)
