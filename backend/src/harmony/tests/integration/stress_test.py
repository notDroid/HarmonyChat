"""
Stress test — concurrent probabilistic simulation.

Uses StochasticContext (random actor/chat selection) instead of
DeterministicContext.  The same ACTION_REGISTRY functions run in both test
suites; only the selection strategy changes.
"""
import asyncio
import random
import time
from typing import Optional

import pytest
from aiolimiter import AsyncLimiter

from harmony.tests.utils import (
    AppClient,
    SimConfig,
    SafeMetrics,
    StochasticContext,
    ACTION_REGISTRY,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

class StressConfig:
    SIM_CONFIG = SimConfig(MAX_USERS=10)   # per worker — scale up for real runs
    DURATION_SECONDS: int = 30
    CONCURRENT_WORKERS: int = 1
    VERBOSE_ERRORS: bool = True
    MONITOR_INTERVAL: int = 2

    ACTION_TIMEOUT_SECONDS: float = 10.0
    MAX_ERROR_RATE: float = 0.05    # 5 % error rate fails the test
    MAX_AVG_LATENCY: float = 2.0    # seconds
    MAX_P95_LATENCY: float = 5.0    # seconds

    # ---------------------------------------------------------------------------
    # Rate limiting (optional)
    #
    # Examples:
    #   RATE_LIMIT_PER_SECOND = 50       → max 50 actions/s across all workers

    #   RATE_LIMIT_PER_SECOND = 10,
    #   RATE_LIMIT_BURST      = 25       → steady 10/s but bursts up to 25

    #   RATE_LIMIT_PER_SECOND = None     → unlimited (original behaviour)
    # ---------------------------------------------------------------------------
    RATE_LIMIT_PER_SECOND: Optional[float] = 100
    RATE_LIMIT_BURST: Optional[float] = None


def _build_limiter() -> Optional[AsyncLimiter]:
    """Return a shared AsyncLimiter if rate limiting is configured, else None."""
    rate = StressConfig.RATE_LIMIT_PER_SECOND
    if rate is None:
        return None
    burst = StressConfig.RATE_LIMIT_BURST if StressConfig.RATE_LIMIT_BURST is not None else rate
    return AsyncLimiter(max_rate=burst, time_period=burst / rate)


# =============================================================================
# MONITOR
# =============================================================================

async def periodic_monitor(metrics: SafeMetrics, stop_event: asyncio.Event) -> None:
    start = time.monotonic()
    while not stop_event.is_set():
        await asyncio.sleep(StressConfig.MONITOR_INTERVAL)
        elapsed = time.monotonic() - start
        summary = await metrics.get_summary_str()
        print(f"[{elapsed:.1f}s] {summary}")


# =============================================================================
# WORKER
# =============================================================================

async def stress_worker(
    worker_id: int,
    stop_event: asyncio.Event,
    client: AppClient,
    metrics: SafeMetrics,
    limiter: Optional[AsyncLimiter] = None,
) -> None:
    """
    Single stress worker.  Each worker owns a StochasticContext (= its own
    SimState) so there is no cross-worker locking on state mutations.
    Only SafeMetrics (and the optional shared AsyncLimiter) is shared.

    Bootstrap: run create_user + create_chat through the registry so the
    worker always starts with at least one user and one chat.

    Rate limiting:
    If a shared AsyncLimiter is provided, each worker acquires one token
    before dispatching an action.  Because all workers share the same limiter
    instance the cap is enforced globally, not per-worker.
    """
    ctx = StochasticContext(client, StressConfig.SIM_CONFIG)

    # --- Bootstrap via the registry (same code path as the action loop) ---
    for bootstrap_action in ("create_user", "create_chat"):
        try:
            await asyncio.wait_for(
                ACTION_REGISTRY[bootstrap_action]["func"](ctx),
                timeout=StressConfig.ACTION_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            print(f"[Worker-{worker_id}] Bootstrap '{bootstrap_action}' failed: {exc}")
            return   # can't run without at least one user + chat

    if not ctx.state._actors:
        print(f"[Worker-{worker_id}] No actors after bootstrap — exiting")
        return

    # --- Pre-compute weighted action list ---------------------------------
    action_names = list(ACTION_REGISTRY.keys())
    action_weights = [ACTION_REGISTRY[k]["weight"] for k in action_names]

    # --- Action loop -------------------------------------------------------
    while not stop_event.is_set():
        chosen_name = random.choices(action_names, weights=action_weights, k=1)[0]
        action_func = ACTION_REGISTRY[chosen_name]["func"]

        # Throttle: acquire one token from the shared limiter before firing.
        # This is the only place that changes when rate limiting is enabled;
        # the rest of the dispatch / metrics / error-handling logic is unchanged.
        if limiter is not None:
            await limiter.acquire()

        start = time.monotonic()
        error_type: str | None = None

        try:
            await asyncio.wait_for(
                action_func(ctx),
                timeout=StressConfig.ACTION_TIMEOUT_SECONDS,
            )
            latency = time.monotonic() - start
            await metrics.record(chosen_name, latency, error=False)

        except asyncio.TimeoutError:
            latency = time.monotonic() - start
            error_type = "timeout"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if StressConfig.VERBOSE_ERRORS:
                print(
                    f"[Worker-{worker_id}] [{chosen_name}] TIMEOUT "
                    f"after {StressConfig.ACTION_TIMEOUT_SECONDS}s"
                )

        except AssertionError as exc:
            # AssertionErrors from inside actions signal correctness bugs —
            # log them distinctly so they stand out in the output
            latency = time.monotonic() - start
            error_type = "assertion"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if StressConfig.VERBOSE_ERRORS:
                print(f"[Worker-{worker_id}] [{chosen_name}] ASSERTION: {exc}")

        except Exception as exc:
            latency = time.monotonic() - start
            error_type = "http_or_other"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if StressConfig.VERBOSE_ERRORS:
                print(f"[Worker-{worker_id}] [{chosen_name}] ERROR: {exc}")

        await asyncio.sleep(0)   # yield to event loop


# =============================================================================
# TEST ENTRY POINT
# =============================================================================

@pytest.mark.stress
@pytest.mark.asyncio
async def test_stress_simulation(app_client: AppClient):
    """
    Spin up CONCURRENT_WORKERS stochastic workers for DURATION_SECONDS then
    assert that error rate and latency stay within configured limits.
    Threshold violations become hard pytest failures.
    """
    limiter = _build_limiter()
    rate_desc = (
        f"{StressConfig.RATE_LIMIT_PER_SECOND} actions/s"
        if limiter is not None
        else "unlimited"
    )

    print(
        f"\n--- Stress test: {StressConfig.CONCURRENT_WORKERS} workers "
        f"x {StressConfig.DURATION_SECONDS}s | rate limit: {rate_desc} ---"
    )

    stop_event = asyncio.Event()
    metrics = SafeMetrics()

    workers = [
        asyncio.create_task(
            stress_worker(i, stop_event, app_client, metrics, limiter=limiter)
        )
        for i in range(StressConfig.CONCURRENT_WORKERS)
    ]
    monitor = asyncio.create_task(periodic_monitor(metrics, stop_event))

    print(f"Running for {StressConfig.DURATION_SECONDS}s …")
    await asyncio.sleep(StressConfig.DURATION_SECONDS)

    print("Stopping …")
    stop_event.set()

    await asyncio.gather(*workers, return_exceptions=True)
    monitor.cancel()
    try:
        await monitor
    except asyncio.CancelledError:
        pass

    await metrics.final_report()

    # Hard assertions — this is what makes the test pass or fail
    await metrics.assert_thresholds(
        max_error_rate=StressConfig.MAX_ERROR_RATE,
        max_avg_latency=StressConfig.MAX_AVG_LATENCY,
        max_p95_latency=StressConfig.MAX_P95_LATENCY,
    )