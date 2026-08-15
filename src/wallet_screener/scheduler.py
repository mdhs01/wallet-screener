from __future__ import annotations

from dataclasses import dataclass
from time import sleep, time
from typing import Callable

from .operational import CircuitBreaker


@dataclass(slots=True)
class SchedulerReport:
    cycles: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_locked: int = 0
    stopped: bool = False


class SingletonLock:
    """Process-local singleton guard for the runtime scheduler."""

    _held = False

    def acquire(self) -> bool:
        if type(self)._held:
            return False
        type(self)._held = True
        return True

    def release(self) -> None:
        type(self)._held = False


class ScheduledRuntime:
    """Bounded scheduler with singleton protection and graceful stop."""

    def __init__(self, job: Callable[[], object], *, lock: SingletonLock | None = None, circuit: CircuitBreaker | None = None) -> None:
        self.job = job
        self.lock = lock or SingletonLock()
        self.circuit = circuit
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self, *, interval_seconds: float, cycles: int | None = None) -> SchedulerReport:
        if interval_seconds < 0:
            raise ValueError("interval_seconds must be >= 0")
        report = SchedulerReport()
        if not self.lock.acquire():
            report.skipped_locked = 1
            return report
        try:
            while not self._stop and (cycles is None or report.cycles < cycles):
                report.cycles += 1
                try:
                    if self.circuit is not None and not self.circuit.allow_request():
                        report.failed += 1
                    else:
                        self.job()
                        report.succeeded += 1
                        if self.circuit is not None:
                            self.circuit.record_success()
                except Exception:
                    report.failed += 1
                    if self.circuit is not None:
                        self.circuit.record_failure()
                if not self._stop and (cycles is None or report.cycles < cycles) and interval_seconds:
                    sleep(interval_seconds)
        finally:
            self.lock.release()
            report.stopped = self._stop
        return report
