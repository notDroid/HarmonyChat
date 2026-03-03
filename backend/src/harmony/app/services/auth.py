import asyncio
from datetime import timedelta, timezone, datetime
from fastapi import HTTPException, status

from harmony.app.core import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    generate_refresh_token, 
    hash_refresh_token
)
from harmony.app.core import AuthConfig
from .command import Command
from .user import UserCommands, UserQueries
from harmony.app.repositories import AuthRepository
from harmony.app.schemas import UserCreateRequest, Token
import structlog

logger = structlog.get_logger(__name__)

class AuthService(Command):
    '''
    Handles authentication workflows including user registration, login, and token refresh.
    
    SignUp:
        1. Validates that the email/username is not already taken.
        2. Hashes the plain-text password using Argon2.
        3. Delegates user creation to the UserService.
        
    Login (Authenticate):
        1. Retrieves the user via the UserDataRepository.
        2. Verifies the user is active (not tombstoned).
        3. Verifies the provided password against the stored hash.
        4. Generates and returns a JWT Bearer token.

    Token Refresh:
        1. Validates the provided refresh token exists and is not expired.
        2. Generates new access and refresh tokens (refresh token rotation).
        3. Stores the new refresh token and invalidates the old one.
        (Token recovation is scheduled in the background)

    Refresh Token Revocation:
        (There is a short grace period before deleting the token to allow multiple simultaneous refresh requests)
        1. Deletes the refresh token from the database, effectively revoking it.
    '''

    def __init__(
            self,
            session,
            user_commands: UserCommands,
            user_queries: UserQueries,
            auth_repository: AuthRepository,
            auth_config: AuthConfig = AuthConfig()
    ):
        super().__init__(session, logger)
        self.user_commands = user_commands
        self.user_queries = user_queries
        self.auth_repository = auth_repository
        self.cfg = auth_config

    async def sign_up(self, user_create: UserCreateRequest) -> str:
        try:
            existing_user = await self.user_queries.get_user_by_email(user_create.email)
        except HTTPException:
            # If get_user_by_email raises an exception (e.g., 404), it means the user doesn't exist
            existing_user = None

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )

        hashed_pw = get_password_hash(user_create.password)

        user = await self.user_commands.create_user(
            req=user_create,
            hashed_password=hashed_pw,
        )
        
        return user

    async def authenticate_user(self, email: str, password: str) -> list[Token]:
        try:
            user = await self.user_queries.get_user_by_email(email, raw=True)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user or user.tombstone:
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

        # Create tokens
        access_token, refresh_token, hashed_rt, rt_expires_dt = await self._generate_tokens(str(user.user_id))

        # Create refresh token session in DB with hashed_rt and user_id
        async with self.transaction_handler("create_refresh_token", email=user.email, user_id=str(user.user_id)):  
            await self.auth_repository.create_token(
                token_hash=hashed_rt,
                user_id=user.user_id,
                expires_at=rt_expires_dt
            )

        return [access_token, refresh_token]
        
    async def _generate_tokens(self, user_id: str) -> list[Token]:
        access_token_expires = timedelta(minutes=self.cfg.access_token_expire_minutes)
        expire_dt = datetime.now(timezone.utc) + access_token_expires
        access_token_str = create_access_token(
            data={"sub": str(user_id)}, 
            expires_delta=access_token_expires,
            secret_key=self.cfg.secret_key,
            algorithm=self.cfg.algorithm
        )
        access_token = Token(
            token=access_token_str, 
            token_type=self.cfg.access_token_name, 
            expiration=int(expire_dt.timestamp())
        )

        plain_rt, hashed_rt = generate_refresh_token()
        rt_expires = datetime.now(timezone.utc) + timedelta(days=self.cfg.refresh_token_expire_days)

        refresh_token = Token(
            token=plain_rt,
            token_type=self.cfg.refresh_token_name, 
            expiration=int(rt_expires.timestamp())
        )

        return access_token, refresh_token, hashed_rt, rt_expires
    
    async def refresh_tokens(self, refresh_token: str) -> list[Token]:
        token_hash = hash_refresh_token(refresh_token)

        try:
            async with self.transaction_handler("refresh_tokens", token_hash=token_hash):
                # Validate token exists and is not expired
                consumed_token = await self.auth_repository.get_token(token_hash)
                user_id = consumed_token.user_id
                if consumed_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token expired."
                    )

                # Generate new tokens
                access_token, refresh_token, hashed_rt, rt_expires_dt = await self._generate_tokens(str(user_id))

                # Store the new refresh token session in DB
                await self.auth_repository.create_token(
                    token_hash=hashed_rt,
                    user_id=user_id,
                    expires_at=rt_expires_dt
                )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return [access_token, refresh_token]
    
    async def revoke_refresh_token(self, refresh_token: str):
        token_hash = hash_refresh_token(refresh_token)
        await self.auth_repository.delete_token(token_hash)

    async def background_revoke_refresh_token(self, refresh_token: str):
        # Wait for grace period before revoking the token to allow for any in-flight requests that might be using the same refresh token (e.g., multiple simultaneous refresh requests or clock skew)
        await asyncio.sleep(self.cfg.refresh_token_grace_period_seconds)
        await self.revoke_refresh_token(refresh_token)