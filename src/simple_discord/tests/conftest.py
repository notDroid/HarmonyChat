import os
from httpx import AsyncClient
import pytest_asyncio
import pytest

API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL", "http://localhost:8000")
API_PATH = os.getenv("API_PATH", "/api/v1")

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(base_url=API_ENDPOINT_URL) as ac:
        yield ac

@pytest_asyncio.fixture
async def api_path():
    return API_PATH

def pytest_addoption(parser):
    parser.addoption("--run-stress", action="store_true", default=False, help="enable stress tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "stress: mark test as a slow stress test")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-stress"):
        return
    skip_stress = pytest.mark.skip(reason="need --run-stress option to run")
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip_stress)