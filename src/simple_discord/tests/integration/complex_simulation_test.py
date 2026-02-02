import pytest
import random
import uuid
from httpx import AsyncClient

# --- 1. Global Simulation Controls ---
# Change this to make the simulation longer or shorter
SIMULATION_STEPS = 100
# Weights determine how likely an action is (User, Chat, Talk, Read, Spy)
ACTION_WEIGHTS = [5, 10, 40, 25, 20] 

class SimulationState:
    """Keeps track of the 'World' so we don't request non-existent IDs."""
    def __init__(self):
        self.users = []  # List of user_ids
        self.chats = {}  # Map: chat_id -> list of member_user_ids
        self.history = {} # Map: chat_id -> list of message strings (for verification)

    def get_random_user(self):
        return random.choice(self.users) if self.users else None

    def get_random_chat(self):
        if not self.chats:
            return None, None
        chat_id = random.choice(list(self.chats.keys()))
        return chat_id, self.chats[chat_id]

# --- 2. Action Helpers ---

async def action_create_user(client: AsyncClient, api_path: str, state: SimulationState):
    """Creates a new unique user."""
    name = f"User_{str(uuid.uuid4())[:6]}"
    res = await client.post(f"{api_path}/user/", json={
        "username": name,
        "email": f"{name}@example.com"
    })
    assert res.status_code == 200
    user_id = res.json()["user_id"]
    state.users.append(user_id)
    print(f"   [ACTION] Created User: {name} ({user_id})")

async def action_create_chat(client: AsyncClient, api_path: str, state: SimulationState):
    """Creates a chat between 2-4 random existing users."""
    if len(state.users) < 2:
        return # Not enough people to chat yet
    
    # Pick 2 to 4 distinct users
    participants = random.sample(state.users, k=random.randint(2, min(4, len(state.users))))
    
    res = await client.post(f"{api_path}/chat/", json={"user_id_list": participants})
    assert res.status_code == 200
    
    chat_id = res.json()["chat_id"]
    state.chats[chat_id] = participants
    state.history[chat_id] = []
    print(f"   [ACTION] Created Chat {chat_id} with {len(participants)} members.")

async def action_send_message(client: AsyncClient, api_path: str, state: SimulationState):
    """A random member sends a message to a random chat."""
    chat_id, members = state.get_random_chat()
    if not chat_id: return

    sender = random.choice(members)
    msg_content = f"Msg_{uuid.uuid4().hex[:8]}"
    
    res = await client.post(
        f"{api_path}/chat/{chat_id}", 
        json={"user_id": sender, "content": msg_content}
    )
    assert res.status_code == 201
    
    # Update our local truth for verification later
    state.history[chat_id].append(msg_content)
    print(f"   [ACTION] User {sender} sent '{msg_content}' to Chat {chat_id}")

async def action_read_history(client: AsyncClient, api_path: str, state: SimulationState):
    """A valid member reads chat history; we verify it matches local truth."""
    chat_id, members = state.get_random_chat()
    if not chat_id: return

    reader = random.choice(members)
    
    res = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": reader})
    assert res.status_code == 200
    
    api_messages = [m["content"] for m in res.json()["messages"]]
    # Verify API returns exactly what we tracked in SimulationState
    assert api_messages == state.history[chat_id]
    print(f"   [VERIFY] User {reader} successfully verified history for Chat {chat_id}")

async def action_spy_attempt(client: AsyncClient, api_path: str, state: SimulationState):
    """A user NOT in the chat tries to read it. MUST FAIL (403)."""
    chat_id, members = state.get_random_chat()
    if not chat_id: return

    # Find users who are NOT in this chat
    outsiders = [u for u in state.users if u not in members]
    if not outsiders:
        return # Everyone is in this chat, cannot spy
    
    spy = random.choice(outsiders)
    
    res = await client.get(f"{api_path}/chat/{chat_id}", params={"user_id": spy})
    
    # CRITICAL: This must fail
    assert res.status_code == 403
    print(f"   [SECURITY] Spy {spy} was correctly blocked from Chat {chat_id}")

# --- 3. The Test Runner ---

@pytest.mark.asyncio
async def test_complex_simulation(client: AsyncClient, api_path: str):
    print(f"\n\n--- STARTING SIMULATION ({SIMULATION_STEPS} Steps) ---")
    
    # Initialize State
    sim_state = SimulationState()
    
    # Step 0: Seed the world with minimum 3 users to ensure flow
    print("[INIT] Seeding initial users...")
    for _ in range(3):
        await action_create_user(client, api_path, sim_state)

    # Simulation Loop
    actions = [
        action_create_user, 
        action_create_chat, 
        action_send_message, 
        action_read_history, 
        action_spy_attempt
    ]

    for i in range(SIMULATION_STEPS):
        print(f"\nStep {i+1}/{SIMULATION_STEPS}:", end=" ")
        
        # Pick an action based on weights
        chosen_action = random.choices(actions, weights=ACTION_WEIGHTS, k=1)[0]
        
        # Execute
        await chosen_action(client, api_path, sim_state)

    print(f"\n--- SIMULATION COMPLETE. Verified {len(sim_state.chats)} chats and {len(sim_state.users)} users. ---")