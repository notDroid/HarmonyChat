import random
import uuid
from typing import List, Optional

from .client import AppClient, SimulationActor
from .state import SimState, SimConfig


class SimulationContext:
    """
    Abstract base.  Carries client + state; subclasses override the
    pick_* methods to implement their selection strategy.
    """

    def __init__(self, client: AppClient, config: Optional[SimConfig] = None):
        self.client = client
        self.state = SimState(config=config or SimConfig())

    # ------------------------------------------------------------------
    # Selection interface — override in subclasses
    # ------------------------------------------------------------------

    def pick_actor(
        self, exclude: Optional[SimulationActor] = None
    ) -> Optional[SimulationActor]:
        raise NotImplementedError

    def pick_actors(self, count: int) -> List[SimulationActor]:
        """Return up to *count* actors (may be fewer if state is small)."""
        raise NotImplementedError

    def pick_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return a chat that *actor* belongs to, or None."""
        raise NotImplementedError

    def pick_active_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return a chat that *actor* is in AND has messages, or None."""
        raise NotImplementedError

    def pick_chat_excluding(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return a chat that *actor* is NOT in, or None."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stochastic — for stress-test workers
# ---------------------------------------------------------------------------

class StochasticContext(SimulationContext):
    """
    Picks randomly.  Mirrors the behaviour of the original actions.py so
    existing stress-test action logic is preserved exactly.
    """

    def pick_actor(self, exclude=None) -> Optional[SimulationActor]:
        candidates = [a for a in self.state._actors if a is not exclude]
        return random.choice(candidates) if candidates else None

    def pick_actors(self, count: int) -> List[SimulationActor]:
        actors = self.state._actors
        if not actors:
            return []
        return random.sample(actors, min(count, len(actors)))

    def pick_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        return self.state.get_chat_for_user(actor.user_id)

    def pick_active_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        return self.state.get_active_chat_for_user(actor.user_id)

    def pick_chat_excluding(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        return self.state.get_chat_user_is_NOT_in(actor.user_id)


# ---------------------------------------------------------------------------
# Deterministic — for integration tests
# ---------------------------------------------------------------------------

class DeterministicContext(SimulationContext):
    """
    Picks actors by a cursor index; always returns the same actor for the
    same cursor position, making tests reproducible.

    Usage pattern
    -------------
    ctx = DeterministicContext(client, SimConfig(MAX_USERS=10))

    # Run actions that auto-pick via the cursor
    actor_a = await ACTION_REGISTRY["create_user"]["func"](ctx)   # cursor → 0
    actor_b = await ACTION_REGISTRY["create_user"]["func"](ctx)   # cursor → 1

    # Point the cursor at a specific actor for the next action(s)
    ctx.focus(2)
    await ACTION_REGISTRY["fail_unauthorized_read"]["func"](ctx)

    # Advance one step
    ctx.advance()

    # Or bypass the registry and call helpers directly
    ctx.actor(0)   # → actors[0]
    ctx.actor(1)   # → actors[1]
    """

    def __init__(self, client: AppClient, config: Optional[SimConfig] = None):
        super().__init__(client, config)
        self._cursor: int = 0

    # ---- Cursor control --------------------------------------------------

    def focus(self, index: int) -> "DeterministicContext":
        """Point cursor at *index*.  Returns self for chaining."""
        self._cursor = index
        return self

    def advance(self, steps: int = 1) -> "DeterministicContext":
        """Move cursor forward by *steps* (wraps around).  Returns self."""
        if self.state._actors:
            self._cursor = (self._cursor + steps) % len(self.state._actors)
        return self

    # ---- Direct actor access (bypasses registry, useful in test bodies) --

    def actor(self, index: int) -> SimulationActor:
        """Return actors[index] directly.  Raises IndexError if out of range."""
        return self.state._actors[index]

    # ---- SimulationContext interface -------------------------------------

    def pick_actor(self, exclude=None) -> Optional[SimulationActor]:
        actors = self.state._actors
        if not actors:
            return None
        if exclude is None:
            return actors[self._cursor % len(actors)]
        # Walk forward from cursor to find a non-excluded actor
        for i in range(len(actors)):
            candidate = actors[(self._cursor + i) % len(actors)]
            if candidate is not exclude:
                return candidate
        return None

    def pick_actors(self, count: int) -> List[SimulationActor]:
        """
        Return up to *count* actors starting from the cursor (no duplicates,
        wraps if needed but stops at len(actors)).
        """
        actors = self.state._actors
        if not actors:
            return []
        n = min(count, len(actors))
        return [actors[(self._cursor + i) % len(actors)] for i in range(n)]

    def pick_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return the FIRST known chat for *actor* (stable, not random)."""
        chats = self.state._user_memberships.get(actor.user_id, [])
        return chats[0] if chats else None

    def pick_active_chat_for(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return the FIRST active chat for *actor*."""
        my_chats = set(self.state._user_memberships.get(actor.user_id, []))
        candidates = sorted(list(my_chats & self.state._active_chats), key=str)
        return candidates[0] if candidates else None

    def pick_chat_excluding(self, actor: SimulationActor) -> Optional[uuid.UUID]:
        """Return the FIRST chat in the system that *actor* is NOT in."""
        my_chats = set(self.state._user_memberships.get(actor.user_id, []))
        all_chats = {
            cid
            for memberships in self.state._user_memberships.values()
            for cid in memberships
        }
        others = sorted(all_chats - my_chats, key=str)  # sorted for stability
        return others[0] if others else None
