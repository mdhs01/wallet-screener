from __future__ import annotations

from dataclasses import asdict

from .analytics import actionability_score, calculate_derived_metrics, divergence_label, distribution_score
from .config import ScreenerConfig
from .models import HoldingSnapshot, ScreeningResult, TradeObservation, WalletMetrics
from .providers import WalletDataProvider


class WalletScreener:
    """Deterministic, API-agnostic wallet screening engine.

    Provider/API code is deliberately kept outside this class so thresholds and
    screening logic can be tuned without changing data acquisition.
    """

    def __init__(self, provider: WalletDataProvider, config: ScreenerConfig | None = None) -> None:
        self.provider = provider
        self.config = config or ScreenerConfig()

    def screen(self, address: str) -> ScreeningResult:
        raw = self.provider.get_wallet_metrics(address)
        metrics = WalletMetrics(**{k: v for k, v in raw.items() if k in WalletMetrics.__dataclass_fields__})
        metrics.address = address

        warnings: list[str] = []
        reasons: list[str] = []
        failed: list[str] = []
        layer_scores: dict[str, float] = {}

        # Layers 10–11 — current holdings and manual trade sample inputs.
        holdings = [HoldingSnapshot(**{k: v for k, v in h.items() if k in HoldingSnapshot.__dataclass_fields__}) for h in self.provider.get_current_holdings(address)]
        trades = [TradeObservation(**{k: v for k, v in t.items() if k in TradeObservation.__dataclass_fields__}) for t in self.provider.get_trade_sample(address, limit=20)]
        metrics = calculate_derived_metrics(metrics, trades)
        self._apply_holdings(metrics, holdings)

        # Layer 2 — Surface filter.
        if metrics.win_rate_7d < self.config.surface.min_win_rate_7d:
            failed.append("win_rate_7d_below_min")
        if metrics.win_rate_30d < self.config.surface.min_win_rate_30d:
            failed.append("win_rate_30d_below_min")
        if metrics.realized_pnl_7d < self.config.surface.min_realized_pnl_7d:
            failed.append("realized_pnl_7d_not_meaningful")
        if metrics.realized_pnl_30d < self.config.surface.min_realized_pnl_30d:
            failed.append("realized_pnl_30d_not_meaningful")
        if metrics.pnl_ratio < self.config.surface.min_pnl_ratio:
            failed.append("pnl_ratio_below_min")
        if metrics.tx_7d > self.config.surface.max_tx_7d:
            failed.append("tx_7d_too_high")
        if metrics.tx_30d > self.config.surface.investigate_tx_30d:
            warnings.append("tx_30d_requires_investigation")
        if metrics.token_diversity_30d < self.config.surface.min_token_diversity_30d:
            failed.append("token_diversity_too_low")
        if metrics.balance_native < self.config.surface.min_balance_native:
            failed.append("balance_too_low")
        if self.config.surface.require_cost and (metrics.cost_7d <= 0 or metrics.cost_30d <= 0):
            failed.append("zero_cost_anomaly")
        if metrics.profit_top_token_share >= self.config.surface.max_top_token_profit_share:
            failed.append("single_token_profit_dependency")
        if metrics.win_rate_7d >= self.config.surface.max_win_rate_for_investigation or metrics.win_rate_30d >= self.config.surface.max_win_rate_for_investigation:
            warnings.append("extreme_win_rate_requires_investigation")

        if failed:
            return ScreeningResult(address, False, "surface_filter", 0.0, reasons, failed, warnings, metrics, layer_scores)

        layer_scores["surface"] = 1.0

        # Layers 3–5 — realized performance and profit distribution.
        if metrics.unrealized_to_realized_ratio > 10:
            warnings.append("unrealized_pnl_dominant")
        else:
            reasons.append("realized_performance_healthy")

        distribution = distribution_score(metrics)
        layer_scores["profit_distribution"] = distribution
        lottery_share = metrics.profit_buckets.get(">5x", 0) / max(sum(metrics.profit_buckets.values()), 1)
        small_medium = (metrics.profit_buckets.get("0–2x", 0) + metrics.profit_buckets.get("2–5x", 0)) / max(sum(metrics.profit_buckets.values()), 1)
        if lottery_share > self.config.distribution.max_lottery_share:
            warnings.append("lottery_dependency")
        if small_medium >= self.config.distribution.min_small_medium_win_share:
            reasons.append("small_medium_wins_are_material")
        if metrics.profit_top_two_token_share >= self.config.distribution.max_top_two_token_profit_share:
            warnings.append("top_two_token_dependency")
        if metrics.daily_profit_series:
            if metrics.recent_profit_stability < self.config.distribution.min_recent_profit_stability:
                warnings.append("daily_profit_series_unstable")
            if metrics.recent_profit_stability >= self.config.distribution.min_recent_profit_stability:
                reasons.append("daily_profit_series_has_repeatability")

        # Layers 6–7 — transaction frequency and holding behavior.
        transfer_ratio = metrics.transfer_in_count / max(metrics.trade_count_30d, 1)
        fast_ratio = metrics.buy_sell_under_10s / max(metrics.trade_count_30d, 1)
        if transfer_ratio > self.config.risk.max_transfer_in_ratio:
            failed.append("transfer_in_ratio_too_high")
        if fast_ratio > self.config.risk.max_buy_sell_under_10s_ratio:
            failed.append("ultra_short_trade_ratio_too_high")
        if metrics.hold_consistency < self.config.behavior.min_hold_consistency:
            failed.append("holding_behavior_inconsistent")
        if metrics.winner_longer_than_loser_rate < self.config.behavior.min_winner_longer_than_loser_rate:
            warnings.append("winner_loser_holding_relationship_weak")
        if metrics.bag_zero_count > max(1, int(metrics.trade_count_30d * self.config.behavior.max_bag_zero_ratio)):
            warnings.append("bag_zero_ratio_high")
        if metrics.style_change_score > self.config.behavior.max_style_change_score:
            warnings.append("style_change_detected")

        layer_scores["holding_behavior"] = max(0.0, min(1.0, metrics.hold_consistency))

        # Layers 12–13 — transfer-in and risk/phishing behavior.
        if metrics.blacklist_count > self.config.risk.max_blacklist_count:
            failed.append("blacklist_risk")
        if metrics.honeypot_count > self.config.risk.max_honeypot_count:
            failed.append("honeypot_risk")
        if metrics.rug_count > self.config.risk.max_rug_count:
            failed.append("rug_risk")
        if metrics.common_funder_count > self.config.risk.max_common_funder_count:
            failed.append("common_funder_risk")
        if metrics.cluster_size > self.config.risk.max_cluster_size:
            failed.append("cluster_too_large")
        if metrics.creator_open_count > self.config.risk.max_creator_open_count:
            warnings.append("creator_or_deployer_activity_high")
        if metrics.did_not_buy_count > 0:
            warnings.append("did_not_buy_activity_present")
        if metrics.sold_more_than_bought > 0:
            warnings.append("sold_more_than_bought_present")

        # Layers 14–15 — cross-token consistency and actionable early entry.
        cross = self.provider.get_cross_token_evidence(address)
        cross_score = cross.score
        layer_scores["cross_token"] = cross_score
        if cross_score < self.config.consistency.min_cross_token_score:
            failed.append("cross_token_consistency_weak")
        else:
            reasons.append("cross_token_repeatability_verified")
        if metrics.early_actionable_rate < self.config.consistency.min_early_actionable_rate:
            failed.append("entry_not_actionable_enough")

        # Layers 16–17 — funding / cluster independence.
        funding = self.provider.get_funding_cluster(address)
        metrics.common_funder_count = int(funding.get("common_funder_count", metrics.common_funder_count))
        metrics.cluster_size = int(funding.get("cluster_size", metrics.cluster_size))
        metrics.independence_score = float(funding.get("independence_score", metrics.independence_score))
        if metrics.independence_score < self.config.consistency.min_independence_score:
            failed.append("funding_independence_weak")

        # Layer 18 — 7D vs 30D divergence.
        divergence = divergence_label(metrics)
        if divergence == "hot_streak":
            warnings.append("7d_hot_streak_vs_30d")
        elif divergence == "decaying":
            warnings.append("7d_performance_decaying")
        elif divergence == "strong_consistency":
            reasons.append("7d_30d_consistency_strong")
        layer_scores["recency_consistency"] = {"strong_consistency": 1.0, "mixed": 0.5, "hot_streak": 0.35, "decaying": 0.25}[divergence]

        # Layers 19–22 — daily series, underwater conviction, size and style.
        if metrics.underwater_recovery_rate >= self.config.behavior.min_underwater_recovery_rate:
            reasons.append("underwater_recovery_behavior_supported")
        if metrics.current_conviction < self.config.consistency.min_current_conviction:
            failed.append("current_conviction_low")
        if metrics.residual_hold_rate < self.config.behavior.min_residual_hold_rate:
            warnings.append("residual_hold_rate_low")
        if metrics.style_match_score < self.config.actionability.min_style_match_score:
            warnings.append("style_match_weak")
        if metrics.crowding_score > self.config.actionability.max_crowding_score:
            failed.append("public_crowding_too_high")

        # Actionability is deliberately a separate metric.
        actionability = actionability_score(metrics)
        layer_scores["actionability"] = actionability
        if actionability < self.config.actionability.min_actionability_score:
            failed.append("actionability_score_too_low")

        # Layers 23–25 — final composite and classification.
        score = self._score(metrics, distribution, cross_score, transfer_ratio, fast_ratio, actionability)
        passed = not failed and score >= self.config.min_final_score
        stage = "final_watchlist" if passed else "deep_review"
        if passed:
            reasons.append("repeatable_edge_candidate")
        else:
            reasons.append("requires_manual_or_further_review")

        return ScreeningResult(address, passed, stage, score, reasons, failed, warnings, metrics, layer_scores)

    @staticmethod
    def _apply_holdings(metrics: WalletMetrics, holdings: list[HoldingSnapshot]) -> None:
        if not holdings:
            return
        total_original = sum(max(h.original_value, 0.0) for h in holdings)
        current_winner = sum(max(h.current_value, 0.0) for h in holdings if h.unrealized_pnl > 0)
        current_total = sum(max(h.current_value, 0.0) for h in holdings)
        if total_original > 0:
            metrics.current_conviction = max(metrics.current_conviction, min(1.0, current_total / total_original))
        if current_total > 0:
            metrics.current_winner_exposure = current_winner / current_total
        metrics.bag_zero_count = max(metrics.bag_zero_count, sum(1 for h in holdings if h.is_zero_value))
        residual = sum(1 for h in holdings if h.held_after_partial_tp)
        metrics.residual_hold_rate = max(metrics.residual_hold_rate, residual / len(holdings))
        recovered = sum(1 for h in holdings if h.underwater_then_recovered)
        accumulated = sum(1 for h in holdings if h.accumulated_underwater)
        metrics.underwater_recovery_rate = max(metrics.underwater_recovery_rate, recovered / len(holdings))
        metrics.underwater_accumulation_rate = max(metrics.underwater_accumulation_rate, accumulated / len(holdings))

    def _score(self, m: WalletMetrics, distribution: float, cross_token_score: float, transfer_ratio: float, fast_ratio: float, actionability: float) -> float:
        s = self.config.score

        def clamp(x: float) -> float:
            return max(0.0, min(1.0, x))

        realized = clamp(m.realized_pnl_30d / 100000.0)
        pnl_ratio = clamp(m.pnl_ratio / 2.0)
        wr = clamp((m.win_rate_7d + m.win_rate_30d) / 2)
        diversity = clamp(m.token_diversity_30d / 10.0)
        holding = clamp(m.hold_consistency)
        entry = clamp(m.early_actionable_rate)
        exit_behavior = clamp((m.winner_longer_than_loser_rate + m.residual_hold_rate) / 2)
        conviction = clamp(m.current_conviction)
        funding = clamp(m.independence_score * (1.0 - min(1.0, transfer_ratio + fast_ratio)))
        style = clamp(m.style_match_score)

        return 10 * (
            realized * s.realized_performance_weight
            + pnl_ratio * s.pnl_ratio_weight
            + wr * s.win_rate_weight
            + distribution * s.profit_distribution_weight
            + diversity * s.token_diversity_weight
            + holding * s.holding_consistency_weight
            + entry * s.entry_timing_weight
            + exit_behavior * s.exit_behavior_weight
            + conviction * s.current_conviction_weight
            + funding * s.funding_cleanliness_weight
            + cross_token_score * s.cross_token_weight
            + style * s.style_match_weight
            + actionability * s.actionability_weight
        )

    def screen_many(self, addresses: list[str]) -> list[ScreeningResult]:
        return [self.screen(address) for address in addresses]

    @staticmethod
    def to_dict(result: ScreeningResult) -> dict:
        payload = {
            "address": result.address,
            "passed": result.passed,
            "stage": result.stage,
            "score": result.score,
            "reasons": result.reasons,
            "failed_rules": result.failed_rules,
            "warnings": result.warnings,
            "layer_scores": result.layer_scores,
        }
        if result.metrics:
            payload["metrics"] = asdict(result.metrics)
        return payload
