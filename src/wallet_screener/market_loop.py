from __future__ import annotations

from dataclasses import dataclass
from time import time

from .market_feed import FeedCycleReport, LiveMarketFeed


@dataclass(slots=True)
class MarketLoopReport:
    started_ts: int
    finished_ts: int
    cycles: int = 0
    fetched: int = 0
    accepted: int = 0
    duplicates: int = 0
    rejected: int = 0
    errors: int = 0


class LiveMarketLoop:
    """Bounded lifecycle runner for read-only market observation ingestion."""

    def __init__(self, feed: LiveMarketFeed) -> None:
        self.feed = feed

    def run(self, *, interval_seconds: float, cycles: int) -> MarketLoopReport:
        if cycles <= 0:
            raise ValueError("cycles must be > 0")
        started = int(time())
        reports: list[FeedCycleReport] = self.feed.run_polling(
            interval_seconds=interval_seconds,
            cycles=cycles,
        )
        return MarketLoopReport(
            started_ts=started,
            finished_ts=int(time()),
            cycles=len(reports),
            fetched=sum(r.fetched for r in reports),
            accepted=sum(r.accepted for r in reports),
            duplicates=sum(r.duplicates for r in reports),
            rejected=sum(r.rejected for r in reports),
            errors=sum(r.errors for r in reports),
        )
