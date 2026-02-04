from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    DYNAMODB_ENDPOINT: str = "http://localhost:8000"
    CHAT_HISTORY_TABLE_NAME: str = "ChatHistory"
    USER_CHAT_TABLE_NAME: str = "UserChat"
    CHAT_DATA_TABLE_NAME: str = "ChatData"
    USER_DATA_TABLE_NAME: str = "UserData"

settings = Settings()