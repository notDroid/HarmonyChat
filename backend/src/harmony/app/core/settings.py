from pydantic_settings import BaseSettings
from pydantic import BaseModel

class RedisOptions(BaseModel):
    health_check_interval: int = 30
    retry_retries: int = 3
    retry_cap: int = 10
    retry_base: int = 1

class Settings(BaseSettings):
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    # DynamoDB Configuration
    DYNAMODB_ENDPOINT: str = "http://localhost:8080"

    CHAT_HISTORY_TABLE_NAME: str = "ChatHistory"
    USER_CHAT_TABLE_NAME: str = "UserChat"
    CHAT_DATA_TABLE_NAME: str = "ChatData"
    USER_DATA_TABLE_NAME: str = "UserData"
    EMAIL_SET_TABLE_NAME: str = "EmailSet"

    # Authentication Configuration
    SECRET_KEY: str = "64d54ec76be75e906e03e3fba806e2c1ff5f8da12dfb9226e7eea2a72e477c96" # temporary hardcoded key for dev. in prod we set it with a env variable.
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Redis Configuration
    REDIS_CONNECT: bool = True
    REDIS_LISTEN: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STALL_TIMEOUT: float = 0.001 # Block for 1ms while stalling for messages.
    redis_opts: RedisOptions = RedisOptions()

settings = Settings()