import pytest
from httpx import AsyncClient

# --- Helper ---
async def create_user_helper(client: AsyncClient, api_path: str, name: str) -> str:
    res = await client.post(f"{api_path}/user/", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    return res.json()["user_id"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_simulation_multi_chat_isolation(client: AsyncClient, api_path: str):
    """
    SIMULATION:
    1. Create 3 users: A, B, C.
    2. Create Chat 1 (A & B).
    3. Create Chat 2 (A & C).
    4. A talks in Chat 1.
    5. C tries to read Chat 1 (fails).
    6. A talks in Chat 2.
    7. Verify B sees Chat 1 history but NOT Chat 2 history.
    """
    
    print("\n[SIM] 1. Creating Users...")
    user_a = await create_user_helper(client, api_path, "SimUserA")
    user_b = await create_user_helper(client, api_path, "SimUserB")
    user_c = await create_user_helper(client, api_path, "SimUserC")

    print("[SIM] 2. Creating Chat 1 (A & B)...")
    res1 = await client.post(f"{api_path}/chat/", json={"user_id_list": [user_a, user_b]})
    chat_1_id = res1.json()["chat_id"]

    print("[SIM] 3. Creating Chat 2 (A & C)...")
    res2 = await client.post(f"{api_path}/chat/", json={"user_id_list": [user_a, user_c]})
    chat_2_id = res2.json()["chat_id"]

    print("[SIM] 4. A talks in Chat 1...")
    await client.post(
        f"{api_path}/chat/{chat_1_id}", 
        json={"user_id": user_a, "content": "Hello B, this is private."}
    )

    print("[SIM] 5. C tries to read Chat 1 (Should Fail)...")
    fail_res = await client.get(f"{api_path}/chat/{chat_1_id}", params={"user_id": user_c})
    assert fail_res.status_code == 403

    print("[SIM] 6. A talks in Chat 2...")
    await client.post(
        f"{api_path}/chat/{chat_2_id}", 
        json={"user_id": user_a, "content": "Hello C, don't tell B."}
    )

    print("[SIM] 7. Verify B sees Chat 1...")
    chat1_res = await client.get(f"{api_path}/chat/{chat_1_id}", params={"user_id": user_b})
    assert chat1_res.status_code == 200
    msgs_1 = chat1_res.json()["messages"]
    assert len(msgs_1) == 1
    assert msgs_1[0]["content"] == "Hello B, this is private."

    print("[SIM] 8. Verify B cannot access Chat 2...")
    chat2_fail = await client.get(f"{api_path}/chat/{chat_2_id}", params={"user_id": user_b})
    assert chat2_fail.status_code == 403

    print("[SIM] Simulation Complete.")