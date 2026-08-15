from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean


@dataclass(slots=True)
class PaperObservation:
    wallet: str
    token: str
    signal_ts: int
    wallet_entry_ts: int | None = None
    wallet_exit_ts: int | None = None
    wallet_entry_price: float = 0.0
    wallet_exit_price: float = 0.0
    hypothetical_entry_ts: int | None = None
    hypothetical_exit_ts: int | None = None
    hypothetical_entry_price: float = 0.0
    hypothetical_exit_price: float = 0.0
    liquidity_at_signal_usd: float = 0.0
    hypothetical_position_usd: float = 0.0
    slippage_pct: float = 0.0
    missed: bool = False
    false_signal: bool = False
    actionable: bool = False
    notes: str = ""

    @property
    def wallet_return_pct(self) -> float:
        if self.wallet_entry_price <= 0 or self.wallet_exit_price <= 0:
            return 0.0
        return (self.wallet_exit_price / self.wallet_entry_price - 1.0) * 100.0

    @property
    def hypothetical_return_pct(self) -> float:
        if self.hypothetical_entry_price <= 0 or self.hypothetical_exit_price <= 0:
            return 0.0
        return (self.hypothetical_exit_price / self.hypothetical_entry_price - 1.0) * 100.0

    @property
    def latency_minutes(self) -> float | None:
        if self.signal_ts is None or self.hypothetical_entry_ts is None:
            return None
        if self.hypothetical_entry_ts < self.signal_ts:
            return None
        return (self.hypothetical_entry_ts - self.signal_ts) / 60.0


@dataclass(slots=True)
class PaperTrackSummary:
    wallet: str
    observations: int = 0
    actionable_count: int = 0
    false_signal_count: int = 0
    missed_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    actionable_rate: float = 0.0
    false_signal_rate: float = 0.0
    missed_rate: float = 0.0
    average_return_pct: float = 0.0
    median_return_pct: float = 0.0
    cumulative_return_pct: float = 0.0
    average_latency_minutes: float = 0.0
    max_drawdown_pct: float = 0.0
    average_slippage_pct: float = 0.0
    ready_for_watchlist: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PaperTracker:
    """Deterministic paper-tracking layer; no live orders or external APIs."""

    def __init__(
        self,
        *,
        min_days: int = 3,
        max_days: int = 7,
        min_observations: int = 10,
        min_actionable_rate: float = 0.50,
        max_false_signal_rate: float = 0.40,
        max_missed_rate: float = 0.50,
        min_positive_expectancy_pct: float = 0.0,
        max_drawdown_pct: float = 30.0,
    ) -> None:
        if min_days <= 0 or max_days < min_days:
            raise ValueError("Invalid paper tracking day range")
        self.min_days = min_days
        self.max_days = max_days
        self.min_observations = min_observations
        self.min_actionable_rate = min_actionable_rate
        self.max_false_signal_rate = max_false_signal_rate
        self.max_missed_rate = max_missed_rate
        self.min_positive_expectancy_pct = min_positive_expectancy_pct
        self.max_drawdown_pct = max_drawdown_pct
        self._observations: dict[str, list[PaperObservation]] = {}

    def add(self, observation: PaperObservation) -> None:
        self._observations.setdefault(observation.wallet, []).append(observation)

    def observations(self, wallet: str) -> list[PaperObservation]:
        return list(self._observations.get(wallet, []))

    def summarize(self, wallet: str) -> PaperTrackSummary:
        obs = self.observations(wallet)
        summary = PaperTrackSummary(wallet=wallet, observations=len(obs))
        if not obs:
            summary.warnings.append("no_paper_observations")
            return summary

        returns = [o.hypothetical_return_pct for o in obs if o.hypothetical_entry_price > 0 and o.hypothetical_exit_price > 0]
        actionable = [o for o in obs if o.actionable]
        latencies = [o.latency_minutes for o in obs if o.latency_minutes is not None]

        summary.actionable_count = len(actionable)
        summary.false_signal_count = sum(1 for o in obs if o.false_signal)
        summary.missed_count = sum(1 for o in obs if o.missed)
        summary.actionable_rate = summary.actionable_count / len(obs)
        summary.false_signal_rate = summary.false_signal_count / len(obs)
        summary.missed_rate = summary.missed_count / len(obs)

        if returns:
            summary.positive_count = sum(1 for r in returns if r > 0)
            summary.negative_count = sum(1 for r in returns if r < 0)
            summary.average_return_pct = mean(returns)
            ordered = sorted(returns)
            mid = len(ordered) // 2
            summary.median_return_pct = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
            equity = 100.0
            peak = equity
            max_dd = 0.0
            for r in returns:
                equity *= max(0.0, 1.0 + r / 100.0)
                peak = max(peak, equity)
                dd = (equity / peak - 1.0) * 100.0
                max_dd = min(max_dd, dd)
            summary.cumulative_return_pct = equity - 100.0
            summary.max_drawdown_pct = abs(max_dd)

        if latencies:
            summary.average_latency_minutes = mean(latencies)
        summary.average_slippage_pct = mean(o.slippage_pct for o in obs)

        if not returns:
            summary.warnings.append("insufficient_return_observations")
        if summary.actionable_rate < self.min_actionable_rate:
            summary.warnings.append("actionable_rate_below_target")
        if summary.false_signal_rate > self.max_false_signal_rate:
            summary.warnings.append("false_signal_rate_high")
        if summary.missed_rate > self.max_missed_rate:
            summary.warnings.append("missed_signal_rate_high")
        if summary.average_return_pct <= self.min_positive_expectancy_pct:
            summary.warnings.append("paper_expectancy_not_positive")
        if summary.max_drawdown_pct > self.max_drawdown_pct:
            summary.warnings.append("paper_drawdown_too_high")
        if summary.observations < self.min_observations:
            summary.warnings.append("paper_sample_too_small")

        summary.ready_for_watchlist = (
            summary.observations >= self.min_observations
            and summary.actionable_rate >= self.min_actionable_rate
            and summary.false_signal_rate <= self.max_false_signal_rate
            and summary.missed_rate <= self.max_missed_rate
            and summary.average_return_pct > self.min_positive_expectancy_pct
            and summary.max_drawdown_pct <= self.max_drawdown_pct
        )
        return summary

    def export(self, wallet: str) -> dict:
        return {
            "summary": self.summarize(wallet).to_dict(),
            "observations": [asdict(item) for item in self.observations(wallet)],
        }
