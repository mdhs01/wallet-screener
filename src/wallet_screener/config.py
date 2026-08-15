from dataclasses import dataclass


@dataclass(slots=True)
class SurfaceConfig:
    min_win_rate_7d: float = 0.40
    min_win_rate_30d: float = 0.40
    max_win_rate_for_auto_pass: float = 0.80
    min_realized_pnl_7d: float = 1.0
    min_realized_pnl_30d: float = 1.0
    min_pnl_ratio: float = 1.0
    ideal_pnl_ratio: float = 1.5
    max_tx_7d: int = 300
    investigate_tx_30d: int = 3000
    min_token_diversity_30d: int = 10
    min_balance_native: float = 0.01
    require_cost: bool = True
    max_top_token_profit_share: float = 0.90


@dataclass(slots=True)
class RiskConfig:
    max_transfer_in_ratio: float = 0.20
    max_buy_sell_under_10s_ratio: float = 0.15
    max_blacklist_count: int = 0
    max_honeypot_count: int = 0
    max_rug_count: int = 0
    max_common_funder_count: int = 0
    max_cluster_size: int = 3


@dataclass(slots=True)
class ConsistencyConfig:
    min_early_actionable_rate: float = 0.50
    min_current_conviction: float = 0.30
    min_hold_consistency: float = 0.50
    min_cross_token_score: float = 0.50


@dataclass(slots=True)
class ScoreConfig:
    realized_performance_weight: float = 0.20
    pnl_ratio_weight: float = 0.15
    win_rate_weight: float = 0.10
    profit_distribution_weight: float = 0.10
    token_diversity_weight: float = 0.05
    holding_consistency_weight: float = 0.10
    entry_timing_weight: float = 0.10
    current_conviction_weight: float = 0.05
    funding_cleanliness_weight: float = 0.05
    cross_token_weight: float = 0.05
    actionability_weight: float = 0.05


@dataclass(slots=True)
class ScreenerConfig:
    surface: SurfaceConfig = SurfaceConfig()
    risk: RiskConfig = RiskConfig()
    consistency: ConsistencyConfig = ConsistencyConfig()
    score: ScoreConfig = ScoreConfig()
    min_final_score: float = 7.0
    max_watchlist_size: int = 15
    paper_track_days: int = 3
