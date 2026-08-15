from __future__ import annotations

from dataclasses import dataclass
from time import sleep, time
from typing import Callable, Iterable, Protocol

from .market_observation import MarketObservationAdapter, MarketSnapshot
from .paper_runtime import PersistentPaperRuntime


class MarketSnapshotSource(Protocol):
    def fetch(self) -> Iterable[MarketSnapshot]:
        ...


@dataclass(slots=True)
class FeedCycleReport:
    started_ts: int
    finished_ts: int
    fetched: int = 0
    accepted: int = 0
    duplicates: int = 0
    rejected: int = 0
    errors: int = 0


class InMemoryMarketSource:
    """Deterministic source for integration tests and dry-run development."""

    def __init__(self, snapshots: Iterable[MarketSnapshot] = ()) -> None:
        self.snapshots = list(snapshots)

    def fetch(self) -> Iterable[MarketSnapshot]:
        return list(self.snapshots)


class LiveMarketFeed:
    """Read-only polling loop that converts market snapshots into paper observations."""

    def __init__(
        self,
        source: MarketSnapshotSource,
        runtime: PersistentPaperRuntime,
        adapter: MarketObservationAdapter | None = None,
        *,
        on_observation: Callable[[object], None] | None = None,
    ) -> None:
        self.source = source
        self.runtime = runtime
        self.adapter = adapter or MarketObservationAdapter()
        self.on_observation = on_observation

    def cycle(self) -> FeedCycleReport:
        started = int(time())
        report = FeedCycleReport(started_ts=started, finished_ts=started)
        try:
            snapshots = list(self.source.fetch())
        except Exception:
            report.errors += 1
            report.finished_ts = int(time())
            return report

        report.fetched = len(snapshots)
        for snapshot in snapshots:
            try:
                observation = self.adapter.to_paper_observation(snapshot)
                inserted = self.runtime.ingest(observation)
                if inserted:
                    report.accepted += 1
                    if self.on_observation is not None:
                        self.on_observation(observation)
                else:
                    report.duplicates += 1
            except (ValueError, TypeError):
                report.rejected += 1
        report.finished_ts = int(time())
        return report

    def run_polling(self, *, interval_seconds: float, cycles: int | None = None) -> list[FeedCycleReport]:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        reports: list[FeedCycleReport] = []
        cycle_no = 0
        while cycles is None or cycle_no < cycles:
            reports.append(self.cycle())
            cycle_no += 1
            if cycles is None or cycle_no < cycles:
                sleep(interval_seconds)
        return reports
