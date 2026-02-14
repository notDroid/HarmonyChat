from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from harmony.app.schemas import Token
from .dependencies import get_auth_service

router = APIRouter()

@router.post(
    "/token", 
    response_model=Token,
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