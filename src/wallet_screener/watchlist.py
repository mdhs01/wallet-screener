from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum

from .paper_tracking import PaperTrackSummary


class WatchlistCategory(StrEnum):
    EARLY_RUNNER = "early_runner"
    SWING = "swing"
    SCALPER = "scalper"
    HIGH_CONVICTION = "high_conviction"
    EXPERIMENTAL = "experimental"


class WatchlistStatus(StrEnum):
    ACTIVE = "active"
    REVIEW = "review"
    DEMOTED = "demoted"
    DROPPED = "dropped"


@dataclass(slots=True)
class RevalidationSnapshot:
    timestamp: int
    score: float
    realized_pnl_7d: float
    realized_pnl_30d: float
    win_rate_7d: float
    win_rate_30d: float
    actionability_score: float
    current_conviction: float
    style: str | None = None
    style_change_score: float = 0.0
    crowding_score: float = 0.0
    cluster_size: int = 1
    independence_score: float = 1.0
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WatchlistEntry:
    wallet: str
    category: WatchlistCategory
    status: WatchlistStatus = WatchlistStatus.REVIEW
    score: float = 0.0
    rank: int = 0
    consecutive_passes: int = 0
    consecutive_failures: int = 0
    edge_decay_score: float = 0.0
    last_revalidated_ts: int | None = None
    notes: list[str] = field(default_factory=list)
    history: list[RevalidationSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def classify_category(
    *,
    style: str | None,
    early_actionable_rate: float,
    avg_hold_minutes: float,
    current_conviction: float,
) -> WatchlistCategory:
    if style in WatchlistCategory._value2member_map_:
        return WatchlistCategory(style)
    if early_actionable_rate >= 0.70 and avg_hold_minutes <= 2880:
        return WatchlistCategory.EARLY_RUNNER
    if current_conviction >= 0.70 and avg_hold_minutes >= 1440:
        return WatchlistCategory.HIGH_CONVICTION
    if avg_hold_minutes < 10:
        return WatchlistCategory.SCALPER
    if avg_hold_minutes <= 10080:
        return WatchlistCategory.SWING
    return WatchlistCategory.EXPERIMENTAL


class WatchlistManager:
    """Dynamic 5–15 wallet watchlist with weekly revalidation and edge-decay handling."""

    def __init__(
        self,
        *,
        max_size: int = 15,
        min_score: float = 7.0,
        review_below_score: float = 6.0,
        drop_below_score: float = 5.0,
        max_crowding_score: float = 0.70,
        max_style_change_score: float = 0.75,
        min_independence_score: float = 0.70,
        max_edge_decay_score: float = 0.60,
    ) -> None:
        if max_size < 1:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self.min_score = min_score
        self.review_below_score = review_below_score
        self.drop_below_score = drop_below_score
        self.max_crowding_score = max_crowding_score
        self.max_style_change_score = max_style_change_score
        self.min_independence_score = min_independence_score
        self.max_edge_decay_score = max_edge_decay_score
        self._entries: dict[str, WatchlistEntry] = {}

    def entries(self) -> list[WatchlistEntry]:
        return sorted(self._entries.values(), key=lambda item: (-item.score, item.wallet))

    def upsert(
        self,
        *,
        wallet: str,
        score: float,
        timestamp: int,
        category: WatchlistCategory,
        passed: bool,
        edge_decay_score: float = 0.0,
        style_change_score: float = 0.0,
        crowding_score: float = 0.0,
        independence_score: float = 1.0,
        paper_summary: PaperTrackSummary | None = None,
        notes: list[str] | None = None,
    ) -> WatchlistEntry:
        entry = self._entries.get(wallet)
        if entry is None:
            entry = WatchlistEntry(wallet=wallet, category=category)
            self._entries[wallet] = entry

        if passed:
            entry.consecutive_passes += 1
            entry.consecutive_failures = 0
        else:
            entry.consecutive_failures += 1
            entry.consecutive_passes = 0

        entry.score = score
        entry.last_revalidated_ts = timestamp
        entry.category = category
        entry.edge_decay_score = edge_decay_score
        if notes:
            entry.notes.extend(notes)

        if paper_summary is not None and not paper_summary.ready_for_watchlist:
            entry.notes.append("paper_tracking_not_ready")
            passed = False

        if not passed or score < self.review_below_score:
            entry.status = WatchlistStatus.REVIEW
        else:
            entry.status = WatchlistStatus.ACTIVE

        if score < self.drop_below_score or edge_decay_score > self.max_edge_decay_score:
            entry.status = WatchlistStatus.DROPPED
        elif style_change_score > self.max_style_change_score or crowding_score > self.max_crowding_score or independence_score < self.min_independence_score:
            entry.status = WatchlistStatus.REVIEW
            entry.notes.append("structural_revalidation_warning")

        return entry

    def revalidate(
        self,
        *,
        timestamp: int,
        wallet: str,
        snapshot: RevalidationSnapshot,
    ) -> WatchlistEntry:
        entry = self._entries.get(wallet)
        if entry is None:
            entry = WatchlistEntry(wallet=wallet, category=WatchlistCategory.EXPERIMENTAL)
            self._entries[wallet] = entry

        previous = entry.history[-1] if entry.history else None
        if previous is not None:
            entry.edge_decay_score = self._calculate_edge_decay(previous, snapshot)

        entry.history.append(snapshot)
        entry.score = snapshot.score
        entry.last_revalidated_ts = timestamp
        entry.edge_decay_score = max(entry.edge_decay_score, snapshot_change_decay(previous, snapshot))

        if snapshot.style and snapshot.style in WatchlistCategory._value2member_map_:
            entry.category = WatchlistCategory(snapshot.style)
        if snapshot.score >= self.min_score and entry.edge_decay_score <= self.max_edge_decay_score:
            entry.status = WatchlistStatus.ACTIVE
            entry.consecutive_passes += 1
            entry.consecutive_failures = 0
        elif snapshot.score < self.drop_below_score or entry.edge_decay_score > self.max_edge_decay_score:
            entry.status = WatchlistStatus.DROPPED
            entry.consecutive_failures += 1
            entry.consecutive_passes = 0
        else:
            entry.status = WatchlistStatus.REVIEW
            entry.consecutive_failures += 1
            entry.consecutive_passes = 0

        return entry

    @staticmethod
    def _calculate_edge_decay(previous: RevalidationSnapshot, current: RevalidationSnapshot) -> float:
        score_drop = max(0.0, previous.score - current.score) / 10.0
        actionability_drop = max(0.0, previous.actionability_score - current.actionability_score)
        conviction_drop = max(0.0, previous.current_conviction - current.current_conviction)
        pnl_decay = 0.0
        if previous.realized_pnl_30d > 0:
            pnl_decay = max(0.0, 1.0 - current.realized_pnl_30d / previous.realized_pnl_30d)
        return min(1.0, 0.35 * score_drop + 0.25 * actionability_drop + 0.20 * conviction_drop + 0.20 * pnl_decay)

    def enforce_capacity(self) -> list[WatchlistEntry]:
        active = [e for e in self.entries() if e.status == WatchlistStatus.ACTIVE]
        keep = active[: self.max_size]
        keep_wallets = {e.wallet for e in keep}
        for entry in active[self.max_size :]:
            entry.status = WatchlistStatus.REVIEW
            entry.notes.append("watchlist_capacity_limit")
        return [e for e in self.entries() if e.wallet in keep_wallets]

    def promote_ready(self) -> list[WatchlistEntry]:
        candidates = [
            e
            for e in self.entries()
            if e.status == WatchlistStatus.REVIEW
            and e.score >= self.min_score
            and e.edge_decay_score <= self.max_edge_decay_score
            and e.consecutive_passes >= 1
        ]
        for entry in candidates:
            entry.status = WatchlistStatus.ACTIVE
        return self.enforce_capacity()

    def export(self) -> dict:
        return {"entries": [entry.to_dict() for entry in self.entries()]}


def snapshot_change_decay(previous: RevalidationSnapshot | None, current: RevalidationSnapshot) -> float:
    if previous is None:
        return 0.0
    if previous.realized_pnl_30d <= 0:
        return 0.0
    pnl_decay = max(0.0, 1.0 - current.realized_pnl_30d / previous.realized_pnl_30d)
    return min(
        1.0,
        0.40 * max(0.0, previous.score - current.score) / 10.0
        + 0.25 * max(0.0, previous.actionability_score - current.actionability_score)
        + 0.20 * max(0.0, previous.current_conviction - current.current_conviction)
        + 0.15 * pnl_decay,
    )
