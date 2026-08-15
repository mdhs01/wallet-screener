from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from .lifecycle import WalletLifecycle
from .market_feed import LiveMarketFeed
from .pipeline import ScreeningPipeline


@dataclass(slots=True)
class UnifiedRuntimeReport:
    started_ts: int
    finished_ts: int
    screening_run_id: int | None = None
    discovered: int = 0
    screened: int = 0
    passed: int = 0
    market_fetched: int = 0
    market_accepted: int = 0
    market_duplicates: int = 0
    market_rejected: int = 0
    market_errors: int = 0
    lifecycle_evaluated: int = 0
    errors: list[str] = field(default_factory=list)


class UnifiedRuntimeJob:
    """Runs one read-only end-to-end screening + market + lifecycle cycle."""

    def __init__(
        self,
        *,
        screening_pipeline: ScreeningPipeline,
        market_feed: LiveMarketFeed,
        lifecycle: WalletLifecycle,
        max_candidates: int | None = None,
    ) -> None:
        self.screening_pipeline = screening_pipeline
        self.market_feed = market_feed
        self.lifecycle = lifecycle
        self.max_candidates = max_candidates

    def run_once(self) -> UnifiedRuntimeReport:
        started = int(time())
        report = UnifiedRuntimeReport(started_ts=started, finished_ts=started)

        try:
            screening = self.screening_pipeline.run(max_candidates=self.max_candidates)
            report.screening_run_id = screening.run_id
            report.discovered = screening.discovered
            report.screened = screening.screened
            report.passed = screening.passed

            for payload in screening.results:
                try:
                    self.lifecycle.evaluate_screening_payload(payload)
                    report.lifecycle_evaluated += 1
                except Exception as exc:  # keep other wallets/cycle alive
                    report.errors.append(f"lifecycle:{payload.get('address', 'unknown')}:{exc}")

            market = self.market_feed.cycle()
            report.market_fetched = market.fetched
            report.market_accepted = market.accepted
            report.market_duplicates = market.duplicates
            report.market_rejected = market.rejected
            report.market_errors = market.errors
        except Exception as exc:
            report.errors.append(f"runtime:{exc}")

        report.finished_ts = int(time())
        return report
