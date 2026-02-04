from fastapi import Depends, Request
from simple_discord.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository, UserDataRepository
from simple_discord.app.services import ChatService, UserService
from simple_discord.app.db import UnitOfWorkFactory

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

def get_unit_of_work(dynamodb = Depends(get_dynamo_client)):
    return UnitOfWorkFactory(dynamodb)

def get_user_service(
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    user_data_repository: UserDataRepository = Depends(get_user_data_repository),
):
    return UserService(user_chat_repository=user_chat_repository, user_data_repository=user_data_repository)

def get_chat_service(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository),
    user_service: UserService = Depends(get_user_service),
    unit_of_work_factory = Depends(get_unit_of_work),

) -> ChatService:
    return ChatService(
        chat_history_repository=chat_history_repository, 
        user_chat_repository=user_chat_repository, 
        chat_data_repository=chat_data_repository, 
        user_service=user_service, 
        unit_of_work=unit_of_work_factory
    )