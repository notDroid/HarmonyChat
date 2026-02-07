from simple_discord.app.schemas import *
from .dependencies import get_user_service

from fastapi import Depends, APIRouter

router = APIRouter()

'''
API endpoints for user operations.

Create User:
    - POST /
    - Request: CreateUserRequest (username, email)
    - Response: CreateUserResponse (user_id)
    desc: Create a new user with a username and email.

Get User Chats:
    - GET /{user_id}/chats
    - Request: user_id (path parameter)
    - Response: GetUserChatsResponse (chat_id_list)
    desc: Retrieve the list of chat IDs associated with a user.

Delete User:
    - DELETE /{user_id}
    - Request: user_id (path parameter)
    - Response: 204 No Content
    desc: Mark a user as deleted (tombstone).
'''

@router.post("/", response_model=CreateUserResponse)
async def create_user(
    msg: CreateUserRequest,
    user_service = Depends(get_user_service)
):
    user_id = await user_service.create_user(msg)
    return {"user_id": user_id}

@router.get("/{user_id}/chats", response_model=GetUserChatsResponse)
async def get_user_chats(
    user_id: str,
    user_service = Depends(get_user_service)
):
    chats = await user_service.get_user_chats(user_id=user_id)
    return GetUserChatsResponse(chat_id_list=chats)

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    user_service = Depends(get_user_service)
):
    await user_service.delete_user(user_id=user_id)