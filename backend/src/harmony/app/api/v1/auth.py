from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from harmony.app.schemas import Token, RefreshRequest
from .dependencies import get_auth_service

router = APIRouter()

@router.post(
    "/token", 
    response_model=List[Token],
    summary="Login / Get Access Token",
    responses={
        401: {
            "description": "Incorrect email or password, or user is inactive.",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect email or password"}
                }
            }
        }
    }
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service = Depends(get_auth_service)
):
    """
    **OAuth2 compatible token login.**
    
    This endpoint exchanges user credentials for a JWT Access Token.
    
    - **username**: Must contain the user's **Email Address**.
    - **password**: The plain-text password.
    
    Returns a Bearer token to be used in the `Authorization` header for subsequent requests.
    """
    # Note: form_data.username is mapped to email in the service layer
    return await auth_service.authenticate_user(
        email=form_data.username, 
        password=form_data.password
    )

@router.post(
    "/refresh", 
    response_model=List[Token],
    summary="Refresh Access Token",
    responses={
        401: {
            "description": "Invalid or expired refresh token.",
        }
    }
)
async def refresh(
    refresh_token: RefreshRequest,
    background_tasks: BackgroundTasks,
    auth_service = Depends(get_auth_service),
):
    """
    **Refresh Tokens using a Refresh Token.**
    """
    # Get tokens
    tokens = await auth_service.refresh_tokens(
        refresh_token=refresh_token.refresh_token
    )

    # Schedule old refresh token for deletion after grace period
    background_tasks.add_task(
        auth_service.background_revoke_refresh_token, 
        refresh_token=refresh_token.refresh_token
    )
    return tokens