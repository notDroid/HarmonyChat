"""
Semantic assertion helpers.

Every function here raises AssertionError (or re-raises with a clearer message)
so that pytest surfaces failures with human-readable context rather than raw
HTTP status codes.

Eventual-consistency note
-------------------------
Because the backend is distributed, a write (POST/DELETE) may not be
immediately reflected in a subsequent read (GET) — a replica or cache layer
may return stale data for a short window.  All "read-after-write" assertions
(chat visibility, message history, deletion propagation) are decorated with
``@eventually`` so they poll with exponential back-off instead of failing on
the first attempt.

"Read-once" assertions — those that check a security invariant like a 403/404
response — are intentionally NOT retried: a security violation should be
surfaced immediately, not hidden behind a retry loop.
"""
import uuid
from typing import Optional

from httpx import HTTPStatusError

from .client import SimulationActor
from .retry import eventually


# ---------------------------------------------------------------------------
# Chat access assertions
# ---------------------------------------------------------------------------

async def assert_chat_accessible(
    actor: SimulationActor,
    chat_id: uuid.UUID,
    *,
    context: str = "",
) -> None:
    """Assert that *actor* can read the history of *chat_id*.

    Not retried — if a member genuinely cannot access their own chat that
    is an immediate correctness failure, not a propagation delay.
    """
    try:
        await actor.get_history(chat_id)
    except HTTPStatusError as exc:
        suffix = f" ({context})" if context else ""
        raise AssertionError(
            f"User '{actor.username}' could not access chat {chat_id}"
            f" — HTTP {exc.response.status_code}{suffix}"
        ) from exc


async def assert_chat_inaccessible(
    actor: SimulationActor,
    chat_id: uuid.UUID,
    *,
    context: str = "",
) -> None:
    """
    Assert that *actor* is denied access to *chat_id* with a 403 or 404.

    Raises AssertionError if the request succeeds (security violation) or if it
    fails with an unexpected status code.

    Not retried — a security boundary check must pass immediately; retrying
    could mask a real security violation that transiently returns 403 then 200.
    """
    try:
        await actor.get_history(chat_id)
        suffix = f" ({context})" if context else ""
        raise AssertionError(
            f"SECURITY VIOLATION: User '{actor.username}' read chat {chat_id}"
            f" without permission{suffix}"
        )
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            suffix = f" ({context})" if context else ""
            raise AssertionError(
                f"Expected 403/404 for unauthorized read of chat {chat_id}"
                f" by '{actor.username}', got {exc.response.status_code}{suffix}"
            ) from exc


# ---------------------------------------------------------------------------
# Chat-list assertions  (retried — list may lag behind create/delete)
# ---------------------------------------------------------------------------

@eventually()
async def assert_chat_in_list(
    actor: SimulationActor,
    chat_id: uuid.UUID,
) -> None:
    """Assert that *chat_id* appears in *actor*'s own chat list.

    Retried with exponential back-off: a freshly created chat may not be
    visible in the member's list immediately across all backend replicas.
    """
    chats = await actor.get_my_chats()
    assert chat_id in chats, (
        f"Chat {chat_id} not yet visible in '{actor.username}''s chat list. "
        f"Found: {chats}"
    )


@eventually()
async def assert_chat_not_in_list(
    actor: SimulationActor,
    chat_id: uuid.UUID,
) -> None:
    """Assert that *chat_id* does NOT appear in *actor*'s chat list.

    Retried: a deleted chat may linger in the list briefly while the deletion
    propagates across read replicas.
    """
    chats = await actor.get_my_chats()
    assert chat_id not in chats, (
        f"Chat {chat_id} is still present in '{actor.username}''s chat list "
        f"after expected removal — deletion may not have propagated yet."
    )


# ---------------------------------------------------------------------------
# Message assertions  (retried — message writes propagate asynchronously)
# ---------------------------------------------------------------------------

@eventually()
async def assert_message_in_history(
    actor: SimulationActor,
    chat_id: uuid.UUID,
    content: str,
) -> None:
    """Assert that a message containing *content* exists in *chat_id*'s history.

    Retried: the message write may be queued (e.g. via Kafka/Redpanda) and not
    immediately visible on the read path.
    """
    messages = await actor.get_history(chat_id)
    contents = [m.content for m in messages]
    assert any(content in c for c in contents), (
        f"Message '{content}' not yet in history of chat {chat_id}. "
        f"Visible messages: {contents}"
    )


@eventually()
async def assert_history_not_empty(
    actor: SimulationActor,
    chat_id: uuid.UUID,
) -> None:
    """Assert that *chat_id* has at least one message.

    Retried: the first message in a chat may be written asynchronously.
    """
    messages = await actor.get_history(chat_id)
    assert messages, (
        f"Expected at least one message in chat {chat_id} "
        f"for user '{actor.username}', but history is still empty"
    )


# ---------------------------------------------------------------------------
# Sending / writing assertions
# ---------------------------------------------------------------------------

async def assert_send_denied(
    actor: SimulationActor,
    chat_id: uuid.UUID,
    content: str = "intrusion attempt",
    *,
    context: str = "",
) -> None:
    """
    Assert that *actor* cannot send a message to *chat_id*.

    Not retried — like assert_chat_inaccessible, this is a security boundary
    check.  A 403/404 is the expected immediate response; retrying could hide
    a security regression.
    """
    try:
        await actor.send_message(chat_id, content)
        suffix = f" ({context})" if context else ""
        raise AssertionError(
            f"SECURITY VIOLATION: User '{actor.username}' sent a message to "
            f"chat {chat_id} without being a member{suffix}"
        )
    except HTTPStatusError as exc:
        if exc.response.status_code not in (403, 404):
            suffix = f" ({context})" if context else ""
            raise AssertionError(
                f"Expected 403/404 when non-member '{actor.username}' sent to "
                f"chat {chat_id}, got {exc.response.status_code}{suffix}"
            ) from exc