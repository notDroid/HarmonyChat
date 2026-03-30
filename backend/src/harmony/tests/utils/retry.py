"""
Retry helpers for assertions against eventually-consistent distributed backends.

The distributed backend may use replicated storage, message queues, or read
replicas — any of these can cause a GET to return stale state immediately after
a POST/DELETE.  Rather than adding fixed sleeps (fragile and slow), these
utilities poll until the expected state is observed or a deadline is reached.

Usage
-----
Direct:
    await poll_until(
        lambda: assert_chat_in_list(actor, chat_id),
        label="chat visible after create",
    )

As a decorator (wraps an existing async assertion function):
    @eventually()
    async def assert_chat_in_list(actor, chat_id):
        ...

The @eventually decorator is most useful on leaf assertion functions in
assertions.py.  poll_until is more appropriate when the retry boundary needs
to wrap a block of code rather than a single call.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Awaitable, Callable, Optional, TypeVar

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Defaults — tweak here to tune for your infrastructure's replication lag
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT: float = 10.0       # seconds before giving up
DEFAULT_MIN_WAIT: float = 0.15      # first back-off interval
DEFAULT_MAX_WAIT: float = 2.0       # back-off ceiling
DEFAULT_MULTIPLIER: float = 1.6     # exponential growth factor


# ---------------------------------------------------------------------------
# Core primitive
# ---------------------------------------------------------------------------

async def poll_until(
    coro_fn: Callable[[], Awaitable[T]],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    multiplier: float = DEFAULT_MULTIPLIER,
    label: str = "",
) -> T:
    """
    Retry ``coro_fn()`` until it completes without raising AssertionError,
    or until *timeout* seconds have elapsed.

    Only ``AssertionError`` is caught and retried — any other exception
    (e.g. ``HTTPStatusError``, ``TimeoutError``) propagates immediately so
    unexpected infrastructure failures are never silently swallowed.

    Args:
        coro_fn:    A zero-argument async callable.  Each retry creates a
                    fresh coroutine, so ``coro_fn`` must be a *function*
                    (lambda or def), not a bare coroutine.
        timeout:    Maximum seconds to keep retrying.
        min_wait:   Initial back-off interval in seconds.
        max_wait:   Maximum back-off interval in seconds (ceiling).
        multiplier: Exponential growth factor between retries.
        label:      Human-readable name shown in the timeout error message.

    Returns:
        Whatever ``coro_fn()`` returns on success.

    Raises:
        AssertionError: Re-raised (with context) if timeout expires.
    """
    label_str = f" [{label}]" if label else ""

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_delay(timeout),
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(AssertionError),
            reraise=True,
        ):
            with attempt:
                return await coro_fn()
    except RetryError as exc:
        # tenacity wraps the last exception in RetryError — unwrap it so callers
        # see a plain AssertionError, not a tenacity implementation detail.
        cause = exc.last_attempt.exception()
        raise AssertionError(
            f"Eventual-consistency assertion{label_str} did not pass within "
            f"{timeout}s. Last failure: {cause}"
        ) from cause

    # Unreachable — satisfies the type checker
    raise AssertionError(f"poll_until{label_str}: unexpected exit")  # pragma: no cover


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def eventually(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    multiplier: float = DEFAULT_MULTIPLIER,
    label: Optional[str] = None,
):
    """
    Decorator that wraps an async function with ``poll_until`` retry logic.

    The label defaults to the wrapped function's qualified name.

    Example::

        @eventually(timeout=15.0)
        async def assert_chat_in_list(actor: SimulationActor, chat_id: uuid.UUID):
            chats = await actor.get_my_chats()
            assert chat_id in chats, f"Chat {chat_id} not yet visible"

    The decorated function has the same signature as the original.
    """
    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        _label = label or fn.__qualname__

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            return await poll_until(
                lambda: fn(*args, **kwargs),
                timeout=timeout,
                min_wait=min_wait,
                max_wait=max_wait,
                multiplier=multiplier,
                label=_label,
            )

        return wrapper

    return decorator