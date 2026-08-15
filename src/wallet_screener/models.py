from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Style = Literal["early_runner", "swing", "scalper", "high_conviction", "experimental"]


@dataclass(slots=True)
class WalletMetrics:
    address: str
    win_rate_7d: float = 0.0
    win_rate_30d: float = 0.0
    realized_pnl_7d: float = 0.0
    realized_pnl_30d: float = 0.0
    unrealized_pnl: float = 0.0
    total_cost_30d: float = 0.0
    tx_7d: int = 0
    tx_30d: int = 0
    token_diversity_30d: int = 0
    balance_native: float = 0.0
    cost_7d: float = 0.0
    cost_30d: float = 0.0
    avg_realized_profit: float = 0.0
    avg_token_cost: float = 0.0
    profit_buckets: dict[str, int] = field(default_factory=dict)
    avg_hold_minutes: float = 0.0
    winner_hold_minutes: float = 0.0
    loser_hold_minutes: float = 0.0
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
    early_actionable_rate: float = 0.0
    current_conviction: float = 0.0
    crowding_score: float = 0.0
    style: Optional[Style] = None

    @property
    def pnl_ratio(self) -> float:
        if self.total_cost_30d <= 0:
            return 0.0
        return self.realized_pnl_30d / self.total_cost_30d


@dataclass(slots=True)
class ScreeningResult:
    address: str
    passed: bool
    stage: str
    score: float
    reasons: list[str] = field(default_factory=list)
    failed_rules: list[str] = field(default_factory=list)
    metrics: WalletMetrics | None = None
