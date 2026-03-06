import aioboto3
from contextlib import asynccontextmanager
from harmony.app.core import DynamoDBConfig, AWSConfig

@asynccontextmanager
async def dynamodb_connector(dynamodb_cfg: DynamoDBConfig, aws_cfg: AWSConfig):
    """
    Context manager that yields an authenticated DynamoDB client.
    """
    session = aioboto3.Session()
    
    async with session.client(
        'dynamodb',
        endpoint_url=dynamodb_cfg.url,
        region_name=aws_cfg.default_region,
        aws_access_key_id=aws_cfg.access_key_id.get_secret_value(),
        aws_secret_access_key=aws_cfg.secret_access_key.get_secret_value()
    ) as client:
        yield client