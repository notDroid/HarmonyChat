import uuid
import traceback
from scalar_fastapi import get_scalar_api_reference
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .core import get_settings, setup_logging, lifespan
from .api.v1 import router as api_v1_router

# Initialize logging
settings = get_settings()
setup_logging(is_local_dev=(settings.app_env == "development"))
logger = structlog.get_logger(__name__)

# Initialize FastAPI app with lifespan for resource management
app = FastAPI(lifespan=lifespan, debug=(settings.app_env == "development"))
app.include_router(api_v1_router, prefix="/api/v1")

# CORS Middleware (allow all for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Harmony API is running."}

# Global exception handler to catch unhandled exceptions and log them
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logger.exception(f"Unhandled exception during request processing", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error", 
            "trace": error_trace if app.debug else None 
        }
    )

# Documentation endpoint for Scalar API reference
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title
    )

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Clear context from the previous request
    clear_contextvars()
    
    # Generate a unique ID for this specific request
    request_id = str(uuid.uuid4())
    
    # Bind the request_id and path to EVERY log emitted during this request
    bind_contextvars(request_id=request_id, path=request.url.path, method=request.method)
    
    logger.info("Request started")
    
    try:
        response = await call_next(request)
        logger.info("Request completed", status_code=response.status_code)
        return response
    except Exception as e:
        logger.exception("Request failed with unhandled exception")
        raise