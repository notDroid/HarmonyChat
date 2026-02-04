import os
from httpx import AsyncClient
import pytest_asyncio
import pytest

API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:8000")
API_PATH = os.getenv("API_PATH", "/api/v1")

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(base_url=API_ENDPOINT) as ac:
        yield ac

@pytest_asyncio.fixture
async def api_path():
    return API_PATH

def pytest_configure(config):
    config.addinivalue_line("markers", "stress")
    config.addinivalue_line("markers", "integration")