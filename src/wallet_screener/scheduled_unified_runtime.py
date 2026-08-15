from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .scheduler import SchedulerReport, ScheduledRuntime, SingletonLock
from .unified_runtime import UnifiedRuntimeJob, UnifiedRuntimeReport


@dataclass(slots=True)
class ScheduledUnifiedReport:
    scheduler: SchedulerReport
    cycles: list[UnifiedRuntimeReport] = field(default_factory=list)

    @property
    def successful_cycles(self) -> int:
        return sum(1 for item in self.cycles if not item.errors)

    @property
    def failed_cycles(self) -> int:
        return sum(1 for item in self.cycles if item.errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler": {
                "cycles": self.scheduler.cycles,
                "succeeded": self.scheduler.succeeded,
                "failed": self.scheduler.failed,
                "skipped_locked": self.scheduler.skipped_locked,
                "stopped": self.scheduler.stopped,
            },
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "cycles": [
                {
                    "started_ts": item.started_ts,
                    "finished_ts": item.finished_ts,
                    "screening_run_id": item.screening_run_id,
                    "discovered": item.discovered,
                    "screened": item.screened,
                    "passed": item.passed,
                    "market_fetched": item.market_fetched,
                    "market_accepted": item.market_accepted,
                    "market_duplicates": item.market_duplicates,
                    "market_rejected": item.market_rejected,
                    "market_errors": item.market_errors,
                    "lifecycle_evaluated": item.lifecycle_evaluated,
                    "errors": list(item.errors),
                }
                for item in self.cycles
            ],
        }


class ScheduledUnifiedRuntime:
    """Runs the unified read-only runtime under the scheduler contract."""

    def __init__(
        self,
        job: UnifiedRuntimeJob,
        *,
        lock: SingletonLock | None = None,
    ) -> None:
        self.job = job
        self.lock = lock or SingletonLock()
        self._cycle_reports: list[UnifiedRuntimeReport] = []
        self._runtime: ScheduledRuntime | None = None

    def stop(self) -> None:
        if self._runtime is not None:
            self._runtime.stop()

    def run(self, *, interval_seconds: float, cycles: int | None = None) -> ScheduledUnifiedReport:
        self._cycle_reports = []
        self._runtime = ScheduledRuntime(
            self._execute_once,
            lock=self.lock,
        )
        try:
            scheduler_report = self._runtime.run(
                interval_seconds=interval_seconds,
                cycles=cycles,
            )
        finally:
            self._runtime = None
        return ScheduledUnifiedReport(
            scheduler=scheduler_report,
            cycles=list(self._cycle_reports),
        )

    def _execute_once(self) -> None:
        report = self.job.run_once()
        self._cycle_reports.append(report)
        # Let the scheduler's failure accounting observe a cycle-level runtime
        # error while preserving the full report for diagnosis.
        if report.errors:
            raise RuntimeError("unified_runtime_cycle_failed")
