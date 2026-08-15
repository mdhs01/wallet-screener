from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from .config import ScreenerConfig
from .persistence import ScreeningStore
from .providers import WalletDataProvider
from .screener import WalletScreener


@dataclass(slots=True)
class PipelineReport:
    run_id: int
    discovered: int = 0
    screened: int = 0
    passed: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"
    error: str | None = None


class ScreeningPipeline:
    """Single orchestration path from discovery to persisted screening results."""

    def __init__(
        self,
        provider: WalletDataProvider,
        config: ScreenerConfig | None = None,
        store: ScreeningStore | None = None,
    ) -> None:
        self.provider = provider
        self.config = config or ScreenerConfig()
        self.store = store or ScreeningStore()
        self.screener = WalletScreener(provider, self.config)

    def run(self, *, max_candidates: int | None = None) -> PipelineReport:
        started = int(time())
        run_id = self.store.start_run(started)
        report = PipelineReport(run_id=run_id)
        try:
            addresses = list(dict.fromkeys(self.provider.discover_wallets()))
            if max_candidates is not None:
                addresses = addresses[:max_candidates]
            report.discovered = len(addresses)

            for address in addresses:
                result = self.screener.screen(address)
                payload = self.screener.to_dict(result)
                report.results.append(payload)
                report.screened += 1
                report.passed += int(result.passed)
                self.store.save_result(run_id, address, payload, int(time()))

            self.store.finish_run(
                run_id,
                finished_ts=int(time()),
                discovered_count=report.discovered,
                screened_count=report.screened,
                passed_count=report.passed,
                status=report.status,
            )
            return report
        except Exception as exc:
            report.status = "failed"
            report.error = str(exc)
            self.store.finish_run(
                run_id,
                finished_ts=int(time()),
                discovered_count=report.discovered,
                screened_count=report.screened,
                passed_count=report.passed,
                status=report.status,
                error=report.error,
            )
            raise
