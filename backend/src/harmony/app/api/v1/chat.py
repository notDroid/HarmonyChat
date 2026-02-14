from harmony.app.schemas import *
from .dependencies import get_chat_service, get_current_user

from fastapi import Depends, BackgroundTasks, APIRouter

router = APIRouter()

'''
Chat API Endpoints:

POST /
  Body:    { "user_id_list": ["<str>", ...] }
  Returns: { "chat_id": "<str>" }

POST /{chat_id}
  Body:    { "content": "<str>" }
  Returns: { "status": "Message sent", "timestamp": <datetime> }
  Status:  201 Created

GET /{chat_id}
  Returns: { "messages": [...] }

DELETE /{chat_id}
  Status:  204 No Content
'''

@router.post("/", response_model=CreateChatResponse)
async def create_chat(
    data: CreateChatRequest,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    chat_id = await chat_service.create_chat(
        user_id=user_id,
        user_id_list=data.user_id_list,
    )
    return {"chat_id": chat_id}

@router.post("/{chat_id}", response_model=SendMessageResponse, status_code=201)
async def send_message(
    chat_id: str,
    data: SendMessageRequest, 
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    timestamp = await chat_service.send_message(
        chat_id=chat_id, 
        user_id=user_id, 
        content=data.content
    )
    return {"status": "Message sent", "timestamp": timestamp}

@router.get("/{chat_id}", response_model=GetChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service)
):
    messages = await chat_service.get_chat_history(user_id=user_id, chat_id=chat_id)
    return GetChatHistoryResponse(messages=messages)

@router.delete("/{chat_id}", status_code=204) # TODO: finish implementation (can cause db memory leaks until then)
async def delete_chat(
    chat_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    chat_service = Depends(get_chat_service),
):
    await chat_service.delete_chat(user_id=user_id, chat_id=chat_id)
    background_tasks.add_task(chat_service.background_delete_chat_history, chat_id=chat_id)