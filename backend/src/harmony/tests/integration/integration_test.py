"""
Deterministic integration tests.

Each test creates a DeterministicContext and runs a fixed sequence of actions
from ACTION_REGISTRY.  Because DeterministicContext.pick_actor() always returns
the actor at the cursor index (not a random one), the same sequence of calls
produces the same result every run.

Design rules
------------
* Every action invocation goes through ACTION_REGISTRY — the same code path
  the stress test uses.  No test-only helper functions that diverge.
* ctx.actor(i) lets a test body read a specific actor without going through
  the registry (useful for inline assertions).
* ctx.focus(i) / ctx.advance() control which actor pick_actor() returns
  for the next registry call.
* Assertions that are purely about correctness (security boundaries, message
  persistence) use the shared assert_* helpers from assertions.py.
  Assertions that are about simulation-state consistency are baked into the
  action itself (e.g. verify_chat_membership, send_and_verify_message).

Run with:  task test:integration
Marker:    @pytest.mark.integration
"""
import uuid

import pytest
from httpx import HTTPStatusError

from harmony.tests.utils import (
    AppClient,
    SimConfig,
    DeterministicContext,
    ACTION_REGISTRY,
)
from harmony.tests.utils.assertions import (
    assert_chat_in_list,
    assert_chat_not_in_list,
    assert_chat_inaccessible,
    assert_history_not_empty,
    assert_message_in_history,
    assert_send_denied,
)


# Convenience: call an action by name from the registry
async def run(name: str, ctx: DeterministicContext):
    return await ACTION_REGISTRY[name]["func"](ctx)


# ============================================================================
# USER LIFECYCLE
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_user_returns_valid_id(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    actor = await run("create_user", ctx)

    assert actor is not None
    assert isinstance(actor.user_id, uuid.UUID)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_returns_access_token(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    actor = ctx.actor(0)

    assert actor.tokens.get("access_token"), (
        "Expected 'access_token' after login"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_two_users_have_distinct_ids(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    assert ctx.actor(0).user_id != ctx.actor(1).user_id


# ============================================================================
# CHAT LIFECYCLE
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_chat_returns_valid_id(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    ctx.focus(0)
    chat_id = await run("create_chat", ctx)

    assert isinstance(chat_id, uuid.UUID)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_members_see_chat_in_list(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    for _ in range(3):
        await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)   # picks [0, 1, 2]

    for i in range(3):
        ctx.focus(i)
        await run("verify_chat_membership", ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_outsider_does_not_see_chat_in_list(app_client: AppClient):
    """
    Create the chat when only 2 actors exist so DeterministicContext.pick_actors
    caps at 2 ([0, 1]).  Then create the third user — the outsider.
    """
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)   # 0
    await run("create_user", ctx)   # 1

    ctx.focus(0)
    chat_id = await run("create_chat", ctx)  # [0, 1] only

    await run("create_user", ctx)   # 2 = outsider

    await assert_chat_in_list(ctx.actor(0), chat_id)
    await assert_chat_in_list(ctx.actor(1), chat_id)
    await assert_chat_not_in_list(ctx.actor(2), chat_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_chat_removes_from_all_members(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    for _ in range(3):
        await run("create_user", ctx)

    ctx.focus(0)
    chat_id = await run("create_chat", ctx)

    # verify_chat_gone: deletes + asserts inaccessible + absent from list
    ctx.focus(0)
    await run("verify_chat_gone", ctx)

    for i in range(1, 3):
        await assert_chat_not_in_list(ctx.actor(i), chat_id)


# ============================================================================
# MESSAGING
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sent_message_appears_in_history(app_client: AppClient):
    """send_and_verify_message raises AssertionError if the read-back fails."""
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)
    await run("send_and_verify_message", ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_every_member_can_send_messages(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    for _ in range(4):
        await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)

    for i in range(4):
        ctx.focus(i)
        await run("send_and_verify_message", ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_messages_accumulate_in_history(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)

    for _ in range(5):
        ctx.focus(0)
        await run("send_message", ctx)

    ctx.focus(0)
    await run("verify_history_not_empty", ctx)


# ============================================================================
# AUTHORIZATION / SECURITY BOUNDARIES
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_non_member_cannot_read_history(app_client: AppClient):
    """
    Create chat with [0,1], then add outsider [2].
    fail_unauthorized_read at cursor=2 calls pick_chat_excluding(actor[2]),
    which returns the only chat in the system — the one [2] is not in.
    """
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)   # 0
    await run("create_user", ctx)   # 1

    ctx.focus(0)
    await run("create_chat", ctx)   # chat with [0,1]

    await run("create_user", ctx)   # 2 = outsider

    ctx.focus(2)
    await run("fail_unauthorized_read", ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_non_member_cannot_send_to_chat(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)

    await run("create_user", ctx)   # outsider

    ctx.focus(2)
    await run("fail_unauthorized_send", ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nonexistent_chat_read_is_rejected(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)

    fake_id = uuid.uuid4()
    await assert_chat_inaccessible(ctx.actor(0), fake_id, context="nonexistent UUID")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nonexistent_chat_send_is_rejected(app_client: AppClient):
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)

    fake_id = uuid.uuid4()
    await assert_send_denied(ctx.actor(0), fake_id, context="nonexistent UUID")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_and_both_security_boundaries_in_one_flow(app_client: AppClient):
    """
    Full lifecycle in one test:
      [0+1] share a chat  ->  [0] sends (verified)  ->  [2] tries to read/send
      (both denied)  ->  [0] deletes chat (vanishes for everyone)
    """
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=5))
    await run("create_user", ctx)
    await run("create_user", ctx)

    ctx.focus(0)
    chat_id = await run("create_chat", ctx)

    ctx.focus(0)
    await run("send_and_verify_message", ctx)

    await run("create_user", ctx)   # outsider

    ctx.focus(2)
    await run("fail_unauthorized_read", ctx)
    await run("fail_unauthorized_send", ctx)

    ctx.focus(0)
    await run("verify_chat_gone", ctx)

    for i in range(1, 3):
        await assert_chat_not_in_list(ctx.actor(i), chat_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_simulation_round_trip(app_client: AppClient):
    """
    Smoke test: runs the full ACTION_REGISTRY happy path deterministically.
    Same sequence a stress worker executes but with stable actor selection.

    create 4 users -> create_chat -> 4x send_and_verify -> verify_membership
    for each -> read_history -> verify_history_not_empty -> delete_chat
    """
    ctx = DeterministicContext(app_client, SimConfig(MAX_USERS=10))
    for _ in range(4):
        await run("create_user", ctx)

    ctx.focus(0)
    await run("create_chat", ctx)

    for i in range(4):
        ctx.focus(i)
        await run("send_and_verify_message", ctx)

    for i in range(4):
        ctx.focus(i)
        await run("verify_chat_membership", ctx)

    ctx.focus(0)
    await run("read_history", ctx)
    await run("verify_history_not_empty", ctx)

    ctx.focus(0)
    await run("verify_chat_gone", ctx)