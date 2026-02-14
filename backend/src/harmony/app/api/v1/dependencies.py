from fastapi import Depends, HTTPException, Request, status

from fastapi.security import OAuth2PasswordBearer
from harmony.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository, UserDataRepository, EmailSetRepository
from harmony.app.services import ChatService, UserService, AuthService
from harmony.app.db import UnitOfWorkFactory
from harmony.app.core import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> str:
    payload = decode_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user_id

def get_dynamo_client(request: Request):
    return request.app.state.dynamodb

def get_chat_history_repository(dynamodb = Depends(get_dynamo_client)) -> ChatHistoryRepository:
    return ChatHistoryRepository(dynamodb)

def get_chat_data_repository(dynamodb = Depends(get_dynamo_client)) -> ChatDataRepository:
    return ChatDataRepository(dynamodb)

def get_user_data_repository(dynamodb = Depends(get_dynamo_client)) -> UserDataRepository:
    return UserDataRepository(dynamodb)

def get_user_chat_repository(dynamodb = Depends(get_dynamo_client)) -> UserChatRepository:
    return UserChatRepository(dynamodb)

def get_email_set_repository(dynamodb = Depends(get_dynamo_client)) -> EmailSetRepository:
    return EmailSetRepository(dynamodb)

def get_unit_of_work(dynamodb = Depends(get_dynamo_client)):
    return UnitOfWorkFactory(dynamodb)

def get_user_service(
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    email_set_repository: EmailSetRepository = Depends(get_email_set_repository),
    unit_of_work: UnitOfWorkFactory = Depends(get_unit_of_work)
):
    return UserService(
        user_chat_repository=user_chat_repository, 
        user_data_repository=user_data_repository, 
        email_set_repository=email_set_repository,
        unit_of_work=unit_of_work
    )

def get_chat_service(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_service: UserService = Depends(get_user_service),
    unit_of_work_factory: UnitOfWorkFactory = Depends(get_unit_of_work),

) -> ChatService:
    return ChatService(
        chat_history_repository=chat_history_repository, 
        user_chat_repository=user_chat_repository, 
        chat_data_repository=chat_data_repository, 
        user_service=user_service, 
        unit_of_work=unit_of_work_factory
    )

def get_auth_service(
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
    unit_of_work_factory: UnitOfWorkFactory = Depends(get_unit_of_work)
):
    return AuthService(user_data_repository=user_data_repository, unit_of_work=unit_of_work_factory)