import uuid
from fastapi import Depends, APIRouter, status, HTTPException, Request, Query
from harmony.app.core.settings import get_settings, Settings
from harmony.app.schemas import (
    ChatCreateRequest, 
    ChatResponse, 
    MessageSendRequest, 
    ChatMessage, 
    ChatHistoryResponse
)
from .dependencies import get_current_user, get_chat_commands, get_chat_queries, get_message_commands, get_message_queries

# common error responses
common_chat_errors = {
    401: {"description": "Authentication credentials were not provided or are invalid."},
    404: {"description": "Chat not found"},
    403: {"description": "User is not a participant of this chat"},
}

router = APIRouter()

@router.post(
    "/", 
    response_model=ChatResponse, 
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
    user_id: uuid.UUID = Depends(get_current_user),
    chat_command_service = Depends(get_chat_commands)
):
    """
    Creates a new chat room between the current user and a list of target users.
    
    - **user_id_list**: A list of user_ids for the users to include.
    """
    chat = await chat_command_service.create_chat(
        creator_id=user_id,
        data=data
    )
    return chat

@router.post(
    "/{chat_id}", 
    response_model=ChatMessage, 
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    responses=common_chat_errors
)
async def send_message(
    chat_id: uuid.UUID,
    data: MessageSendRequest, 
    user_id: uuid.UUID = Depends(get_current_user),
    message_command_service = Depends(get_message_commands)
):
    """
    Persist a message to the database for a specific chat.
    
    Returns the message details including the generated ULID and timestamp.
    """

    # Simulate timeout for testing purposes
    # await asyncio.sleep(5)

    msg = await message_command_service.send_message(
        chat_id=chat_id, 
        user_id=user_id,
        content=data.content,
        client_uuid=data.client_uuid
    )

    return msg

def get_chat_pagination_limit(
    limit: int | None = Query(default=None, ge=1, description="Number of items to return"),
    settings: Settings = Depends(get_settings)
) -> int:
    """
    Resolves the chat pagination limit. 
    Falls back to the default setting if no limit is provided by the client.
    """
    if limit is None:
        return settings.chat.default_pagination_limit
    
    if limit > settings.chat.default_pagination_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Limit cannot be greater than {settings.chat.default_pagination_limit}"
        )
        
    return limit

@router.get(
    "/{chat_id}", 
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Retrieves all messages for a specific chat. Messages are sorted by ULID (chronologically).",
    responses=common_chat_errors
)
async def get_chat_history(
    chat_id: uuid.UUID,
    limit: int = Depends(get_chat_pagination_limit),
    cursor: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user),
    message_queries_service = Depends(get_message_queries)
):
    # Simulate timeout for testing purposes
    # await asyncio.sleep(5)

    messages, next_cursor = await message_queries_service.get_chat_history(
        user_id=user_id, 
        chat_id=chat_id, 
        limit=limit, 
        cursor=cursor
    )
    return ChatHistoryResponse(messages=messages, next_cursor=next_cursor)

@router.delete(
    "/{chat_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat",
    responses=common_chat_errors
)
async def delete_chat(
    chat_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user),
    chat_command_service = Depends(get_chat_commands),
):
    """
    **Hard deletes** a chat and all its associated history.
    
    - This operation performs a 'soft' check immediately.
    - The actual deletion of thousands of messages happens in a **Background Task** 
      to prevent the API from hanging.
    """
    await chat_command_service.delete_chat(user_id=user_id, chat_id=chat_id)