import pytest
from harmony.tests.utils import AppClient, spawn_actor

@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_happy_path(app_client: AppClient):
    """
    Tests the full lifecycle: Create Users -> Create Chat -> Send Msg -> Read History
    """
    # 1. Setup Actors
    alice = await spawn_actor(app_client)
    bob = await spawn_actor(app_client)

    # 2. Alice creates chat
    chat_id = await alice.create_chat_with([bob])
    assert chat_id

    # 3. Exchange messages
    await alice.send_message(chat_id, "Hello Bob!")
    await bob.send_message(chat_id, "Hi Alice!")

    # 4. Verify History (Alice's perspective)
    alice_hist = await alice.get_history(chat_id)
    assert len(alice_hist) == 2
    assert alice_hist[1].content == "Hello Bob!"
    assert alice_hist[1].user_id == alice.user_id
    assert alice_hist[0].content == "Hi Alice!"

    # 5. Verify History (Bob's perspective)
    bob_hist = await bob.get_history(chat_id)
    assert len(bob_hist) == 2

@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_isolation_security(app_client: AppClient):
    """
    Ensure users cannot access chats they are not part of.
    """
    alice = await spawn_actor(app_client)
    bob = await spawn_actor(app_client)
    eve = await spawn_actor(app_client) # The Spy

    # Alice and Bob start a chat
    chat_id = await alice.create_chat_with([bob])
    await alice.send_message(chat_id, "Secret code is 1234")

    # Eve tries to read history
    with pytest.raises(Exception) as excinfo:
        await eve.get_history(chat_id)
    # httpx raises HTTPStatusError, we expect 403
    assert "403" in str(excinfo.value)

    # Eve tries to send message
    with pytest.raises(Exception) as excinfo:
        await eve.send_message(chat_id, "I am watching")
    assert "403" in str(excinfo.value)