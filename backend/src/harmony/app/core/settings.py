from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    # DynamoDB Configuration
    DYNAMODB_ENDPOINT: str = "http://localhost:8000"

    CHAT_HISTORY_TABLE_NAME: str = "ChatHistory"
    USER_CHAT_TABLE_NAME: str = "UserChat"
    CHAT_DATA_TABLE_NAME: str = "ChatData"
    USER_DATA_TABLE_NAME: str = "UserData"

    # Authentication Configuration
    SECRET_KEY: str = "temporary_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

settings = Settings()