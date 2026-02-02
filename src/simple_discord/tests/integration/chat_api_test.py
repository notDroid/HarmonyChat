import pytest
from httpx import AsyncClient

# --- Helper ---
async def create_user_helper(client: AsyncClient, api_path: str, name: str) -> str:
    res = await client.post(f"{api_path}/user/", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert res.status_code == 200
    return res.json()["user_id"]

# ----------------------------- CREATE CHAT TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_create_chat_happy_path(client: AsyncClient, api_path: str):
    """
    Test that a valid request (with existing users) creates a chat.
    """
    # ARRANGE: Create valid users first
    u1 = await create_user_helper(client, api_path, "chat_tester_1")
    u2 = await create_user_helper(client, api_path, "chat_tester_2")

    payload = {
        "user_id_list": [u1, u2]
    }

    # ACT
    response = await client.post(f"{api_path}/chat/", json=payload)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "chat_id" in data

@pytest.mark.asyncio
async def test_create_chat_not_enough_users(client: AsyncClient, api_path: str):
    """
    Test that providing fewer than 2 users fails with 400.
    """
    # ARRANGE
    payload = {
        "user_id_list": ["just_one_user"]
    }

    # ACT
    response = await client.post(f"{api_path}/chat/", json=payload)

    # ASSERT
    assert response.status_code == 400
    assert response.json()["detail"] == "A chat must have at least two users."

@pytest.mark.asyncio
async def test_create_chat_user_not_found(client: AsyncClient, api_path: str):
    """
    Test that providing a user ID that doesn't exist in DB fails with 404.
    """
    # ARRANGE
    # We create one valid user, but the second one is fake
    u1 = await create_user_helper(client, api_path, "real_user")
    
    payload = {
        "user_id_list": [u1, "non_existent_ulid"]
    }

    # ACT
    response = await client.post(f"{api_path}/chat/", json=payload)

    # ASSERT
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

# ----------------------------- SEND MESSAGE TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_send_message_happy_path(client: AsyncClient, api_path: str):
    """
    Test sending a message to an existing chat as a member.
    """
    # ARRANGE
    u1 = await create_user_helper(client, api_path, "msg_sender")
    u2 = await create_user_helper(client, api_path, "msg_receiver")
    
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": [u1, u2]})
    chat_id = setup_res.json()["chat_id"]

    # ACT
    msg_payload = {"user_id": u1, "content": "Hello World"}
    response = await client.post(f"{api_path}/chat/{chat_id}", json=msg_payload)

    # ASSERT
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Message sent"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_send_message_forbidden_user(client: AsyncClient, api_path: str):
    """
    Test sending a message as a user who is NOT in the chat (403).
    """
    # ARRANGE
    u1 = await create_user_helper(client, api_path, "insider_1")
    u2 = await create_user_helper(client, api_path, "insider_2")
    outsider = await create_user_helper(client, api_path, "outsider")
    
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": [u1, u2]})
    chat_id = setup_res.json()["chat_id"]

    # ACT
    msg_payload = {"user_id": outsider, "content": "Let me in"}
    response = await client.post(f"{api_path}/chat/{chat_id}", json=msg_payload)

    # ASSERT
    assert response.status_code == 403
    assert response.json()["detail"] == "User is not a member of this chat."

@pytest.mark.asyncio
async def test_send_message_chat_not_found(client: AsyncClient, api_path: str):
    """
    Test sending a message to a non-existent chat (404).
    """
    # ARRANGE
    u1 = await create_user_helper(client, api_path, "lost_user")
    
    # ACT
    msg_payload = {"user_id": u1, "content": "Where am I?"}
    response = await client.post(f"{api_path}/chat/fake_chat_id", json=msg_payload)

    # ASSERT
    assert response.status_code == 404

# ----------------------------- CHAT HISTORY TESTS ---------------------------- #

@pytest.mark.asyncio
async def test_get_chat_history(client: AsyncClient, api_path: str):
    """
    Test creating chat -> sending messages -> retrieving history.
    """
    # ARRANGE
    alice = await create_user_helper(client, api_path, "alice_hist")
    bob = await create_user_helper(client, api_path, "bob_hist")
    
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": [alice, bob]})
    chat_id = setup_res.json()["chat_id"]

    # Send messages
    await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": alice, "content": "Hi Bob"})
    await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": bob, "content": "Hi Alice"})

    # ACT
    # Note: user_id is a query parameter in your router: ?user_id=...
    response = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": alice})

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    
    # Check content match
    assert data["messages"][0]["content"] == "Hi Bob"
    assert data["messages"][0]["user_id"] == alice
    assert data["messages"][1]["content"] == "Hi Alice"
    assert data["messages"][1]["user_id"] == bob

@pytest.mark.asyncio
async def test_get_chat_history_forbidden(client: AsyncClient, api_path: str):
    """
    Test that a non-member cannot read history.
    """
    # ARRANGE
    alice = await create_user_helper(client, api_path, "alice_secret")
    bob = await create_user_helper(client, api_path, "bob_secret")
    eve = await create_user_helper(client, api_path, "eve_spy")
    
    setup_res = await client.post(f"{api_path}/chat/", json={"user_id_list": [alice, bob]})
    chat_id = setup_res.json()["chat_id"]

    # ACT
    response = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": eve})

    # ASSERT
    assert response.status_code == 403