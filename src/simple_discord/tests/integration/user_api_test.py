import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_happy_path(client: AsyncClient, api_path: str):
    """
    Test that a valid request creates a user and returns a User ID.
    """
    # ARRANGE
    payload = {
        "username": "test_user_1",
        "email": "test@example.com"
    }

    # ACT
    response = await client.post(f"{api_path}/user/", json=payload)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert isinstance(data["user_id"], str)
    assert len(data["user_id"]) > 0

@pytest.mark.asyncio
async def test_create_user_validation_error(client: AsyncClient, api_path: str):
    """
    Test that missing required fields returns 422 (FastAPI default validation).
    """
    # ARRANGE
    payload = {
        "username": "test_user_2"
        # Missing email
    }

    # ACT
    response = await client.post(f"{api_path}/user/", json=payload)

    # ASSERT
    assert response.status_code == 422