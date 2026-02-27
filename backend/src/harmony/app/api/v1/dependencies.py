import uuid

from starlette.requests import HTTPConnection
from fastapi import Depends, HTTPException, status
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
    StreamService, 
    UserCommands, UserQueries, 
    ChatCommands, ChatQueries,
    MessageCommands, MessageQueries,
)
from harmony.app.core import decode_access_token

# ------------------------- Authentication Dependency ------------------------ #
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user_id

# --------------------------- Database Dependencies -------------------------- #
def get_dynamo_client(conn: HTTPConnection):
    return conn.app.state.dynamodb

async def get_db_session(conn: HTTPConnection):
    async with conn.app.state.session_factory() as session:
        yield session

# -------------------------- Repository Dependencies ------------------------- #
def get_chat_history_repository(dynamodb = Depends(get_dynamo_client)) -> ChatHistoryRepository:
    return ChatHistoryRepository(dynamodb)

def get_chat_data_repository(session: AsyncSession = Depends(get_db_session)) -> ChatDataRepository:
    return ChatDataRepository(session)

def get_user_data_repository(session: AsyncSession = Depends(get_db_session)) -> UserDataRepository:
    return UserDataRepository(session)

def get_user_chat_repository(session: AsyncSession = Depends(get_db_session)) -> UserChatRepository:
    return UserChatRepository(session)

def get_auth_repository(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session)

# ---------------------------- Stream Dependencies --------------------------- #
def get_redis_manager(conn: HTTPConnection):
    return conn.app.state.redis_manager

def get_ws_manager(conn: HTTPConnection):
    return conn.app.state.ws_manager

# --------------------------- Service Dependencies --------------------------- #
def get_user_queries(
    session: AsyncSession = Depends(get_db_session),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
) -> UserQueries:
    return UserQueries(session, user_data_repository, user_chat_repository)

def get_chat_queries(
    session: AsyncSession = Depends(get_db_session),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
) -> ChatQueries:
    return ChatQueries(session, chat_data_repository, user_chat_repository)

def get_message_queries(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    chat_queries: ChatQueries = Depends(get_chat_queries),
    user_queries: UserQueries = Depends(get_user_queries),
) -> MessageQueries:
    return MessageQueries(chat_history_repository, chat_queries, user_queries)

def get_user_commands(
    session: AsyncSession = Depends(get_db_session),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
) -> UserCommands:
    return UserCommands(session, user_data_repository, user_chat_repository)

def get_chat_commands(
    session: AsyncSession = Depends(get_db_session),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
) -> ChatCommands:
    return ChatCommands(session, chat_data_repository, user_chat_repository)

def get_message_commands(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    chat_queries: ChatQueries = Depends(get_chat_queries),
    user_queries: UserQueries = Depends(get_user_queries),
    event_publisher = Depends(get_redis_manager),
) -> MessageCommands:
    return MessageCommands(chat_history_repository, chat_queries, user_queries, event_publisher)

def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    user_commands: UserCommands = Depends(get_user_commands),
    user_queries: UserQueries = Depends(get_user_queries),
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(session, user_commands=user_commands, user_queries=user_queries, auth_repository=auth_repository) 

def get_stream_service(
    ws_manager = Depends(get_ws_manager),
    redis_manager = Depends(get_redis_manager),
    chat_queries: ChatQueries = Depends(get_chat_queries),
) -> StreamService:
    return StreamService(ws_manager, redis_manager, chat_queries)