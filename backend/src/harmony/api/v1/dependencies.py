import uuid
from aiokafka import AIOKafkaProducer
import jwt
from harmony.app.core import Settings
from starlette.requests import HTTPConnection
from fastapi import BackgroundTasks, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.security import OAuth2PasswordBearer

from harmony.app.repositories import (
    ChatHistoryRepository, 
    UserChatRepository, 
    ChatDataRepository, 
    UserDataRepository, 
    AuthRepository
)
from harmony.app.services import (
    AuthService, 
    PubSubService, 
    UserCommands, UserQueries,
    ChatCommands, ChatQueries,
    MessageCommands, MessageQueries,
    CacheService
)
from harmony.app.core import decode_access_token, get_settings, Settings

import structlog
logger = structlog.get_logger(__name__)

# ------------------------- Authentication Dependency ------------------------ #
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings)
) -> uuid.UUID:
    cfg = settings.auth
    try:
        payload = decode_access_token(
            token, 
            secret_key=cfg.secret_key.get_secret_value(), 
            algorithm=cfg.algorithm
        )
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired", token=token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logger.warning("invalid_token", token=token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user_id

async def get_user_from_cookie(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> str | None:
    cfg = settings.auth
    token = request.cookies.get(cfg.access_token_name)
    if not token:
        return None

    try:
        payload = decode_access_token(
            token, 
            secret_key=cfg.secret_key.get_secret_value(), 
            algorithm=cfg.algorithm
        )
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        logger.warning("invalid_ws_cookie_token")
        return None

# --------------------------- Database Dependencies -------------------------- #
def get_dynamo_client(conn: HTTPConnection):
    return conn.app.state.dynamodb

async def get_db_session(conn: HTTPConnection):
    async with conn.app.state.session_factory() as session:
        yield session

# -------------------------- Repository Dependencies ------------------------- #
def get_chat_history_repository(dynamodb = Depends(get_dynamo_client), settings: Settings = Depends(get_settings)) -> ChatHistoryRepository:
    return ChatHistoryRepository(dynamodb, dynamodb_config=settings.dynamodb)

def get_chat_data_repository(session: AsyncSession = Depends(get_db_session)) -> ChatDataRepository:
    return ChatDataRepository(session)

def get_user_data_repository(session: AsyncSession = Depends(get_db_session)) -> UserDataRepository:
    return UserDataRepository(session)

def get_user_chat_repository(session: AsyncSession = Depends(get_db_session)) -> UserChatRepository:
    return UserChatRepository(session)

def get_auth_repository(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session)

# ---------------------------- Stream Dependencies --------------------------- #
def get_redis_cache_client(conn: HTTPConnection, settings: Settings = Depends(get_settings)):
    return conn.app.state.redis_cache_client

def get_kafka_producer(conn: HTTPConnection):
    return conn.app.state.kafka_producer

# --------------------------- Service Dependencies --------------------------- #

def get_cache_service(redis_client = Depends(get_redis_cache_client)):
    if not redis_client: return None
    return CacheService(redis_client=redis_client)

def get_user_queries(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    cache_service: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
) -> UserQueries:
    return UserQueries(
        session=session, 
        user_data_repository=user_data_repository, 
        user_chat_repository=user_chat_repository, 
        cache_service=cache_service, 
        task_queue=background_tasks,
        cache_config=settings.cache
    )

def get_chat_queries(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    cache_service: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings)
) -> ChatQueries:
    return ChatQueries(
        session=session, 
        chat_data_repository=chat_data_repository, 
        user_chat_repository=user_chat_repository, 
        cache_service=cache_service, 
        task_queue=background_tasks,
        cache_config=settings.cache,
    )

def get_message_queries(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    chat_queries: ChatQueries = Depends(get_chat_queries),
    user_queries: UserQueries = Depends(get_user_queries),
) -> MessageQueries:
    return MessageQueries(
        chat_history_repository=chat_history_repository, 
        chat_queries=chat_queries, 
        user_queries=user_queries
    )

def get_pubsub_service(
    chat_queries: ChatQueries = Depends(get_chat_queries),
):
    return PubSubService(chat_queries=chat_queries)

def get_user_commands(
    session: AsyncSession = Depends(get_db_session),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
) -> UserCommands:
    return UserCommands(
        session=session, 
        user_data_repository=user_data_repository, 
        user_chat_repository=user_chat_repository, 
    )

def get_chat_commands(
    session: AsyncSession = Depends(get_db_session),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    settings: Settings = Depends(get_settings)
) -> ChatCommands:
    return ChatCommands(
        session=session, 
        chat_data_repository=chat_data_repository, 
        user_chat_repository=user_chat_repository, 
        chat_config=settings.chat
    )

def get_message_commands(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    chat_queries: ChatQueries = Depends(get_chat_queries),
    user_queries: UserQueries = Depends(get_user_queries),
    settings: Settings = Depends(get_settings),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer),
) -> MessageCommands:
    return MessageCommands(
        chat_history_repository=chat_history_repository, 
        chat_queries=chat_queries, 
        user_queries=user_queries, 
        publisher=kafka_producer, 
        chat_config=settings.chat,
    )

def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    user_commands: UserCommands = Depends(get_user_commands),
    user_queries: UserQueries = Depends(get_user_queries),
    auth_repository: AuthRepository = Depends(get_auth_repository),
    settings: Settings = Depends(get_settings)
) -> AuthService:
    return AuthService(
        session=session, 
        user_commands=user_commands, 
        user_queries=user_queries, 
        auth_repository=auth_repository,
        auth_config=settings.auth
    )