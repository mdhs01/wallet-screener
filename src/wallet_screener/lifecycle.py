from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from .paper_persistence import PaperObservationStore
from .paper_tracking import PaperObservation, PaperTracker
from .persistence import ScreeningStore
from .watchlist import WatchlistCategory, WatchlistManager, classify_category


@dataclass(slots=True)
class LifecycleResult:
    wallet: str
    status: str
    paper_summary: dict[str, Any] | None = None
    watchlist_entry: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)


class WalletLifecycle:
    """Connect screening persistence, paper tracking, and watchlist state.

    Paper observations are persisted in SQLite and reloaded for each wallet
    evaluation, so a process restart does not erase paper-track evidence.
    This layer never fetches market data or places orders.
    """

    def __init__(
        self,
        store: ScreeningStore | None = None,
        paper_tracker: PaperTracker | None = None,
        watchlist: WatchlistManager | None = None,
        paper_store: PaperObservationStore | None = None,
    ) -> None:
        self.store = store or ScreeningStore()
        self.paper_tracker = paper_tracker or PaperTracker()
        self.watchlist = watchlist or WatchlistManager()
        self.paper_store = paper_store or PaperObservationStore(self.store.path)

    def add_paper_observation(self, observation: PaperObservation) -> bool:
        """Persist and register an observation exactly once.

        The persistence layer is authoritative for idempotency. The in-memory
        tracker is updated only when the SQLite insert succeeds, preventing a
        duplicate ingest from being counted twice.
        """
        inserted = self.paper_store.add(observation, int(time()))
        if inserted:
            self.paper_tracker.add(observation)
        return inserted

    def _paper_summary(self, wallet: str):
        return self.paper_store.summary(wallet, self.paper_tracker)

    def evaluate_wallet(
        self,
        *,
        wallet: str,
        score: float,
        passed: bool,
        category: WatchlistCategory | None = None,
        timestamp: int | None = None,
        edge_decay_score: float = 0.0,
        style_change_score: float = 0.0,
        crowding_score: float = 0.0,
        independence_score: float = 1.0,
        notes: list[str] | None = None,
    ) -> LifecycleResult:
        ts = timestamp or int(time())
        paper_summary = self._paper_summary(wallet)
        selected_category = category or WatchlistCategory.EXPERIMENTAL

        effective_passed = bool(passed and paper_summary.ready_for_watchlist)
        lifecycle_notes = list(notes or [])
        if not paper_summary.ready_for_watchlist:
            lifecycle_notes.append("paper_tracking_not_ready")

        entry = self.watchlist.upsert(
            wallet=wallet,
            score=score,
            timestamp=ts,
            category=selected_category,
            passed=effective_passed,
            edge_decay_score=edge_decay_score,
            style_change_score=style_change_score,
            crowding_score=crowding_score,
            independence_score=independence_score,
            paper_summary=paper_summary,
            notes=lifecycle_notes,
        )

        status = entry.status.value
        lifecycle_notes = list(entry.notes[-5:])
        lifecycle_notes.append(f"paper_ready={paper_summary.ready_for_watchlist}")
        return LifecycleResult(
            wallet=wallet,
            status=status,
            paper_summary=paper_summary.to_dict(),
            watchlist_entry=entry.to_dict(),
            notes=lifecycle_notes,
        )

    def evaluate_screening_payload(self, payload: dict[str, Any], *, timestamp: int | None = None) -> LifecycleResult:
        wallet = str(payload["address"])
        metrics = payload.get("metrics") or {}
        style = metrics.get("style")
        category = classify_category(
            style=style,
            early_actionable_rate=float(metrics.get("early_actionable_rate", 0.0)),
            avg_hold_minutes=float(metrics.get("avg_hold_minutes", 0.0)),
            current_conviction=float(metrics.get("current_conviction", 0.0)),
        )
        return self.evaluate_wallet(
            wallet=wallet,
            score=float(payload.get("score", 0.0)),
            passed=bool(payload.get("passed", False)),
            category=category,
            timestamp=timestamp,
            independence_score=float(metrics.get("independence_score", 1.0)),
            crowding_score=float(metrics.get("crowding_score", 0.0)),
            style_change_score=float(metrics.get("style_change_score", 0.0)),
            notes=list(payload.get("warnings") or []),
        )
