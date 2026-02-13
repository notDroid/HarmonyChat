from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status

from typing import Annotated
from .dependencies import get_user_service

from harmony.app.core import verify_password, create_token, settings
from datetime import timedelta


router = APIRouter()

@router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service = Depends(get_user_service)
):
    # Authenticate user
    user_data = await user_service.get_user_by_email(form_data.username)
    if not user_data or not verify_password(form_data.password, user_data.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    access_token = create_token(data={"sub": user_data.user_id}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
