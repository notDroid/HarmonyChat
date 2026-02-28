import aioboto3
from contextlib import asynccontextmanager
from harmony.app.core import settings

async def init_dynamodb(app, stack):
    """
    Initializes the DynamoDB client and stores it in app.state.
    """
    if not settings.ENABLE_DYNAMODB:
        return

    dynamodb_client = await stack.enter_async_context(dynamodb_connector())
    app.state.dynamodb = dynamodb_client

@asynccontextmanager
async def dynamodb_connector():
    """
    Context manager that yields an authenticated DynamoDB client.
    """
    session = aioboto3.Session()
    
    async with session.client(
        'dynamodb',
        endpoint_url=settings.DYNAMODB_ENDPOINT,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    ) as client:
        yield client