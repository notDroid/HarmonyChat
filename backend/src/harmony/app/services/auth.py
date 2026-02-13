from datetime import timedelta
from fastapi import HTTPException, status

from harmony.app.core.security import get_password_hash, verify_password, create_access_token
from harmony.app.core.settings import settings
from harmony.app.repositories import UserDataRepository
from harmony.app.services.user import UserService
from harmony.app.schemas.auth import UserCreate, Token 

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
            user_service: UserService,
            user_data_repository: UserDataRepository
    ):
        self.user_service = user_service
        self.user_data_repository = user_data_repository

    async def sign_up(self, user_create: UserCreate) -> str:
        existing_user = await self.user_data_repository.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        hashed_pw = get_password_hash(user_create.password)

        user_id = await self.user_service.create_user_with_auth(
            email=user_create.email,
            hashed_password=hashed_pw,
            metadata=user_create.metadata
        )
        
        return user_id

    async def authenticate_user(self, email: str, password: str) -> Token:
        user = await self.user_data_repository.get_user_by_email(email)
        
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
        access_token = create_access_token(
            data={"sub": user.user_id}, 
            expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")