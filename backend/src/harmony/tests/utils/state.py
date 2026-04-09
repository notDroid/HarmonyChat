import uuid
import random
from collections import defaultdict
from pydantic import BaseModel, Field
from typing import List, Set, Optional
from .client import SimulationActor

class SimConfig(BaseModel):
    MAX_USERS: int = Field(default=50)

class SimState:
    def __init__(self, config: SimConfig):
        self.config = config
        self._actors: List[SimulationActor] = []
        # Maps user_id -> list of chat_ids they are in
        self._user_memberships = defaultdict(list) 
        # Set of chat_ids that have had at least one message sent to them
        self._active_chats: Set[uuid.UUID] = set()

    @property
    def current_user_count(self) -> int:
        return len(self._actors)

    def add_actor(self, actor: SimulationActor):
        self._actors.append(actor)

    def remove_actor(self, actor: SimulationActor):
        """Cleanly remove an actor and their local membership records."""
        if actor in self._actors:
            self._actors.remove(actor)
        if actor.user_id in self._user_memberships:
            del self._user_memberships[actor.user_id]

    def register_chat(self, chat_id: uuid.UUID, participant_ids: List[uuid.UUID]):
        for uid in participant_ids:
            self._user_memberships[uid].append(chat_id)

    def mark_chat_active(self, chat_id: uuid.UUID):
        """Mark a chat as having messages (ready for history verification)."""
        self._active_chats.add(chat_id)

    def deregister_chat(self, chat_id: uuid.UUID):
        for uid, chats in self._user_memberships.items():
            if chat_id in chats:
                chats.remove(chat_id)
        if chat_id in self._active_chats:
            self._active_chats.remove(chat_id)
    
    def remove_chat_from_user(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        """Specific cleanup if a user leaves a chat or it becomes invalid for them."""
        if chat_id in self._user_memberships[user_id]:
            self._user_memberships[user_id].remove(chat_id)

    # ==========================
    # Queries (The "Ask" part)
    # ==========================

    def get_random_actor(self) -> Optional[SimulationActor]:
        if not self._actors:
            return None
        return random.choice(self._actors)
    
    def get_random_actors(self, count: int) -> List[SimulationActor]:
        """Safe sample of actors."""
        if not self._actors:
            return []
        safe_count = min(len(self._actors), count)
        return random.sample(self._actors, safe_count)

    def get_chat_for_user(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        chats = self._user_memberships.get(user_id, [])
        return random.choice(chats) if chats else None

    def get_active_chat_for_user(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Return a random chat for user_id that is known to have messages."""
        my_chats = set(self._user_memberships.get(user_id, []))
        candidates = list(my_chats & self._active_chats)
        return random.choice(candidates) if candidates else None

    def get_known_chats_for_user(self, user_id: uuid.UUID) -> Set[uuid.UUID]:
        """Return the set of chat IDs the simulation thinks this user has."""
        return set(self._user_memberships.get(user_id, []))

    def get_chat_user_is_NOT_in(self, user_id: uuid.UUID) -> Optional[uuid.UUID]:
        """
        Find a chat ID that exists in the system but does NOT belong 
        to the specified user_id.
        """
        my_chats = set(self._user_memberships.get(user_id, []))
        
        # Flatten all known chats from all users
        all_chats = set(
            chat_id 
            for chat_list in self._user_memberships.values() 
            for chat_id in chat_list
        )
        
        forbidden_chats = list(all_chats - my_chats)
        return random.choice(forbidden_chats) if forbidden_chats else None