"""
Metrics collection for stress tests.
"""
import asyncio
import statistics
import time
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

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

    @property
    def stddev_latency(self) -> float:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0.0

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
        self._actions: Dict[str, ActionMetrics] = {}
        self._calls: Dict[str, ActionMetrics] = {}
        self.start_time: float = time.monotonic()

    # ---- Recording --------------------------------------------------------

    def record(
        self,
        name: str,
        latency: float,
        *,
        error: bool = False,
        error_type: Optional[str] = None,
        category: str = "action",
    ) -> None:
        if category == "action":
            self.requests += 1
            if error:
                self.errors += 1
            else:
                self.latencies.append(latency)
            bucket = self._actions.setdefault(name, ActionMetrics())
        else:
            bucket = self._calls.setdefault(name, ActionMetrics())

        bucket.calls += 1
        if error:
            bucket.errors += 1
        else:
            bucket.latencies.append(latency)

    # ---- Aggregates -------------------------------------------------------

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.start_time

    @property
    def rps(self) -> float:
        return self.requests / self.elapsed if self.elapsed > 0 else 0.0

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
    def p50_latency(self) -> float:
        return self._global_percentile(50)

    @property
    def p95_latency(self) -> float:
        return self._global_percentile(95)

    @property
    def p99_latency(self) -> float:
        return self._global_percentile(99)

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0

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
            f"Requests: {self.requests} ({self.rps:.1f} RPS) | "
            f"Errors: {self.errors} ({self.error_rate:.1%}) | "
            f"Latency p50/p95/p99: "
            f"{self.p50_latency * 1000:.2f}ms / "
            f"{self.p95_latency * 1000:.2f}ms / "
            f"{self.p99_latency * 1000:.2f}ms"
        )

    def _render_table(self, title: str, data: Dict[str, ActionMetrics]) -> Table:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta", title=f"[bold]{title}[/bold]")
        table.add_column("Name", style="cyan", min_width=30)
        table.add_column("Calls", justify="right")
        table.add_column("Errors", justify="right")
        table.add_column("Rate", justify="right")
        table.add_column("Avg", justify="right")
        table.add_column("p50", justify="right")
        table.add_column("p95", justify="right")
        table.add_column("p99", justify="right")
        table.add_column("Max", justify="right")

        for name, am in sorted(data.items()):
            error_style = "red" if am.error_rate > 0.05 else "green"
            table.add_row(
                name,
                str(am.calls),
                f"[{error_style}]{am.errors}[/{error_style}]",
                f"[{error_style}]{am.error_rate:.0%}[/{error_style}]",
                f"{am.avg_latency * 1000:.1f}ms",
                f"{am.percentile(50) * 1000:.1f}ms",
                f"{am.percentile(95) * 1000:.1f}ms",
                f"{am.percentile(99) * 1000:.1f}ms",
                f"{am.max_latency * 1000:.1f}ms",
            )
        return table

    def print_final_report(self) -> None:
        console = Console()
        console.print("\n[bold cyan]=== FINAL STRESS TEST REPORT ===[/bold cyan]")
        console.print(self.summary_str())
        
        if self._actions:
            console.print(self._render_table("HIGH-LEVEL ACTIONS (Simulation Path)", self._actions))
        
        if self._calls:
            console.print(self._render_table("RAW API CALLS (Network Latency)", self._calls))


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
        name: str,
        latency: float,
        *,
        error: bool = False,
        error_type: Optional[str] = None,
        category: str = "action",
    ) -> None:
        async with self._lock:
            self._metrics.record(name, latency, error=error, error_type=error_type, category=category)

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