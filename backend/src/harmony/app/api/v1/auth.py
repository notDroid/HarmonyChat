from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from typing import Annotated

from .dependencies import get_auth_service
from harmony.app.schemas import Token


router = APIRouter()

'''
Authentication API Endpoints:

POST /token
    Body:    { "email": "<str>", "password": "<str>" }
    Returns: { "access_token": "<str>", "token_type": "bearer" }
'''

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service = Depends(get_auth_service)
):
    return await user_service.authenticate_user(form_data.username, form_data.password)