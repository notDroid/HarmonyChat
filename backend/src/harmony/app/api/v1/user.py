from fastapi import APIRouter, Depends, status, HTTPException
from harmony.app.schemas import (
    UserCreateRequest, 
    UserResponse, 
    UserChatsResponse
)
from .dependencies import get_auth_service, get_current_user, get_user_service

router = APIRouter()

@router.post(
    "/", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "A user with this email already exists."}
                }
            }
        }
    }
)
async def sign_up(
    auth_create: UserCreateRequest,
    auth_service = Depends(get_auth_service)
):
    """
    Registers a new user in the system.
    
    - **Validation**: Checks if the email is unique.
    - **Security**: The password is securely hashed (Argon2) before storage.
    - **Output**: Returns the generated User ID (ULID).
    """
    user_id = await auth_service.sign_up(auth_create)
    return UserResponse(user_id=user_id)

@router.get(
    "/me/chats", 
    response_model=UserChatsResponse,
    summary="Get my chats",
    responses={
        401: {"description": "Authentication credentials were not provided or are invalid."}
    }
)
async def get_my_chats(
    user_id: str = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """
    Retrieves a list of Chat IDs that the currently logged-in user participates in.
    """
    chats = await user_service.get_user_chats(user_id=user_id)
    return UserChatsResponse(chat_id_list=chats)

@router.delete(
    "/me", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate my account",
    responses={
        401: {"description": "Authentication credentials were not provided or are invalid."}
    }
)
async def delete_me(
    user_id: str = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """
    **Soft delete** the current user.
    
    - Marks the user as 'tombstoned' in the database.
    - The user will no longer be able to log in.
    - Historical data (messages) is preserved for data integrity.
    """
    await user_service.delete_user(user_id=user_id)