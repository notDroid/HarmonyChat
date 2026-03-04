import aioboto3
from contextlib import asynccontextmanager
from ..settings import get_settings, DynamoDBConfig, AWSConfig

async def init_dynamodb(app, stack):
    """
    Initializes the DynamoDB client and stores it in app.state.
    """
    settings = get_settings()
    if not settings.features.dynamodb:
        return

    dynamodb_client = await stack.enter_async_context(dynamodb_connector(settings.dynamodb, settings.aws))
    app.state.dynamodb = dynamodb_client

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
        aws_access_key_id=aws_cfg.access_key_id,
        aws_secret_access_key=aws_cfg.secret_access_key
    ) as client:
        yield client