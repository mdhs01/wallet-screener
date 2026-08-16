from dataclasses import dataclass, field


@dataclass(slots=True)
class SurfaceConfig:
    min_win_rate_7d: float = 0.40
    min_win_rate_30d: float = 0.40
    max_win_rate_for_investigation: float = 0.80
    min_realized_pnl_7d: float = 1.0
    min_realized_pnl_30d: float = 1.0
    min_pnl_ratio: float = 1.0
    ideal_pnl_ratio: float = 1.5
    # Calibrated against the live Smart Money sample: TX7 > 750 remains a
    # surface rejection, while lower frequency bands are classified rather
    # than rejected outright.
    max_tx_7d: int = 750
    normal_tx_7d_max: int = 300
    active_tx_7d_max: int = 500
    investigate_tx_30d: int = 3000
    min_token_diversity_30d: int = 10
    min_balance_native: float = 0.01
    require_cost: bool = True
    max_top_token_profit_share: float = 0.90


@dataclass(slots=True)
class DistributionConfig:
    max_lottery_share: float = 0.25
    max_top_two_token_profit_share: float = 0.95
    min_small_medium_win_share: float = 0.50
    max_daily_profit_cv: float = 2.0
    min_recent_profit_stability: float = 0.35


@dataclass(slots=True)
class BehaviorConfig:
    min_hold_consistency: float = 0.50
    min_winner_longer_than_loser_rate: float = 0.50
    max_style_change_score: float = 0.75
    min_residual_hold_rate: float = 0.20
    min_underwater_recovery_rate: float = 0.20
    max_bag_zero_ratio: float = 0.40


@dataclass(slots=True)
class RiskConfig:
    max_transfer_in_ratio: float = 0.20
    max_buy_sell_under_10s_ratio: float = 0.15
    max_blacklist_count: int = 0
    max_honeypot_count: int = 0
    max_rug_count: int = 0
    max_common_funder_count: int = 0
    max_cluster_size: int = 3
    max_creator_open_count: int = 10


@dataclass(slots=True)
class ConsistencyConfig:
    min_early_actionable_rate: float = 0.50
    min_current_conviction: float = 0.30
    min_cross_token_score: float = 0.50
    max_7d_30d_hot_streak_ratio: float = 3.0
    min_independence_score: float = 0.70


@dataclass(slots=True)
class ActionabilityConfig:
    min_style_match_score: float = 0.50
    max_crowding_score: float = 0.70
    min_actionability_score: float = 0.50
    max_latency_minutes: float = 10.0


@dataclass(slots=True)
class ManualQAConfig:
    min_sample_trades: int = 15
    max_sample_trades: int = 20
    min_actionable_rate: float = 0.50
    max_transfer_in_rate: float = 0.20
    min_complete_data_rate: float = 0.90
    min_repeatable_behavior_rate: float = 0.50
    require_manual_review_before_watchlist: bool = True


@dataclass(slots=True)
class PaperTrackConfig:
    min_days: int = 3
    max_days: int = 7
    min_observations: int = 10
    min_actionable_rate: float = 0.50
    max_false_signal_rate: float = 0.40
    max_missed_rate: float = 0.50
    min_positive_expectancy_pct: float = 0.0
    max_drawdown_pct: float = 30.0


@dataclass(slots=True)
class ScoreConfig:
    realized_performance_weight: float = 0.15
    pnl_ratio_weight: float = 0.10
    win_rate_weight: float = 0.08
    profit_distribution_weight: float = 0.10
    token_diversity_weight: float = 0.05
    holding_consistency_weight: float = 0.08
    entry_timing_weight: float = 0.08
    exit_behavior_weight: float = 0.05
    current_conviction_weight: float = 0.07
    funding_cleanliness_weight: float = 0.06
    cross_token_weight: float = 0.08
    style_match_weight: float = 0.05
    actionability_weight: float = 0.05


@dataclass(slots=True)
class ScreenerConfig:
    surface: SurfaceConfig = field(default_factory=SurfaceConfig)
    distribution: DistributionConfig = field(default_factory=DistributionConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    consistency: ConsistencyConfig = field(default_factory=ConsistencyConfig)
    actionability: ActionabilityConfig = field(default_factory=ActionabilityConfig)
    manual_qa: ManualQAConfig = field(default_factory=ManualQAConfig)
    paper_track: PaperTrackConfig = field(default_factory=PaperTrackConfig)
    score: ScoreConfig = field(default_factory=ScoreConfig)
    min_final_score: float = 7.0
    max_watchlist_size: int = 15
    paper_track_days: int = 3
