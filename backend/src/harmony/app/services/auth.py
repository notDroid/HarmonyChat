from datetime import timedelta
from fastapi import HTTPException, status

from harmony.app.core import get_password_hash, verify_password, create_token, settings
from .user import UserService
from harmony.app.schemas import UserCreateRequest, Token

class AuthService:
    '''
    Handles authentication workflows including user registration and login.
    
    SignUp:
        1. Validates that the email/username is not already taken.
        2. Hashes the plain-text password using Argon2.
        3. Delegates user creation to the UserService.
        
    Login (Authenticate):
        1. Retrieves the user via the UserDataRepository.
        2. Verifies the user is active (not tombstoned).
        3. Verifies the provided password against the stored hash.
        4. Generates and returns a JWT Bearer token.
    '''

    def __init__(
            self,
            user_service: UserService
    ):
        self.user_service = user_service

    async def sign_up(self, user_create: UserCreateRequest) -> str:
        existing_user = await self.user_service.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        hashed_pw = get_password_hash(user_create.password)

        user_id = await self.user_service.create_user(
            req=user_create.model_copy(update={"hashed_password": hashed_pw})
        )
        
        return user_id

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.user_service.get_user_by_email(email)
        
        if not user or getattr(user, "tombstone", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": user.user_id}, 
            expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")