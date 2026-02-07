from simple_discord.app.schemas import *
from .dependencies import get_chat_service

from fastapi import Depends, BackgroundTasks, APIRouter

router = APIRouter()

'''
API endpoints for chat operations.

create_chat:
    - POST /
    - Request: CreateChatRequest (user_id_list)
    - Response: CreateChatResponse (chat_id)
    desc: Create a new chat with a list of user IDs.

send_message:
    - POST /{chat_id}
    - Request: SendMessageRequest (user_id, content)
    - Response: SendMessageResponse (status, timestamp)
    desc: Send a message to a specific chat.

get_chat_history:
    - GET /{chat_id}
    - Request: user_id (as query parameter)
    - Response: GetChatHistoryResponse (messages)
    desc: Retrieve the chat history for a given chat ID.
'''
@router.post("/", response_model=CreateChatResponse)
async def create_chat(
    msg: CreateChatRequest,
    chat_service = Depends(get_chat_service)
):
    chat_id = await chat_service.create_chat(
        user_id_list=msg.user_id_list,
    )
    return {"chat_id": chat_id}

@router.post("/{chat_id}", response_model=SendMessageResponse, status_code=201)
async def send_message(
    chat_id: str,
    msg: SendMessageRequest, 
    chat_service = Depends(get_chat_service)
):
    timestamp = await chat_service.send_message(
        chat_id=chat_id, 
        user_id=msg.user_id, 
        content=msg.content
    )
    return {"status": "Message sent", "timestamp": timestamp}

@router.get("/{chat_id}", response_model=GetChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    user_id: str,
    chat_service = Depends(get_chat_service)
):
    messages = await chat_service.get_chat_history(user_id=user_id, chat_id=chat_id)
    return GetChatHistoryResponse(messages=messages)

@router.delete("/{chat_id}", status_code=204) # TODO: finish implementation (can cause db memory leaks until then)
async def delete_chat(
    chat_id: str,
    user_id: str,
    background_tasks: BackgroundTasks,
    chat_service = Depends(get_chat_service),
):
    await chat_service.delete_chat(user_id=user_id, chat_id=chat_id)
    background_tasks.add_task(chat_service.background_delete_chat_history, chat_id=chat_id)