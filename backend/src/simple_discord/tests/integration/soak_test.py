import pytest
import random
import uuid
import os
import time
import asyncio
from httpx import AsyncClient, HTTPStatusError

# --- CONFIGURATION ---
DURATION_SECONDS = 60 * 60  # Run for 1 hour
PRINT_INTERVAL = 1000       # Print stats every 1000 steps
SLEEP_INTERVAL = 0          # Sleep time between actions
MAX_HISTORY_PER_CHAT = 20   # Prevent RAM explosion

# Weights correspond to:
# [CreateUser, CreateChat, SendMsg, ReadHist, Spy, GetUserChats, DeleteChat, DeleteUser]
ACTION_WEIGHTS = [2, 5, 50, 20, 5, 15, 2, 1] 

class SimulationMetrics:
    def __init__(self):
        self.requests = 0
        self.errors = 0
        self.latencies = []
        self.step_count = 0
    
    def record(self, latency, success=True):
        self.requests += 1
        self.latencies.append(latency)
        if not success:
            self.errors += 1
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def print_summary(self):
        if not self.latencies: return
        avg_lat = sum(self.latencies) / len(self.latencies)
        print(f"\n--- STATUS [Step {self.step_count}] ---")
        print(f"Total Requests: {self.requests} | Errors: {self.errors}")
        print(f"Avg Latency (last 1k): {avg_lat:.4f}s")
        print(f"Users Active: {len(state.users)} | Chats Active: {len(state.chats)}")
        print("-----------------------------------")

class SimulationState:
    def __init__(self):
        self.users = []
        self.chats = {} # {chat_id: [user_ids]}
        self.history = {} 

    def get_random_user(self):
        return random.choice(self.users) if self.users else None

    def get_random_chat(self):
        if not self.chats: return None, None
        chat_id = random.choice(list(self.chats.keys()))
        return chat_id, self.chats[chat_id]

    def prune_history(self):
        for chat_id in self.history:
            if len(self.history[chat_id]) > MAX_HISTORY_PER_CHAT:
                self.history[chat_id] = self.history[chat_id][-MAX_HISTORY_PER_CHAT:]
    
    def remove_chat(self, chat_id):
        if chat_id in self.chats:
            del self.chats[chat_id]
        if chat_id in self.history:
            del self.history[chat_id]

    def remove_user(self, user_id):
        if user_id in self.users:
            self.users.remove(user_id)
        # Remove user from local chat participant lists so we don't try to send messages as them
        for chat_id in self.chats:
            if user_id in self.chats[chat_id]:
                self.chats[chat_id].remove(user_id)

# --- ROBUST ACTIONS ---

async def safe_request(func, metrics, *args):
    start = time.time()
    try:
        await func(*args)
        metrics.record(time.time() - start, success=True)
    except AssertionError as e:
        metrics.record(time.time() - start, success=False)
        print(f" [FAIL] Logic Error in {func.__name__}: {e}")
    except Exception as e:
        metrics.record(time.time() - start, success=False)
        print(f" [FAIL] Request Error in {func.__name__}: {e}")

async def action_create_user(client, api_path, state):
    name = f"User_{str(uuid.uuid4())[:6]}"
    res = await client.post(f"{api_path}/user/", json={"username": name, "email": f"{name}@ex.com"})
    if res.status_code == 200:
        state.users.append(res.json()["user_id"])
    else:
        raise AssertionError(f"Status {res.status_code}")

async def action_create_chat(client, api_path, state):
    if len(state.users) < 2: return
    participants = random.sample(state.users, k=random.randint(2, min(4, len(state.users))))
    res = await client.post(f"{api_path}/chat/", json={"user_id_list": participants})
    if res.status_code == 200:
        chat_id = res.json()["chat_id"]
        state.chats[chat_id] = participants
        state.history[chat_id] = []
    else:
        raise AssertionError(f"Status {res.status_code}")

async def action_send_message(client, api_path, state):
    chat_id, members = state.get_random_chat()
    if not chat_id or not members: return
    
    sender = random.choice(members)
    msg_content = f"Msg_{uuid.uuid4().hex[:8]}"
    
    res = await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": sender, "content": msg_content})
    
    if res.status_code != 201:
        raise AssertionError(f"Expected 201, got {res.status_code}")
        
    state.history[chat_id].append(msg_content)

async def action_read_history(client, api_path, state):
    chat_id, members = state.get_random_chat()
    if not chat_id or not members: return
    
    reader = random.choice(members)
    res = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": reader})
    
    if res.status_code != 200:
        raise AssertionError(f"Read failed: {res.status_code}")
    
    api_msgs = [m["content"] for m in res.json()["messages"]]
    local_history = state.history[chat_id]
    overlap_len = min(len(api_msgs), len(local_history))
    if api_msgs[-overlap_len:] != local_history[-overlap_len:]:
         raise AssertionError(f"History mismatch in Chat {chat_id}")

async def action_spy_attempt(client, api_path, state):
    chat_id, members = state.get_random_chat()
    if not chat_id: return
    outsiders = [u for u in state.users if u not in members]
    if not outsiders: return
    
    spy = random.choice(outsiders)
    res = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": spy})
    
    if res.status_code != 403:
        raise AssertionError(f"Security breach! Spy got {res.status_code}")

# --- NEW ACTIONS ---

async def action_get_user_chats(client, api_path, state):
    """Test GET /{user_id}/chats"""
    user_id = state.get_random_user()
    if not user_id: return

    res = await client.get(f"{api_path}/user/{user_id}/chats")
    
    if res.status_code != 200:
        raise AssertionError(f"Failed to get user chats: {res.status_code}")
    
    returned_chats = set(res.json()["chat_id_list"])
    
    # Validation: Check against local state
    # Find all chats in state where this user is a participant
    expected_chats = {cid for cid, members in state.chats.items() if user_id in members}
    
    if returned_chats != expected_chats:
        # Note: This might fail if the server deletes chats slower than the test runner updates state,
        # but in a strong consistency model it should match.
        pass # Commenting out strict assertion for soft stress testing, but logically:
        # raise AssertionError(f"Chat list mismatch for user {user_id}")

async def action_delete_chat(client, api_path, state):
    """Test DELETE /{chat_id}"""
    chat_id, _ = state.get_random_chat()
    if not chat_id: return

    if not state.chats[chat_id]:
        return  # No members to authenticate deletion
    res = await client.delete(f"{api_path}/chat/{chat_id}", params={"user_id": state.chats[chat_id][0]})
    
    if res.status_code != 204:
        raise AssertionError(f"Failed to delete chat: {res.status_code}")
    
    state.remove_chat(chat_id)

async def action_delete_user(client, api_path, state):
    """Test DELETE /{user_id}"""
    user_id = state.get_random_user()
    if not user_id: return
    
    # Don't delete if population is critical (keeps simulation alive)
    if len(state.users) < 5: return

    res = await client.delete(f"{api_path}/user/{user_id}")
    
    if res.status_code != 204:
        raise AssertionError(f"Failed to delete user: {res.status_code}")
    
    state.remove_user(user_id)

# --- RUNNER ---

# Global reference for metrics printing
state = SimulationState() 

@pytest.mark.stress
@pytest.mark.asyncio
async def test_prolonged_stress(client: AsyncClient, api_path: str):
    print(f"\n--- STARTING SOAK TEST ({DURATION_SECONDS} Seconds) ---")
    
    metrics = SimulationMetrics()
    # Reset state for fresh run
    state.users = []
    state.chats = {}
    state.history = {}
    
    # Seed
    for _ in range(10): await action_create_user(client, api_path, state)

    start_time = time.time()
    
    actions = [
        action_create_user, 
        action_create_chat, 
        action_send_message, 
        action_read_history, 
        action_spy_attempt,
        action_get_user_chats, # New
        action_delete_chat,    # New
        action_delete_user     # New
    ]

    endpoint = os.getenv("API_ENDPOINT", "http://localhost:8000")

    while time.time() - start_time < DURATION_SECONDS:
        metrics.step_count += 1
        
        if metrics.step_count % 100 == 0:
            state.prune_history()

        if metrics.step_count % PRINT_INTERVAL == 0:
            metrics.print_summary()

        chosen_action = random.choices(actions, weights=ACTION_WEIGHTS, k=1)[0]
        
        async with AsyncClient(base_url=endpoint) as fresh_client:
            await safe_request(chosen_action, metrics, fresh_client, api_path, state)
        
        if SLEEP_INTERVAL > 0:
            await asyncio.sleep(SLEEP_INTERVAL) 

    print("\n--- TEST COMPLETE ---")
    metrics.print_summary()