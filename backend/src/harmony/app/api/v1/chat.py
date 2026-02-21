import asyncio
from fastapi import Depends, BackgroundTasks, APIRouter, status, HTTPException, Request
from harmony.app.core import settings
from harmony.app.schemas import (
    ChatCreateRequest, 
    ChatCreatedResponse, 
    MessageSendRequest, 
    ChatMessage, 
    ChatHistoryResponse
)
from .dependencies import get_chat_service, get_current_user

# 1. We define common error responses once to keep code clean
common_chat_errors = {
    401: {"description": "Authentication credentials were not provided or are invalid."},
    404: {"description": "Chat not found"},
    403: {"description": "User is not a participant of this chat"},
}

router = APIRouter()

@router.post(
    "/", 
    response_model=ChatCreatedResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat",
    responses={
        400: {"description": "Invalid user list (duplicates or too many users)."},
        401: {"description": "Authentication credentials were not provided or are invalid."},
        404: {"description": "One or more target users do not exist."}
    }
)
async def create_chat(
    data: ChatCreateRequest,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    """
    Creates a new chat room between the current user and a list of target users.
    
    - **user_id_list**: A list of user_ids for the users to include.
    - **Constraints**: 
        - Max 10 users per chat (initially, you can add more later).
        - You cannot create a chat with non-existent users.
        - The creator is automatically added to the chat.
    """
    chat_id = await chat_service.create_chat(
        user_id=user_id,
        user_id_list=data.user_id_list,
    )
    return ChatCreatedResponse(chat_id=chat_id)

@router.post(
    "/{chat_id}", 
    response_model=ChatMessage, 
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    responses=common_chat_errors
)
async def send_message(
    chat_id: str,
    data: MessageSendRequest, 
    request: Request, # TODO: Refactor to avoid tight coupling with FastAPI request object
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    """
    Persist a message to the database for a specific chat.
    
    Returns the message details including the generated ULID and timestamp.
    """
    msg = await chat_service.send_message(
        chat_id=chat_id, 
        user_id=user_id, 
        content=data.content,
        client_uuid=data.client_uuid
    )

    # Simulate timeout for testing purposes
    await asyncio.sleep(5)
    # TODO: Merge into chat service and use dependency injection for Redis manager to avoid tight coupling with FastAPI request
    redis_manager = request.app.state.redis_manager
    await redis_manager.publish(chat_id, msg.model_dump())

    return ChatMessage.model_validate(msg.model_dump())

@router.get(
    "/{chat_id}", 
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Retrieves all messages for a specific chat. Messages are sorted by ULID (chronologically).",
    responses=common_chat_errors
)
async def get_chat_history(
    chat_id: str,
    limit: int = settings.DEFAULT_PAGINATION_LIMIT,
    cursor: str | None = None,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    # Simulate timeout for testing purposes
    # await asyncio.sleep(5)
    messages, next_cursor = await chat_service.get_chat_history(user_id=user_id, chat_id=chat_id, limit=limit, cursor=cursor)
    return ChatHistoryResponse(messages=messages, next_cursor=next_cursor)

@router.delete(
    "/{chat_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat",
    responses=common_chat_errors
)
async def delete_chat(
    chat_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service),
):
    """
    **Hard deletes** a chat and all its associated history.
    
    - This operation performs a 'soft' check immediately.
    - The actual deletion of thousands of messages happens in a **Background Task** 
      to prevent the API from hanging.
    """
    await chat_service.delete_chat(user_id=user_id, chat_id=chat_id)
    background_tasks.add_task(chat_service.background_delete_chat_history, chat_id=chat_id)