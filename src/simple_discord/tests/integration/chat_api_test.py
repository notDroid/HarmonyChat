import pytest
from httpx import AsyncClient

# ----------------------------- CREATE CHAT TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_create_chat_happy_path(client: AsyncClient, api_path: str):
    """
    Test that a valid request creates a chat and returns a Chat ID.
    """
    # ARRANGE
    payload = {
        "user_id_list": ["user_1", "user_2"]
    }

    # ACT
    response = await client.post(f"{api_path}/chat/", json=payload)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "chat_id" in data
    assert isinstance(data["chat_id"], str)
    assert len(data["chat_id"]) > 0

@pytest.mark.asyncio
async def test_create_chat_validation_error(client: AsyncClient, api_path: str):
    """
    Test that providing fewer than 2 users fails.
    The Service raises ValueError. 
    """
    # ARRANGE
    payload = {
        "user_id_list": ["user_1"] # Only one user
    }

    # ACT
    response = await client.post(f"{api_path}/chat/", json=payload)

    # ASSERT
    # Since there is no exception handler in the router code provided, 
    # FastAPI will throw a 500 error when ValueError is raised.
    # Ideally, you should implement an exception handler to return 400.
    assert response.status_code == 500 
    # If you add an exception handler, change this to: assert response.status_code == 400

# ----------------------------- SEND MESSAGE TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_send_message_happy_path(client: AsyncClient, api_path: str):
    """
    Test flow: Create a chat -> Send a message to that chat -> Verify success.
    """
    # ARRANGE: Create the chat first
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": ["alice", "bob"]})
    chat_id = setup_res.json()["chat_id"]

    message_payload = {
        "user_id": "alice",
        "content": "Hello World"
    }

    # ACT
    response = await client.post(f"{api_path}/chat/{chat_id}", json=message_payload)

    # # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Message sent"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_send_message_forbidden_user(client: AsyncClient, api_path: str):
    """
    Test sending a message as a user who is NOT in the chat.
    """
    # ARRANGE
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": ["alice", "bob"]})
    chat_id = setup_res.json()["chat_id"]

    # 'eve' is not in the chat
    message_payload = {
        "user_id": "eve", 
        "content": "I am hacking you"
    }

    # ACT
    response = await client.post(f"{api_path}/chat/{chat_id}", json=message_payload)

    # ASSERT
    # Service raises PermissionError. Without a handler, this is 500.
    # With a handler, this should be 403.
    assert response.status_code == 500

# ----------------------------- CHAT HISTORY TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_get_chat_history(client: AsyncClient, api_path: str):
    """
    Test flow: Create chat -> Send 2 messages -> Get history -> Verify 2 messages exist.
    """
    # ARRANGE
    # 1. Create Chat
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": ["alice", "bob"]})
    chat_id = setup_res.json()["chat_id"]

    # 2. Send Message 1
    await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": "alice", "content": "Hi"})
    
    # 3. Send Message 2
    await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": "bob", "content": "Hello back"})

    # ACT
    response = await client.get(f"{api_path}/chat/{chat_id}")

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    
    # Check that we received a list of messages
    assert "messages" in data
    assert len(data["messages"]) == 2
    
    # Verify content order (assuming standard appending)
    assert data["messages"][0]["content"] == "Hi"
    assert data["messages"][0]["user_id"] == "alice"
    assert data["messages"][1]["content"] == "Hello back"