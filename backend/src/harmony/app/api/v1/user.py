from harmony.app.schemas import UserCreate, CreateUserResponse, GetUserChatsResponse
from .dependencies import get_auth_service, get_current_user, get_user_service

from fastapi import Depends, APIRouter

router = APIRouter()

'''
API endpoints for user operations.

POST /
  Body:    { "username": "<str>", "email": "<str>", "password": "<str>" }
  Returns: { "user_id": "<str>" }

GET /me/chats
  Returns: { "chat_id_list": ["<str>", ...] }

DELETE /me
  Status:  204 No Content
'''

@router.post("/", response_model=CreateUserResponse)
async def sign_up(
    auth_create: UserCreate,
    auth_service = Depends(get_auth_service)
):
    user_id = await auth_service.create_user(auth_create)
    return {"user_id": user_id}

@router.get("/me/chats", response_model=GetUserChatsResponse)
async def get_my_chats(
    user_id: str = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    chats = await user_service.get_user_chats(user_id=user_id)
    return GetUserChatsResponse(chat_id_list=chats)

@router.delete("/me", status_code=204)
async def delete_me(
    user_id: str = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    await user_service.delete_user(user_id=user_id)