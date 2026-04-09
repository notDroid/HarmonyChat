"""
Action registry for simulation-based integration and stress tests.

Eventual-consistency note
-------------------------
Several "verify" actions send a write and then immediately read back to confirm
the result.  In a distributed backend (replicated DB, message queue, read
replica) the GET may hit a node that hasn't yet received the write.

All such read-after-write checks are wrapped with ``poll_until`` so they retry
with exponential back-off rather than failing on the first stale read.

Security-boundary actions (fail_unauthorized_*) are intentionally NOT retried —
a 403/404 must come back on the first request or it's a real violation.
"""

import random
import uuid
from typing import Optional

from httpx import HTTPStatusError

from .simulation import SimulationContext
from .client import SimulationActor
from .data_gen import generate_user_data, generate_chat_message
from .retry import poll_until


# ---------------------------------------------------------------------------
# Registry + decorator
# ---------------------------------------------------------------------------

ACTION_REGISTRY: dict = {}


def simulation_action(name: str, weight: int):
    """Register an action function with a name and stress-test weight."""
    def decorator(func):
        ACTION_REGISTRY[name] = {"func": func, "weight": weight, "name": name}
        return func
    return decorator


# ===========================================================================
# HAPPY PATH
# ===========================================================================

@simulation_action("create_user", weight=10)
async def action_create_user(ctx: SimulationContext) -> Optional[SimulationActor]:
    """Create a new user, log them in, and register them in sim state."""
    if ctx.state.current_user_count >= ctx.state.config.MAX_USERS:
        return None

    data = generate_user_data()
    uid = await ctx.client.create_user(**data)
    actor = SimulationActor(
        user_id=uid,
        username=data["username"],
        email=data["email"],
        password=data["password"],
        client=ctx.client,
    )
    await actor.login()
    ctx.state.add_actor(actor)
    return actor


@simulation_action("create_chat", weight=20)
async def action_create_chat(ctx: SimulationContext) -> Optional[uuid.UUID]:
    """
    Pick 2–6 actors via the context's strategy and have the first one create
    a group chat with the rest.  Registers participants in sim state.
    """
    # cap at 6 for stress; DeterministicContext.pick_actors caps at len(actors)
    users = ctx.pick_actors(random.randint(2, 6))
    if len(users) < 2:
        return None

    creator, others = users[0], users[1:]
    chat_id = await creator.create_chat_with(others)
    ctx.state.register_chat(chat_id, [u.user_id for u in users])
    return chat_id


@simulation_action("send_message", weight=50)
async def action_send_message(ctx: SimulationContext):
    """Send a message to one of the current actor's chats."""
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_chat_for(actor)
    if not chat_id:
        return None
    content = generate_chat_message()
    res = await actor.send_message(chat_id, content)
    ctx.state.mark_chat_active(chat_id)
    return res


@simulation_action("read_history", weight=40)
async def action_read_history(ctx: SimulationContext):
    """Fetch message history for one of the current actor's chats."""
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_chat_for(actor)
    if not chat_id:
        return None
    return await actor.get_history(chat_id)


@simulation_action("delete_chat", weight=5)
async def action_delete_chat(ctx: SimulationContext) -> Optional[uuid.UUID]:
    """Delete one of the current actor's chats and deregister it from state."""
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_chat_for(actor)
    if not chat_id:
        return None

    try:
        await actor.delete_chat(chat_id)
        ctx.state.deregister_chat(chat_id)
        return chat_id
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            raise AssertionError(
                f"Unexpected error deleting chat {chat_id}: {exc.response.status_code}"
            ) from exc
    return None


@simulation_action("chaos_delete_user", weight=5)
async def action_chaos_delete_user(ctx: SimulationContext) -> Optional[SimulationActor]:
    """Delete a random actor (chaos action — keeps at least 1 user alive)."""
    actor = ctx.pick_actor()
    if not actor or ctx.state.current_user_count <= 1:
        return None

    try:
        await actor.delete_self()
        ctx.state.remove_actor(actor)
        return actor
    except HTTPStatusError as exc:
        raise AssertionError(
            f"Failed to delete user {actor.user_id}: {exc.response.status_code}"
        ) from exc


# ===========================================================================
# VERIFICATION — useful for deterministic sequences
# ===========================================================================

@simulation_action("send_and_verify_message", weight=30)
async def action_send_and_verify_message(ctx: SimulationContext) -> Optional[str]:
    """
    Send a message then poll until it appears in history.

    The send itself is a single best-effort call.  The read-back is wrapped in
    ``poll_until`` because, in a distributed system, the write may be queued
    (e.g. via Kafka/Redpanda) and not immediately visible on the read path.

    Raises AssertionError if the content is still missing after the retry
    window expires — which indicates a real correctness bug, not propagation
    lag.
    """
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_chat_for(actor)
    if not chat_id:
        return None

    content = generate_chat_message()
    await actor.send_message(chat_id, content)
    ctx.state.mark_chat_active(chat_id)

    async def _check_history():
        history = await actor.get_history(chat_id)
        contents = [m.content for m in history]
        assert any(content in c for c in contents), (
            f"[send_and_verify] Sent '{content}' to chat {chat_id} "
            f"but it is not yet in history. Got: {contents}"
        )

    await poll_until(_check_history, label="send_and_verify_message")
    return content


@simulation_action("verify_chat_membership", weight=10)
async def action_verify_chat_membership(ctx: SimulationContext) -> None:
    """
    Assert that the actor's real API chat list exactly matches what the
    simulation believes the actor belongs to.

    Polled because the chat list endpoint may be served by a read replica
    that lags behind after ``create_chat``.
    """
    actor = ctx.pick_actor()
    if not actor:
        return None

    # Snapshot local expected state before entering the retry loop so the
    # comparison target stays stable across retries.
    expected_ids = ctx.state.get_known_chats_for_user(actor.user_id)

    async def _check_membership():
        real_ids = set(await actor.get_my_chats())
        assert real_ids == expected_ids, (
            f"[verify_membership] Sync error for '{actor.username}': "
            f"API has {len(real_ids)} chats, sim expects {len(expected_ids)}.\n"
            f"  Extra in API:   {real_ids - expected_ids}\n"
            f"  Missing in API: {expected_ids - real_ids}"
        )

    await poll_until(_check_membership, label="verify_chat_membership")


# kept as alias so existing Taskfile / CI references still work
ACTION_REGISTRY["validate_chat_list"] = {
    "func": action_verify_chat_membership,
    "weight": 10,
    "name": "validate_chat_list",
}


@simulation_action("verify_history_not_empty", weight=10)
async def action_verify_history_not_empty(ctx: SimulationContext) -> None:
    """
    Assert that the actor's current chat has at least one message.

    Polled because the history endpoint may return an empty list briefly
    after the first message is written to a distributed store.

    Now uses pick_active_chat_for to ensure we only target chats that
    SHOULD have messages according to our sim state.
    """
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_active_chat_for(actor)
    if not chat_id:
        return None

    async def _check_not_empty():
        messages = await actor.get_history(chat_id)
        assert messages, (
            f"[verify_history] Expected ≥1 message in chat {chat_id} "
            f"for actor '{actor.username}', got 0"
        )

    await poll_until(_check_not_empty, label="verify_history_not_empty")


# ===========================================================================
# SAD PATH / AUTHORIZATION — correctness violations become AssertionError
# NOT retried — a security check must pass on the first request.
# ===========================================================================

@simulation_action("fail_unauthorized_read", weight=15)
async def action_fail_unauthorized_read(ctx: SimulationContext) -> None:
    """
    Assert that the actor cannot read a chat they are NOT in.

    Security violation  → AssertionError (API returned 200)
    Unexpected status   → AssertionError (e.g. 500 instead of 403/404)
    Expected 403/404    → success (this is the correct API behaviour)
    """
    actor = ctx.pick_actor()
    if not actor:
        return None
    target_chat_id = ctx.pick_chat_excluding(actor)
    if not target_chat_id:
        return None

    try:
        await actor.get_history(target_chat_id)
        raise AssertionError(
            f"SECURITY VIOLATION: '{actor.username}' read chat "
            f"{target_chat_id} without being a member"
        )
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            raise AssertionError(
                f"Expected 403/404 for unauthorized read by '{actor.username}', "
                f"got {exc.response.status_code}"
            ) from exc


@simulation_action("fail_unauthorized_send", weight=15)
async def action_fail_unauthorized_send(ctx: SimulationContext) -> None:
    """Assert that a non-member cannot send messages to a chat."""
    actor = ctx.pick_actor()
    if not actor:
        return None
    target_chat_id = ctx.pick_chat_excluding(actor)
    if not target_chat_id:
        return None

    try:
        await actor.send_message(target_chat_id, "intrusion attempt")
        raise AssertionError(
            f"SECURITY VIOLATION: '{actor.username}' sent a message to chat "
            f"{target_chat_id} without being a member"
        )
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            raise AssertionError(
                f"Expected 403/404 for unauthorized send by '{actor.username}', "
                f"got {exc.response.status_code}"
            ) from exc


@simulation_action("fail_message_nonexistent_chat", weight=10)
async def action_fail_message_nonexistent_chat(ctx: SimulationContext) -> None:
    """Assert that sending to a completely made-up UUID is rejected."""
    actor = ctx.pick_actor()
    if not actor:
        return None

    fake_id = uuid.uuid4()
    try:
        await actor.send_message(fake_id, "hello void")
        raise AssertionError(
            f"API accepted a message to non-existent chat {fake_id}"
        )
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            raise AssertionError(
                f"Expected 403/404 for ghost-chat send, "
                f"got {exc.response.status_code}"
            ) from exc


@simulation_action("verify_chat_gone", weight=8)
async def action_verify_chat_gone(ctx: SimulationContext) -> None:
    """
    Pick a chat that the current actor is in, delete it, then poll until both
    the history endpoint and the chat list reflect the deletion.

    The delete itself is a single call (idempotent).  The read-back checks are
    polled because delete propagation across replicas may not be instantaneous.

    Combined poll to reduce sequential latency overhead.
    """
    actor = ctx.pick_actor()
    if not actor:
        return None
    chat_id = ctx.pick_chat_for(actor)
    if not chat_id:
        return None

    # --- Issue the delete ---------------------------------------------------
    try:
        await actor.delete_chat(chat_id)
        ctx.state.deregister_chat(chat_id)
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            raise AssertionError(
                f"Unexpected error deleting chat {chat_id}: {exc.response.status_code}"
            ) from exc
        return  # already gone — that's acceptable

    # --- Poll until the deletion is visible on both read paths --------------

    async def _check_gone():
        # Check history gone
        try:
            await actor.get_history(chat_id)
            raise AssertionError(f"Chat {chat_id} still readable via history")
        except HTTPStatusError as exc:
            if exc.response.status_code not in (403, 404):
                raise AssertionError(f"Unexpected status for deleted chat: {exc.response.status_code}")
        
        # Check list gone
        chats = await actor.get_my_chats()
        assert chat_id not in chats, f"Chat {chat_id} still in chat list"

    await poll_until(_check_gone, label="verify_chat_gone (history+list)")
