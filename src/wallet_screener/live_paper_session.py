from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Iterable

from .paper_persistence import PaperObservationStore
from .paper_runtime import PersistentPaperRuntime
from .paper_tracking import PaperObservation


@dataclass(slots=True)
class PaperSessionReport:
    started_ts: int
    finished_ts: int
    observations_seen: int = 0
    observations_accepted: int = 0
    duplicates: int = 0
    rejected: int = 0
    errors: int = 0


class LivePaperSession:
    """Persistent read-only paper session for a bounded live validation window."""

    def __init__(self, store: PaperObservationStore, runtime: PersistentPaperRuntime) -> None:
        self.store = store
        self.runtime = runtime

    def ingest(self, observations: Iterable[PaperObservation]) -> PaperSessionReport:
        started = int(time())
        report = PaperSessionReport(started_ts=started, finished_ts=started)
        for observation in observations:
            report.observations_seen += 1
            try:
                result = self.runtime.ingest_observations([observation])
                report.observations_accepted += result.inserted
                report.duplicates += result.duplicates
                # PersistentPaperRuntime currently ignores malformed/wrong-wallet
                # observations rather than exposing a rejected count, so only
                # inserted and duplicate outcomes are reflected here.
            except Exception:
                report.errors += 1
        report.finished_ts = int(time())
        return report

    def readiness(self, *, now_ts: int | None = None) -> dict[str, object]:
        now = int(time()) if now_ts is None else now_ts
        observations = self.store.count_observations()
        oldest_ts = self.store.oldest_observation_ts()
        age_days = 0.0 if oldest_ts is None else max(0.0, (now - oldest_ts) / 86400)
        return {
            "observations": observations,
            "oldest_observation_ts": oldest_ts,
            "age_days": age_days,
            "minimum_days_met": age_days >= 3.0,
            "maximum_days_reached": age_days >= 7.0,
        }
