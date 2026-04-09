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
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
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

class StressSettings(BaseSettings):
    """
    Stress test configuration.
    
    Can be overridden via environment variables prefixed with STRESS_:
    - STRESS_DURATION_SECONDS=60
    - STRESS_CONCURRENT_WORKERS=10
    - STRESS_RATE_LIMIT_PER_SECOND=200
    """
    model_config = SettingsConfigDict(
        env_prefix="STRESS_",
        case_sensitive=False,
        env_file=".env",
        extra="ignore"
    )

    # Simulation setup
    duration_seconds: int = Field(default=30)
    concurrent_workers: int = Field(default=5)
    max_users_per_worker: int = Field(default=10)
    monitor_interval: int = Field(default=2)
    verbose_errors: bool = Field(default=True)

    # Thresholds
    action_timeout_seconds: float = Field(default=5.0)
    max_error_rate: float = Field(default=0.05)
    max_avg_latency: float = Field(default=2.0)
    max_p95_latency: float = Field(default=5.0)

    # Rate limiting
    rate_limit_per_second: Optional[float] = Field(default=100.0)
    rate_limit_burst: Optional[float] = Field(default=None)

    @property
    def sim_config(self) -> SimConfig:
        return SimConfig(MAX_USERS=self.max_users_per_worker)

    def build_limiter(self) -> Optional[AsyncLimiter]:
        """Return a shared AsyncLimiter if rate limiting is configured, else None."""
        if self.rate_limit_per_second is None:
            return None
        burst = self.rate_limit_burst if self.rate_limit_burst is not None else self.rate_limit_per_second
        return AsyncLimiter(max_rate=burst, time_period=burst / self.rate_limit_per_second)


# Global settings instance
settings = StressSettings()


# =============================================================================
# MONITOR
# =============================================================================

async def periodic_monitor(metrics: SafeMetrics, stop_event: asyncio.Event) -> None:
    start = time.monotonic()
    while not stop_event.is_set():
        await asyncio.sleep(settings.monitor_interval)
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
    """
    ctx = StochasticContext(client, settings.sim_config)

    # --- Bootstrap via the registry (same code path as the action loop) ---
    for bootstrap_action in ("create_user", "create_chat"):
        try:
            await asyncio.wait_for(
                ACTION_REGISTRY[bootstrap_action]["func"](ctx),
                timeout=settings.action_timeout_seconds,
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

        if limiter is not None:
            await limiter.acquire()

        start = time.monotonic()
        error_type: str | None = None

        try:
            await asyncio.wait_for(
                action_func(ctx),
                timeout=settings.action_timeout_seconds,
            )
            latency = time.monotonic() - start
            await metrics.record(chosen_name, latency, error=False)

        except asyncio.TimeoutError:
            latency = time.monotonic() - start
            error_type = "timeout"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if settings.verbose_errors:
                print(
                    f"[Worker-{worker_id}] [{chosen_name}] TIMEOUT "
                    f"after {settings.action_timeout_seconds}s"
                )

        except AssertionError as exc:
            latency = time.monotonic() - start
            error_type = "assertion"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if settings.verbose_errors:
                print(f"[Worker-{worker_id}] [{chosen_name}] ASSERTION: {exc}")

        except Exception as exc:
            latency = time.monotonic() - start
            error_type = "http_or_other"
            await metrics.record(chosen_name, latency, error=True, error_type=error_type)
            if settings.verbose_errors:
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
    limiter = settings.build_limiter()
    rate_desc = (
        f"{settings.rate_limit_per_second} actions/s"
        if limiter is not None
        else "unlimited"
    )

    print(
        f"\n--- Stress test: {settings.concurrent_workers} workers "
        f"x {settings.duration_seconds}s | rate limit: {rate_desc} ---"
    )

    stop_event = asyncio.Event()
    metrics = SafeMetrics()
    app_client.metrics = metrics

    workers = [
        asyncio.create_task(
            stress_worker(i, stop_event, app_client, metrics, limiter=limiter)
        )
        for i in range(settings.concurrent_workers)
    ]
    monitor = asyncio.create_task(periodic_monitor(metrics, stop_event))

    print(f"Running for {settings.duration_seconds}s …")
    await asyncio.sleep(settings.duration_seconds)

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
        max_error_rate=settings.max_error_rate,
        max_avg_latency=settings.max_avg_latency,
        max_p95_latency=settings.max_p95_latency,
    )
