from contextlib import asynccontextmanager
import aioboto3
from fastapi import FastAPI
from .core import settings
from .api.v1 import router as api_v1_router

session = aioboto3.Session()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n\n\n------------------------------- Starting Up -------------------------------\n\n\n")
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

app = FastAPI(lifespan=lifespan, debug=True)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Simple Discord API is running."}