from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter, time

from .lifecycle import WalletLifecycle
from .market_feed import LiveMarketFeed
from .observability import Observability
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
        observability: Observability | None = None,
    ) -> None:
        self.screening_pipeline = screening_pipeline
        self.market_feed = market_feed
        self.lifecycle = lifecycle
        self.max_candidates = max_candidates
        self.observability = observability or Observability()

    def run_once(self) -> UnifiedRuntimeReport:
        started = int(time())
        started_perf = perf_counter()
        report = UnifiedRuntimeReport(started_ts=started, finished_ts=started)
        self.observability.event("runtime_cycle_started")

        try:
            screening = self.screening_pipeline.run(max_candidates=self.max_candidates)
            report.screening_run_id = screening.run_id
            report.discovered = screening.discovered
            report.screened = screening.screened
            report.passed = screening.passed

            self.observability.event(
                "screening_cycle_completed",
                context={
                    "run_id": screening.run_id,
                    "discovered": screening.discovered,
                    "screened": screening.screened,
                    "passed": screening.passed,
                },
            )

            for payload in screening.results:
                try:
                    self.lifecycle.evaluate_screening_payload(payload)
                    report.lifecycle_evaluated += 1
                except Exception as exc:  # keep other wallets/cycle alive
                    report.errors.append(f"lifecycle:{payload.get('address', 'unknown')}:{exc}")
                    self.observability.error(
                        "lifecycle_evaluation_failed",
                        error=exc,
                        context={"address": payload.get("address", "unknown")},
                    )

            market = self.market_feed.cycle()
            report.market_fetched = market.fetched
            report.market_accepted = market.accepted
            report.market_duplicates = market.duplicates
            report.market_rejected = market.rejected
            report.market_errors = market.errors
            self.observability.record_market(
                fetched=market.fetched,
                accepted=market.accepted,
                duplicates=market.duplicates,
                rejected=market.rejected,
                errors=market.errors,
            )
        except Exception as exc:
            report.errors.append(f"runtime:{exc}")
            self.observability.error("runtime_cycle_failed", error=exc)

        report.finished_ts = int(time())
        duration_ms = (perf_counter() - started_perf) * 1000
        success = not report.errors and report.market_errors == 0
        self.observability.record_cycle(
            success=success,
            duration_ms=duration_ms,
            discovered=report.discovered,
            passed=report.passed,
        )
        self.observability.event(
            "runtime_cycle_completed",
            context={
                "success": success,
                "duration_ms": duration_ms,
                "discovered": report.discovered,
                "passed": report.passed,
                "market_accepted": report.market_accepted,
                "market_duplicates": report.market_duplicates,
                "errors": len(report.errors) + report.market_errors,
            },
        )
        return report
