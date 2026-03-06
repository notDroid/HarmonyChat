from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from harmony.app.core.exceptions import (
    NotFoundError,
    AuthorizationError,
    AuthenticationError,
    ConflictError,
    ValidationError,
    LimitExceededError,
    InternalServerError
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
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(InternalServerError)
    async def internal_server_error_handler(request: Request, exc: InternalServerError):
        return JSONResponse(status_code=500, content={"detail": exc.message})
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """
        Catches any unexpected Python exceptions that aren't wrapped in a HarmonyError.
        Prevents stack traces from leaking to the client.
        """
        logger.exception("unhandled_system_error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500, 
            content={"detail": "An unexpected server error occurred."}
        )