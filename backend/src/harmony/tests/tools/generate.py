import pytest
import asyncio
import json
import os
import random
import logging
from typing import List, Dict

from harmony.tests.utils import AppClient, SimulationActor
from harmony.tests.utils.data_gen import generate_user_data, generate_chat_message

# ==========================================
# CONFIGURATION
# ==========================================
SEED_FILE = "generated_data.json"
TARGET_USERS = 10
TARGET_CHATS = 100
LIVE_DELAY_MIN = 0.01
LIVE_DELAY_MAX = 0.5

logger = logging.getLogger(__name__)

class PersistentSimManager:
    """
    Manages state persistence to JSON and re-hydration of Actors.
    """
    def __init__(self, client: AppClient):
        self.client = client
        self.actors: List[SimulationActor] = []
        self.chats: List[Dict] = [] # List of {"chat_id": str, "participants": [uid, uid]}

    def load_state(self):
        if not os.path.exists(SEED_FILE):
            print(f"[{SEED_FILE}] not found. Starting fresh.")
            return False

        try:
            with open(SEED_FILE, 'r') as f:
                data = json.load(f)
                
            print(f"Loading {len(data['users'])} users and {len(data['chats'])} chats from disk...")
            
            # Recreate Actor objects (tokens are fetched separately)
            for u in data['users']:
                actor = SimulationActor(
                    user_id=u['user_id'],
                    username=u['username'],
                    email=u['email'],
                    password=u['password'],
                    client=self.client
                )
                self.actors.append(actor)
            
            self.chats = data.get('chats', [])
            return True
        except Exception as e:
            print(f"Failed to load state: {e}. Starting fresh.")
            return False

    def save_state(self):
        data = {
            "users": [
                {
                    "user_id": a.user_id,
                    "username": a.username,
                    "email": a.email,
                    "password": a.password
                } for a in self.actors
            ],
            "chats": self.chats
        }
        with open(SEED_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"State saved to {os.path.abspath(SEED_FILE)}")

    async def rehydrate_actors(self):
        """
        Logs in all loaded actors to get fresh JWT tokens.
        """
        print("Re-authenticating loaded users...")
        valid_actors = []
        for actor in self.actors:
            try:
                await actor.login()
                valid_actors.append(actor)
            except Exception as e:
                print(f"Could not login user {actor.username} (might be deleted from DB): {e}")
        
        self.actors = valid_actors
        self.save_state() # Update state to remove invalid users

    async def seed_missing_users(self):
        current_count = len(self.actors)
        needed = TARGET_USERS - current_count
        
        if needed <= 0:
            return

        print(f"Seeding {needed} new users...")
        for _ in range(needed):
            raw_data = generate_user_data()
            try:
                # 1. Create on Backend
                uid = await self.client.create_user(**raw_data)
                
                # 2. Create Object & Login
                actor = SimulationActor(
                    user_id=uid,
                    username=raw_data['username'],
                    email=raw_data['email'],
                    password=raw_data['password'],
                    client=self.client
                )
                await actor.login()
                self.actors.append(actor)
            except Exception as e:
                print(f"Error creating user: {e}")
        
        self.save_state()

    async def seed_missing_chats(self):
        if len(self.chats) >= TARGET_CHATS:
            return

        print("Seeding initial chats...")
        while len(self.chats) < TARGET_CHATS:
            # Pick random participants (2 to 4)
            participants = random.sample(self.actors, k=random.randint(2, min(4, len(self.actors))))
            creator = participants[0]
            others = participants[1:]
            
            try:
                chat_id = await creator.create_chat_with(others)
                self.chats.append({
                    "chat_id": chat_id,
                    "participant_ids": [p.user_id for p in participants]
                })
                print(f"Created chat {chat_id} with {len(participants)} users.")
            except Exception as e:
                print(f"Error creating chat: {e}")
        
        self.save_state()

    def get_chats_for_actor(self, actor_id: str) -> List[str]:
        return [c['chat_id'] for c in self.chats if actor_id in c['participant_ids']]


# ==========================================
# LIVE SIMULATION LOOP
# ==========================================
async def live_chatter(manager: PersistentSimManager):
    """
    Infinite loop that picks a random user and sends a message
    to one of their chats.
    """
    print("\n--- STARTING LIVE CHATTER ---")
    print("Use Ctrl+C to stop. Data is saved.")
    
    # Removed hardcoded messages list

    try:
        while True:
            # 1. Pick random actor
            actor = random.choice(manager.actors)
            
            # 2. Find a chat they belong to
            my_chat_ids = manager.get_chats_for_actor(actor.user_id)
            
            if my_chat_ids:
                chat_id = random.choice(my_chat_ids)
                content = generate_chat_message()  # <--- Now using Faker
                
                try:
                    await actor.send_message(chat_id, content)
                    print(f"[{actor.username}] sent msg to [{chat_id[:8]}]: {content[:30]}...")
                except Exception as e:
                    print(f"Error sending message: {e}")
            
            # 3. Wait randomly
            delay = random.uniform(LIVE_DELAY_MIN, LIVE_DELAY_MAX)
            await asyncio.sleep(delay)
            
    except asyncio.CancelledError:
        print("Stopping chatter...")


# ==========================================
# TEST ENTRY POINT
# ==========================================
@pytest.mark.stress
@pytest.mark.asyncio
async def test_live_simulation_seed(app_client: AppClient):
    """
    1. Loads or Creates Users/Chats.
    2. Saves credentials to 'frontend_seed_data.json'.
    3. Runs an infinite loop generating messages.
    """
    manager = PersistentSimManager(app_client)

    # 1. Initialization Phase
    if manager.load_state():
        await manager.rehydrate_actors()
    
    await manager.seed_missing_users()
    
    if len(manager.actors) < 2:
        print("Not enough users to create chats.")
        return

    await manager.seed_missing_chats()

    # 2. Output Credentials for Developer
    print("\n" + "="*40)
    print(" TEST DATA READY ")
    print("="*40)
    print(f"Data file: {os.path.abspath(SEED_FILE)}")
    print(f"Total Users: {len(manager.actors)}")
    print(f"Total Chats: {len(manager.chats)}")
    print("-" * 40)
    print("SAMPLE ACCOUNTS (Login with these):")
    for i in range(min(3, len(manager.actors))):
        u = manager.actors[i]
        print(f"User: {u.email}  |  Pass: {u.password}")
    print("="*40 + "\n")

    # 3. Live Phase
    # We use a task here so pytest can handle keyboard interrupts gracefully if needed,
    # though usually Ctrl+C in pytest just kills it.
    await live_chatter(manager)