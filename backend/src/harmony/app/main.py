import aioboto3
import traceback
import logging
from scalar_fastapi import get_scalar_api_reference

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core import settings
from .api.v1 import router as api_v1_router
from .services import WebSocketManager, RedisPubSubManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = aioboto3.Session()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n\n\n------------------------------- Starting Up -------------------------------\n\n\n")

    # Initialize Redis Manager
    if settings.REDIS_CONNECT:
        ws_manager = WebSocketManager()
        redis_manager = RedisPubSubManager(ws_manager)
        await redis_manager.connect()
        if settings.REDIS_LISTEN:
            redis_manager.start_listen()
    
        # Inject into app.state for dependencies
        app.state.redis_manager = redis_manager
        app.state.ws_manager = ws_manager

    try:
        async with session.client(
            'dynamodb',
            endpoint_url=settings.DYNAMODB_ENDPOINT,
            region_name=settings.AWS_REGION,
        ) as dynamodb:  
            app.state.dynamodb = dynamodb
            yield
    finally:
        print("\n\n\n------------------------------ Shutting Down ------------------------------\n\n\n")
        if redis_manager:
            await redis_manager.disconnect()

app = FastAPI(lifespan=lifespan, debug=True)
app.include_router(api_v1_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Harmony API is running."}

# Global exception handler to catch unhandled exceptions and log them
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logger.error(f"UNHANDLED EXCEPTION on {request.method} {request.url}\n{error_trace}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error", 
            "trace": error_trace if app.debug else None 
        }
    )

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title
    )