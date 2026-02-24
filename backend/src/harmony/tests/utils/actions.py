import uuid
import random
from httpx import HTTPStatusError

from harmony.tests.utils.client import AppClient, SimulationActor
from harmony.tests.utils.data_gen import generate_user_data
from .state import SimState

# ==========================================
# ACTION REGISTRY
# ==========================================
ACTION_REGISTRY = {}

def simulation_action(name: str, weight: int):
    def decorator(func):
        ACTION_REGISTRY[name] = {"func": func, "weight": weight, "name": name}
        return func
    return decorator

# ==========================================
# HAPPY PATH ACTIONS
# ==========================================

@simulation_action(name="create_user", weight=10)
async def action_create_user(client: AppClient, state: SimState):
    if state.current_user_count >= state.config.MAX_USERS:
        return 
        
    data = generate_user_data()
    uid = await client.create_user(**data)
    
    actor = SimulationActor(
        user_id=uid, 
        username=data['username'], 
        email=data['email'],
        password=data['password'],
        client=client
    )
    await actor.login()
    state.add_actor(actor)

@simulation_action(name="create_chat", weight=20)
async def action_create_chat(client: AppClient, state: SimState):
    users = state.get_random_actors(random.randint(2, 6))
    if len(users) < 2: return
    
    creator = users[0]
    others = users[1:]
    
    chat_id = await creator.create_chat_with(others)
    state.register_chat(chat_id, [u.user_id for u in users])

@simulation_action(name="send_message", weight=50)
async def action_send_message(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    chat_id = state.get_chat_for_user(actor.user_id)
    if chat_id:
        await actor.send_message(chat_id, "Happy path payload")

@simulation_action(name="read_history", weight=40)
async def action_read_history(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    chat_id = state.get_chat_for_user(actor.user_id)
    if chat_id:
        await actor.get_history(chat_id)

# ==========================================
# SAD PATH / FAILURE SCENARIO ACTIONS
# ==========================================

@simulation_action(name="fail_unauthorized_read", weight=15)
async def action_fail_unauthorized_read(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    target_chat_id = state.get_chat_user_is_NOT_in(actor.user_id)
    if not target_chat_id: return 

    try:
        await actor.get_history(target_chat_id)
        raise Exception(f"CRITICAL: User {actor.username} read chat {target_chat_id} without permission!")
    except HTTPStatusError as e:
        if e.response.status_code not in [403, 404]:
            raise Exception(f"Unexpected status on unauthorized read: {e.response.status_code}")

@simulation_action(name="fail_message_nonexistent_chat", weight=10)
async def action_fail_message_ghost_chat(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    fake_chat_id = uuid.uuid4()
    try:
        await actor.send_message(fake_chat_id, "Hello void")
        raise Exception(f"API accepted message to non-existent chat! {fake_chat_id}")
    except HTTPStatusError as e:
        if e.response.status_code not in [403, 404]:
            raise Exception(f"Unexpected status for ghost chat: {e.response.status_code}")

@simulation_action(name="chaos_delete_user", weight=5)
async def action_chaos_delete_user(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor or state.current_user_count <= 1: return

    try:
        await actor.delete_self()
        state.remove_actor(actor)
    except HTTPStatusError as e:
        raise Exception(f"Failed to delete user {actor.user_id}: {e}")

@simulation_action(name="fail_message_deleted_user", weight=10)
async def action_fail_message_deleted_user(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    chat_id = state.get_chat_for_user(actor.user_id)
    if not chat_id: return

    try:
        await actor.send_message(chat_id, "Are you still there?")
    except HTTPStatusError as e:
        if e.response.status_code in [403, 404]:
            state.remove_chat_from_user(actor.user_id, chat_id)
        else:
            raise e
        
@simulation_action(name="delete_chat", weight=5)
async def action_delete_chat(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    chat_id = state.get_chat_for_user(actor.user_id)
    if not chat_id: return

    try:
        await actor.delete_chat(chat_id)
        state.deregister_chat(chat_id) 
    except HTTPStatusError as e:
        if e.response.status_code not in [403, 404]:
            raise Exception(f"Unexpected error deleting chat {chat_id}: {e}")
        
@simulation_action(name="validate_chat_list", weight=10)
async def action_validate_chat_list(client: AppClient, state: SimState):
    actor = state.get_random_actor()
    if not actor: return

    try:
        real_chat_ids = set(await actor.get_my_chats())
        expected_chat_ids = state.get_known_chats_for_user(actor.user_id)
        
        if real_chat_ids != expected_chat_ids:
            raise Exception(
                f"Sync Error User {actor.username}: "
                f"API={len(real_chat_ids)} vs Sim={len(expected_chat_ids)}"
            )
    except HTTPStatusError as e:
        raise Exception(f"Failed to fetch my chats: {e}")