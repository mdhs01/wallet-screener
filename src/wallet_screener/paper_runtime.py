from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Protocol

from .lifecycle import LifecycleResult, WalletLifecycle
from .paper_persistence import PaperObservationStore
from .paper_tracking import PaperObservation


class PaperObservationSource(Protocol):
    """Supplies read-only market observations for a tracked wallet/token."""

    def observe(self, wallet: str) -> list[PaperObservation]:
        ...


@dataclass(slots=True)
class PaperRuntimeReport:
    wallet: str
    observed: int = 0
    inserted: int = 0
    duplicates: int = 0
    lifecycle: LifecycleResult | None = None


class PersistentPaperRuntime:
    """Read-only runtime that persists observations before evaluating lifecycle."""

    def __init__(self, lifecycle: WalletLifecycle | None = None, store: PaperObservationStore | None = None) -> None:
        self.lifecycle = lifecycle or WalletLifecycle()
        self.store = store or PaperObservationStore(self.lifecycle.store.path)

    def ingest(self, wallet: str, source: PaperObservationSource) -> PaperRuntimeReport:
        report = PaperRuntimeReport(wallet=wallet)
        observations = source.observe(wallet)
        report.observed = len(observations)
        for observation in observations:
            if observation.wallet != wallet:
                continue
            if self._persist_once(observation):
                report.inserted += 1
            else:
                report.duplicates += 1

        entry = next((item for item in self.lifecycle.watchlist.entries() if item.wallet == wallet), None)
        if entry is not None:
            report.lifecycle = self.lifecycle.evaluate_wallet(
                wallet=wallet,
                score=entry.score,
                passed=entry.status.value in {"active", "review"},
                category=entry.category,
                independence_score=1.0,
            )
        return report

    def ingest_observations(self, observations: list[PaperObservation]) -> PaperRuntimeReport:
        wallet = observations[0].wallet if observations else ""
        report = PaperRuntimeReport(wallet=wallet)
        for observation in observations:
            report.observed += 1
            if self._persist_once(observation):
                report.inserted += 1
            else:
                report.duplicates += 1
        return report

    def _persist_once(self, observation: PaperObservation) -> bool:
        """Persist the observation and update lifecycle exactly once."""
        inserted = self.store.add(observation, int(time()))
        if inserted:
            self.lifecycle.paper_tracker.add(observation)
        return inserted
