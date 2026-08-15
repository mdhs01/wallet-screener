from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Mapping


class JsonFormatter(logging.Formatter):
    """Render log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            payload["context"] = dict(context)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging(level: str = "INFO") -> None:
    """Configure one stderr JSON handler for the application root logger."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)


@dataclass(slots=True)
class RuntimeMetrics:
    counters: dict[str, int] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    timings_ms: dict[str, list[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def inc(self, name: str, value: int = 1) -> None:
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self.gauges[name] = float(value)

    def observe_ms(self, name: str, value: float) -> None:
        with self._lock:
            self.timings_ms.setdefault(name, []).append(float(value))

    def timed(self, name: str):
        metrics = self

        class _Timer:
            def __enter__(self):
                self.started = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc, tb):
                metrics.observe_ms(name, (time.perf_counter() - self.started) * 1000)
                return False

        return _Timer()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "timings_ms": {
                    key: {
                        "count": len(values),
                        "avg": sum(values) / len(values) if values else 0.0,
                        "max": max(values) if values else 0.0,
                    }
                    for key, values in self.timings_ms.items()
                },
            }


class Observability:
    """Convenience facade for structured events and runtime metrics."""

    def __init__(self, metrics: RuntimeMetrics | None = None, logger_name: str = "wallet_screener") -> None:
        self.metrics = metrics or RuntimeMetrics()
        self.logger = logging.getLogger(logger_name)

    def event(self, event: str, *, level: int = logging.INFO, context: Mapping[str, Any] | None = None) -> None:
        self.logger.log(level, event, extra={"context": {"event": event, **dict(context or {})}})

    def error(self, event: str, *, error: Exception | None = None, context: Mapping[str, Any] | None = None) -> None:
        extra = {"context": {"event": event, **dict(context or {})}}
        self.logger.error(event, extra=extra, exc_info=error is not None)
        self.metrics.inc("errors_total")

    def record_cycle(self, *, success: bool, duration_ms: float, discovered: int = 0, passed: int = 0) -> None:
        self.metrics.inc("runtime_cycles_total")
        self.metrics.inc("runtime_cycles_success_total" if success else "runtime_cycles_failed_total")
        self.metrics.observe_ms("runtime_cycle", duration_ms)
        self.metrics.set_gauge("last_discovered", discovered)
        self.metrics.set_gauge("last_passed", passed)

    def record_market(self, *, fetched: int, accepted: int, duplicates: int, rejected: int, errors: int) -> None:
        for name, value in {
            "market_snapshots_fetched_total": fetched,
            "paper_observations_accepted_total": accepted,
            "paper_observations_duplicate_total": duplicates,
            "paper_observations_rejected_total": rejected,
            "market_feed_errors_total": errors,
        }.items():
            self.metrics.inc(name, value)
