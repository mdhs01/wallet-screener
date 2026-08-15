from __future__ import annotations

from dataclasses import dataclass
from time import monotonic, sleep
from typing import Callable, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class RetryPolicy:
    retries: int = 3
    backoff_seconds: float = 0.5
    max_backoff_seconds: float = 8.0

    def delays(self):
        for attempt in range(self.retries):
            yield min(self.max_backoff_seconds, self.backoff_seconds * (2**attempt))


def with_retry(operation: Callable[[], T], *, policy: RetryPolicy | None = None) -> T:
    policy = policy or RetryPolicy()
    last_error: Exception | None = None
    for delay in policy.delays():
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - boundary helper intentionally retries caller-defined operations
            last_error = exc
            sleep(delay)
    try:
        return operation()
    except Exception as exc:  # noqa: BLE001
        last_error = exc
    raise last_error or RuntimeError("operation failed")


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    opened_until: float = 0.0


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 5, cooldown_seconds: float = 60.0) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self.state = CircuitState()

    def allow(self) -> bool:
        return monotonic() >= self.state.opened_until

    def record_success(self) -> None:
        self.state.failures = 0
        self.state.opened_until = 0.0

    def record_failure(self) -> None:
        self.state.failures += 1
        if self.state.failures >= self.failure_threshold:
            self.state.opened_until = monotonic() + self.cooldown_seconds
