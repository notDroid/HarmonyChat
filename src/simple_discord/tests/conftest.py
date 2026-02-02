import os
from httpx import AsyncClient
import pytest_asyncio

API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL", "http://localhost:8080")
API_PATH = os.getenv("API_PATH", "/api/v1")

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(base_url=API_ENDPOINT_URL) as ac:
        yield ac

@pytest_asyncio.fixture
async def api_path():
    return API_PATH