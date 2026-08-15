from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Style = Literal["early_runner", "swing", "scalper", "high_conviction", "experimental"]


@dataclass(slots=True)
class HoldingSnapshot:
    token: str
    current_value: float = 0.0
    original_value: float = 0.0
    unrealized_pnl: float = 0.0
    original_position_pct: float = 0.0
    held_after_partial_tp: bool = False
    is_zero_value: bool = False
    underwater_then_recovered: bool = False
    accumulated_underwater: bool = False


@dataclass(slots=True)
class TradeObservation:
    token: str
    launch_ts: int | None = None
    entry_ts: int | None = None
    exit_ts: int | None = None
    buy_size_usd: float = 0.0
    liquidity_at_entry_usd: float = 0.0
    realized_pnl_usd: float = 0.0
    realized_roi: float = 0.0
    transfer_in: bool = False
    actionable: bool = False
    partial_tp: bool = False
    residual_hold: bool = False
    cut_loss: bool = False

    @property
    def hold_minutes(self) -> float:
        if self.entry_ts is None or self.exit_ts is None or self.exit_ts < self.entry_ts:
            return 0.0
        return (self.exit_ts - self.entry_ts) / 60.0


@dataclass(slots=True)
class WalletMetrics:
    address: str
    win_rate_7d: float = 0.0
    win_rate_30d: float = 0.0
    realized_pnl_7d: float = 0.0
    realized_pnl_30d: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl_30d: float = 0.0
    total_cost_30d: float = 0.0
    tx_7d: int = 0
    tx_30d: int = 0
    token_diversity_30d: int = 0
    balance_native: float = 0.0
    cost_7d: float = 0.0
    cost_30d: float = 0.0
    avg_realized_profit: float = 0.0
    avg_token_cost: float = 0.0
    avg_buy_size_usd: float = 0.0
    median_buy_size_usd: float = 0.0
    profit_buckets: dict[str, int] = field(default_factory=dict)
    daily_profit_series: list[float] = field(default_factory=list)
    holding_period_buckets: dict[str, int] = field(default_factory=dict)
    avg_hold_minutes: float = 0.0
    hold_variance: float = 0.0
    winner_hold_minutes: float = 0.0
    loser_hold_minutes: float = 0.0
    winner_hold_variance: float = 0.0
    loser_hold_variance: float = 0.0
    winner_longer_than_loser_rate: float = 0.0
    hold_consistency: float = 0.0
    transfer_in_count: int = 0
    trade_count_30d: int = 0
    blacklist_count: int = 0
    honeypot_count: int = 0
    rug_count: int = 0
    buy_sell_under_10s: int = 0
    sold_more_than_bought: int = 0
    did_not_buy_count: int = 0
    common_funder_count: int = 0
    cluster_size: int = 1
    creator_open_count: int = 0
    profit_top_token_share: float = 0.0
    profit_top_two_token_share: float = 0.0
    early_entry_rate: float = 0.0
    early_actionable_rate: float = 0.0
    current_conviction: float = 0.0
    current_winner_exposure: float = 0.0
    residual_hold_rate: float = 0.0
    bag_zero_count: int = 0
    underwater_recovery_rate: float = 0.0
    underwater_accumulation_rate: float = 0.0
    style_change_score: float = 0.0
    crowding_score: float = 0.0
    public_followers: int = 0
    style: Optional[Style] = None
    style_match_score: float = 0.0
    independence_score: float = 1.0
    pnl_7d_vs_30d_ratio: float = 0.0
    recent_profit_stability: float = 0.0

    @property
    def pnl_ratio(self) -> float:
        if self.total_cost_30d <= 0:
            return 0.0
        return self.realized_pnl_30d / self.total_cost_30d

    @property
    def unrealized_to_realized_ratio(self) -> float:
        if self.realized_pnl_30d <= 0:
            return float("inf") if self.unrealized_pnl > 0 else 0.0
        return self.unrealized_pnl / self.realized_pnl_30d


@dataclass(slots=True)
class ScreeningResult:
    address: str
    passed: bool
    stage: str
    score: float
    reasons: list[str] = field(default_factory=list)
    failed_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: WalletMetrics | None = None
    layer_scores: dict[str, float] = field(default_factory=dict)
