from fastapi import Depends, Request
from simple_discord.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository, UserDataRepository
from simple_discord.app.services import ChatService

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

def get_chat_service(
    chat_history_repository: ChatHistoryRepository = Depends(get_chat_history_repository),
    user_chat_repository: UserChatRepository = Depends(get_user_chat_repository),
    chat_data_repository: ChatDataRepository = Depends(get_chat_data_repository)
) -> ChatService:
    return ChatService(chat_history_repository, user_chat_repository, chat_data_repository)