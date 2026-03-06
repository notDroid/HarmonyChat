from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from harmony.app.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    AuthenticationError,
    ConflictError,
    ValidationError,
    LimitExceededError
)

logger = structlog.get_logger(__name__)

def register_exception_handlers(app: FastAPI):
    
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message},
            headers=exc.headers
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(LimitExceededError)
    async def limit_exceeded_handler(request: Request, exc: LimitExceededError):
        return JSONResponse(status_code=400, content={"detail": exc.message})