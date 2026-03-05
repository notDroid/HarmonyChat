from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureToggles(BaseModel):
    """Flags to enable or disable specific architectural components."""
    postgres: bool = Field(default=False, description="Enable PostgreSQL database integration")
    dynamodb: bool = Field(default=False, description="Enable AWS DynamoDB integration")
    cache_redis: bool = Field(default=False, description="Enable Redis caching")
    kafka: bool = Field(default=False, description="Enable Kafka message brokering")


class DynamoDBConfig(BaseModel):
    """Configuration for AWS DynamoDB."""
    url: str = Field(default="http://localhost:8080", description="Endpoint URL for DynamoDB")
    chat_history_table_name: str = Field(default="ChatHistory", description="Table name for chat history storage")


class ChatConfig(BaseModel):
    """Configuration for chat-related limits and queues."""
    max_users_per_operation: int = Field(default=10, ge=1, description="Maximum number of users processed per batch")
    default_pagination_limit: int = Field(default=50, ge=1, description="Default item limit for paginated chat endpoints")
    message_topic: str = Field(default="chat_messages", description="Topic name for chat messages")


class UserConfig(BaseModel):
    """Configuration for user-related domains."""
    default_user_search_limit: int = Field(default=10, ge=1, description="Default limit for user search queries")


class AWSConfig(BaseModel):
    """AWS SDK Client Configuration."""
    region: str = Field(default="us-east-1", description="Primary AWS region")
    default_region: str = Field(default="us-east-1", description="Fallback AWS region")
    access_key_id: SecretStr = Field(default=SecretStr("test"), description="AWS Access Key ID")
    secret_access_key: SecretStr = Field(default=SecretStr("test"), description="AWS Secret Access Key")


class AuthConfig(BaseModel):
    """JWT and Authentication Configuration."""
    secret_key: SecretStr = Field(
        default=SecretStr("64d54ec76be75e906e03e3fba806e2c1ff5f8da12dfb9226e7eea2a72e477c96"),
        description="Secret key for signing JWTs. Must be overridden in production."
    )
    algorithm: str = Field(default="HS256", description="Algorithm used to sign JWTs")
    
    access_token_name: str = Field(default="access_token", description="Cookie or header name for the access token")
    access_token_expire_minutes: int = Field(default=15, ge=1, description="Access token lifespan in minutes")
    
    refresh_token_name: str = Field(default="refresh_token", description="Cookie or header name for the refresh token")
    refresh_token_expire_days: int = Field(default=7, ge=1, description="Refresh token lifespan in days")
    refresh_token_grace_period_seconds: int = Field(default=2, ge=0, description="Grace period to prevent race conditions during refresh")


class CacheConfig(BaseModel):
    """Time-to-Live (TTL) settings for various cache layers."""
    default_ttl_seconds: int = Field(default=300, ge=0, description="Fallback TTL for cached items")
    membership_ttl_seconds: int = Field(default=300, ge=0, description="TTL for user group/membership cache")
    chat_metadata_ttl_seconds: int = Field(default=300, ge=0, description="TTL for chat metadata cache")
    user_ttl_seconds: int = Field(default=300, ge=0, description="TTL for user profile cache")


class RedisConfig(BaseModel):
    """Redis connection and health configuration."""
    url: str = Field(default="redis://localhost:6379/1", description="Redis connection string")
    health_check_interval: int = Field(default=30, ge=0, description="Interval in seconds between Redis health checks")
    request_timeout_ms: int = Field(default=100, ge=0, description="Timeout for Redis operations in milliseconds")


class PostgresConfig(BaseModel):
    """PostgreSQL connection configuration."""
    url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/harmony", 
        description="Async connection string for PostgreSQL"
    )


class KafkaConfig(BaseModel):
    """Kafka producer/consumer configuration."""
    bootstrap_servers: str = Field(default="localhost:9092", description="Comma-separated Kafka brokers")
    retry_backoff_ms: int = Field(default=500, ge=0, description="Milliseconds to wait before retrying a failed Kafka operation")


class Settings(BaseSettings):
    """
    Main Application Settings.
    """
    # App Metadata
    project_name: str = Field(default="Harmony API", description="Name of the FastAPI application")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", 
        description="Current application environment"
    )
    debug: bool = Field(default=True, description="Enable or disable FastAPI debug mode")
    
    # Nested Configurations
    features: FeatureToggles = FeatureToggles()
    chat: ChatConfig = ChatConfig()
    user: UserConfig = UserConfig()
    auth: AuthConfig = AuthConfig()
    cache: CacheConfig = CacheConfig()

    # Infrastructure Configurations
    redis: RedisConfig = RedisConfig()
    aws: AWSConfig = AWSConfig()
    dynamodb: DynamoDBConfig = DynamoDBConfig()
    postgres: PostgresConfig = PostgresConfig()
    kafka: KafkaConfig = KafkaConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__", 
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()