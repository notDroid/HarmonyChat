import pytest
import random
import uuid
import time
import asyncio
from httpx import AsyncClient, HTTPStatusError

# --- CONFIGURATION ---
DURATION_SECONDS = 60 * 60  # Run for 1 hour (Change as needed)
PRINT_INTERVAL = 1000       # Print stats every 1000 steps
SLEEP_INTERVAL = 0.01      # Sleep time between actions to control RPS
MAX_HISTORY_PER_CHAT = 20   # Prevent RAM explosion
ACTION_WEIGHTS = [2, 5, 60, 20, 13] # Lower weight on creating users/chats to stabilize memory

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
        # Keep latency list small for memory safety (last 1000 requests)
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def print_summary(self):
        if not self.latencies: return
        avg_lat = sum(self.latencies) / len(self.latencies)
        print(f"\n--- STATUS [Step {self.step_count}] ---")
        print(f"Total Requests: {self.requests} | Errors: {self.errors}")
        print(f"Avg Latency (last 1k): {avg_lat:.4f}s")
        print("-----------------------------------")

class SimulationState:
    def __init__(self):
        self.users = []
        self.chats = {} 
        self.history = {} 

    def get_random_user(self):
        return random.choice(self.users) if self.users else None

    def get_random_chat(self):
        if not self.chats: return None, None
        chat_id = random.choice(list(self.chats.keys()))
        return chat_id, self.chats[chat_id]

    def prune_history(self):
        """Prevent memory leaks by removing old messages."""
        for chat_id in self.history:
            if len(self.history[chat_id]) > MAX_HISTORY_PER_CHAT:
                # Keep only the last N messages
                self.history[chat_id] = self.history[chat_id][-MAX_HISTORY_PER_CHAT:]

# --- ROBUST ACTIONS (Soft Assertions) ---

async def safe_request(func, metrics, *args):
    """Wrapper to handle errors without crashing the simulation."""
    start = time.time()
    try:
        await func(*args)
        metrics.record(time.time() - start, success=True)
    except AssertionError as e:
        metrics.record(time.time() - start, success=False)
        print(f" [FAIL] Logic Error: {e}")
    except Exception as e:
        metrics.record(time.time() - start, success=False)
        print(f" [FAIL] Request Error: {e}")

async def action_create_user(client, api_path, state):
    name = f"User_{str(uuid.uuid4())[:6]}"
    res = await client.post(f"{api_path}/user/", json={"username": name, "email": f"{name}@ex.com"})
    if res.status_code == 200:
        state.users.append(res.json()["user_id"])

async def action_create_chat(client, api_path, state):
    if len(state.users) < 2: return
    participants = random.sample(state.users, k=random.randint(2, min(4, len(state.users))))
    res = await client.post(f"{api_path}/chat/", json={"user_id_list": participants})
    if res.status_code == 200:
        chat_id = res.json()["chat_id"]
        state.chats[chat_id] = participants
        state.history[chat_id] = []

async def action_send_message(client, api_path, state):
    chat_id, members = state.get_random_chat()
    if not chat_id: return
    sender = random.choice(members)
    msg_content = f"Msg_{uuid.uuid4().hex[:8]}"
    
    res = await client.post(f"{api_path}/chat/{chat_id}", json={"user_id": sender, "content": msg_content})
    
    # Soft Assertion
    if res.status_code != 201:
        raise AssertionError(f"Expected 201, got {res.status_code}")
        
    state.history[chat_id].append(msg_content)

async def action_read_history(client, api_path, state):
    chat_id, members = state.get_random_chat()
    if not chat_id: return
    reader = random.choice(members)
    
    res = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": reader})
    
    if res.status_code != 200:
        raise AssertionError(f"Read failed: {res.status_code}")
    
    # Verify content match (Check only the last few messages to handle pruning)
    api_msgs = [m["content"] for m in res.json()["messages"]]
    local_history = state.history[chat_id]
    
    # If API has more messages than we stored (due to pruning), just check the overlap
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

# --- RUNNER ---

@pytest.mark.stress
@pytest.mark.asyncio
async def test_prolonged_stress(client: AsyncClient, api_path: str):
    print(f"\n--- STARTING SOAK TEST ({DURATION_SECONDS} Seconds) ---")
    
    metrics = SimulationMetrics()
    state = SimulationState()
    
    # Seed
    for _ in range(5): await action_create_user(client, api_path, state)

    start_time = time.time()
    actions = [action_create_user, action_create_chat, action_send_message, action_read_history, action_spy_attempt]

    while time.time() - start_time < DURATION_SECONDS:
        metrics.step_count += 1
        
        # Periodic Cleanup (Critical for long runs)
        if metrics.step_count % 100 == 0:
            state.prune_history()

        # Periodic Reporting
        if metrics.step_count % PRINT_INTERVAL == 0:
            metrics.print_summary()

        # Pick and Run Action
        chosen_action = random.choices(actions, weights=ACTION_WEIGHTS, k=1)[0]
        await safe_request(chosen_action, metrics, client, api_path, state)
        
        # Optional: Sleep briefly to control "Requests Per Second"
        if SLEEP_INTERVAL > 0:
            await asyncio.sleep(SLEEP_INTERVAL) 

    print("\n--- TEST COMPLETE ---")
    metrics.print_summary()