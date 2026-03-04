from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class FeatureToggles(BaseModel):
    postgres: bool = False
    dynamodb: bool = False
    cache_redis: bool = False
    event_handlers: bool = False
    kafka: bool = False

class DynamoDBConfig(BaseModel):
    url: str = "http://localhost:8080"
    chat_history_table_name: str = "ChatHistory"

class ChatConfig(BaseModel):
    max_users_per_operation: int = 10
    default_pagination_limit: int = 50
    message_topic: str = "chat_messages"

class UserConfig(BaseModel):
    default_user_search_limit: int = 10

class AWSConfig(BaseModel):
    region: str = "us-east-1"
    default_region: str = "us-east-1"
    access_key_id: str = "test"
    secret_access_key: str = "test"

class AuthConfig(BaseModel):
    # temporary hardcoded key for dev. in prod we set it with a env variable.
    secret_key: str = "64d54ec76be75e906e03e3fba806e2c1ff5f8da12dfb9226e7eea2a72e477c96" 
    algorithm: str = "HS256"
    access_token_name: str = "access_token"
    access_token_expire_minutes: int = 15
    refresh_token_name: str = "refresh_token"
    refresh_token_expire_days: int = 7
    refresh_token_grace_period_seconds: int = 2

class CacheConfig(BaseModel):
    default_ttl_seconds: int = 300
    membership_ttl_seconds: int = 300
    chat_metadata_ttl_seconds: int = 300
    user_ttl_seconds: int = 300

class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/1"
    health_check_interval: int = 30

class PostgresConfig(BaseModel):
    url: str = "postgresql+asyncpg://user:password@localhost:5432/harmony"

class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    retry_backoff_ms: int = 500

class Settings(BaseSettings):
    app_env: str = "development"
    
    features: FeatureToggles = FeatureToggles()

    chat: ChatConfig = ChatConfig()
    user: UserConfig = UserConfig()
    auth: AuthConfig = AuthConfig()
    cache: CacheConfig = CacheConfig()

    redis: RedisConfig = RedisConfig()
    aws: AWSConfig = AWSConfig()
    dynamodb: DynamoDBConfig = DynamoDBConfig()
    postgres: PostgresConfig = PostgresConfig()
    kafka: KafkaConfig = KafkaConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__", 
        case_sensitive=False
    )

@lru_cache
def get_settings() -> Settings:
    """
    Creates and caches the Settings object. 
    Using lru_cache ensures we don't read the .env file on every request.
    """
    return Settings()