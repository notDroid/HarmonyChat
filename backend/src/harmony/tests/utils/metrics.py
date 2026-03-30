"""
Metrics collection for stress tests.
"""
import asyncio
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich import box


# ---------------------------------------------------------------------------
# Internal per-action bucket
# ---------------------------------------------------------------------------

@dataclass
class ActionMetrics:
    calls: int = 0
    errors: int = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def successes(self) -> int:
        return self.calls - self.errors

    @property
    def error_rate(self) -> float:
        return self.errors / self.calls if self.calls else 0.0

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    def percentile(self, pct: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lats = sorted(self.latencies)
        idx = min(int(len(sorted_lats) * pct / 100), len(sorted_lats) - 1)
        return sorted_lats[idx]


# ---------------------------------------------------------------------------
# Core (non-thread-safe) Metrics
# ---------------------------------------------------------------------------

class Metrics:
    def __init__(self):
        self.requests: int = 0
        self.errors: int = 0
        self.latencies: List[float] = []
        self._per_action: Dict[str, ActionMetrics] = {}

    # ---- Recording --------------------------------------------------------

    def record(
        self,
        action: str,
        latency: float,
        *,
        error: bool = False,
        error_type: Optional[str] = None,
    ) -> None:
        self.requests += 1
        if error:
            self.errors += 1
        else:
            self.latencies.append(latency)

        bucket = self._per_action.setdefault(action, ActionMetrics())
        bucket.calls += 1
        if error:
            bucket.errors += 1
        else:
            bucket.latencies.append(latency)

    # ---- Aggregates -------------------------------------------------------

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests if self.requests else 0.0

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    def _global_percentile(self, pct: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lats = sorted(self.latencies)
        idx = min(int(len(sorted_lats) * pct / 100), len(sorted_lats) - 1)
        return sorted_lats[idx]

    @property
    def p95_latency(self) -> float:
        return self._global_percentile(95)

    @property
    def p99_latency(self) -> float:
        return self._global_percentile(99)

    # ---- Validation -------------------------------------------------------

    def assert_thresholds(
        self,
        *,
        max_error_rate: float = 0.05,
        max_avg_latency: float = 2.0,
        max_p95_latency: float = 5.0,
    ) -> None:
        """
        Raise AssertionError if any threshold is breached.

        Call this at the end of a stress test so metric violations become hard
        pytest failures rather than silent log noise.

        Args:
            max_error_rate:   Fraction of requests that may fail  (default 5 %).
            max_avg_latency:  Maximum acceptable mean latency in seconds.
            max_p95_latency:  Maximum acceptable p95 latency in seconds.
        """
        violations: List[str] = []

        if self.error_rate > max_error_rate:
            violations.append(
                f"Error rate {self.error_rate:.1%} exceeds threshold {max_error_rate:.1%}"
            )
        if self.avg_latency > max_avg_latency:
            violations.append(
                f"Avg latency {self.avg_latency * 1000:.2f}ms exceeds threshold {max_avg_latency * 1000:.2f}ms"
            )
        if self.p95_latency > max_p95_latency:
            violations.append(
                f"p95 latency {self.p95_latency * 1000:.2f}ms exceeds threshold {max_p95_latency * 1000:.2f}ms"
            )

        if violations:
            bullet_list = "\n  ".join(violations)
            raise AssertionError(
                f"Stress test threshold violations:\n  {bullet_list}"
            )

    # ---- Reporting --------------------------------------------------------

    def summary_str(self) -> str:
        return (
            f"Requests: {self.requests} | "
            f"Errors: {self.errors} ({self.error_rate:.1%}) | "
            f"Latency avg/p95/p99: "
            f"{self.avg_latency * 1000:.2f}ms / "
            f"{self.p95_latency * 1000:.2f}ms / "
            f"{self.p99_latency * 1000:.2f}ms"
        )

    def print_final_report(self) -> None:
        console = Console()
        console.print("\n[bold cyan]=== FINAL METRICS ===[/bold cyan]")
        console.print(self.summary_str())

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Action", style="cyan", min_width=40)
        table.add_column("Calls", justify="right")
        table.add_column("Errors", justify="right")
        table.add_column("Error Rate", justify="right")
        table.add_column("Avg Latency", justify="right")
        table.add_column("p95 Latency", justify="right")

        for name, am in sorted(self._per_action.items()):
            error_style = "red" if am.error_rate > 0.05 else "green"
            table.add_row(
                name,
                str(am.calls),
                f"[{error_style}]{am.errors}[/{error_style}]",
                f"[{error_style}]{am.error_rate:.0%}[/{error_style}]",
                f"{am.avg_latency * 1000:.2f}ms",
                f"{am.percentile(95) * 1000:.2f}ms",
            )

        console.print(table)

# ---------------------------------------------------------------------------
# Thread-safe wrapper (used by concurrent stress-test workers)
# ---------------------------------------------------------------------------

class SafeMetrics:
    """Wraps Metrics with an asyncio lock for concurrent workers."""

    def __init__(self):
        self._metrics = Metrics()
        self._lock = asyncio.Lock()

    async def record(
        self,
        action: str,
        latency: float,
        *,
        error: bool = False,
        error_type: Optional[str] = None,
    ) -> None:
        async with self._lock:
            self._metrics.record(action, latency, error=error, error_type=error_type)

    async def get_summary_str(self) -> str:
        async with self._lock:
            return self._metrics.summary_str()

    async def final_report(self) -> None:
        async with self._lock:
            self._metrics.print_final_report()

    async def assert_thresholds(
        self,
        *,
        max_error_rate: float = 0.05,
        max_avg_latency: float = 2.0,
        max_p95_latency: float = 5.0,
    ) -> None:
        """Thread-safe wrapper around Metrics.assert_thresholds()."""
        async with self._lock:
            self._metrics.assert_thresholds(
                max_error_rate=max_error_rate,
                max_avg_latency=max_avg_latency,
                max_p95_latency=max_p95_latency,
            )