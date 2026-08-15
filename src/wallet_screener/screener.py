from __future__ import annotations

from dataclasses import asdict

from .config import ScreenerConfig
from .models import ScreeningResult, WalletMetrics
from .providers import WalletDataProvider


class WalletScreener:
    def __init__(self, provider: WalletDataProvider, config: ScreenerConfig | None = None) -> None:
        self.provider = provider
        self.config = config or ScreenerConfig()

    def screen(self, address: str) -> ScreeningResult:
        raw = self.provider.get_wallet_metrics(address)
        metrics = WalletMetrics(**{k: v for k, v in raw.items() if k in WalletMetrics.__dataclass_fields__})
        failed: list[str] = []
        reasons: list[str] = []

        # Layer 2 — Surface filter
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
            failed.append("tx_30d_requires_investigation")
        if metrics.token_diversity_30d < self.config.surface.min_token_diversity_30d:
            failed.append("token_diversity_too_low")
        if metrics.balance_native < self.config.surface.min_balance_native:
            failed.append("balance_too_low")
        if self.config.surface.require_cost and (metrics.cost_7d <= 0 or metrics.cost_30d <= 0):
            failed.append("zero_cost_anomaly")
        if metrics.profit_top_token_share >= self.config.surface.max_top_token_profit_share:
            failed.append("single_token_profit_dependency")

        if failed:
            return ScreeningResult(address, False, "surface_filter", 0.0, reasons, failed, metrics)

        # Layer 3–4 — realized performance and distribution
        if metrics.unrealized_pnl > metrics.realized_pnl_30d * 10:
            reasons.append("unrealized_dominant")

        buckets = metrics.profit_buckets
        total_bucket_trades = sum(buckets.values()) or 1
        lottery_share = buckets.get(">5x", 0) / total_bucket_trades
        if lottery_share > 0.25:
            reasons.append("lottery_dependent")
        else:
            reasons.append("healthy_profit_distribution")

        # Layer 6–7 — frequency and holding behavior
        transfer_ratio = metrics.transfer_in_count / max(metrics.trade_count_30d, 1)
        fast_ratio = metrics.buy_sell_under_10s / max(metrics.trade_count_30d, 1)
        if transfer_ratio > self.config.risk.max_transfer_in_ratio:
            failed.append("transfer_in_ratio_too_high")
        if fast_ratio > self.config.risk.max_buy_sell_under_10s_ratio:
            failed.append("ultra_short_trade_ratio_too_high")
        if metrics.hold_consistency < self.config.consistency.min_hold_consistency:
            failed.append("holding_behavior_inconsistent")

        # Layer 13 — risk
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

        cross = self.provider.get_cross_token_evidence(address)
        if cross.score < self.config.consistency.min_cross_token_score:
            failed.append("cross_token_consistency_weak")

        if metrics.early_actionable_rate < self.config.consistency.min_early_actionable_rate:
            failed.append("entry_not_actionable_enough")
        if metrics.current_conviction < self.config.consistency.min_current_conviction:
            failed.append("current_conviction_low")

        score = self._score(metrics, lottery_share, cross.score, transfer_ratio, fast_ratio)
        passed = not failed and score >= self.config.min_final_score
        stage = "final_watchlist" if passed else "deep_review"
        if passed:
            reasons.append("repeatable_edge_candidate")
        else:
            reasons.append("requires_manual_or_further_review")

        return ScreeningResult(address, passed, stage, score, reasons, failed, metrics)

    def _score(self, m: WalletMetrics, lottery_share: float, cross_token_score: float, transfer_ratio: float, fast_ratio: float) -> float:
        s = self.config.score
        def clamp(x: float) -> float:
            return max(0.0, min(1.0, x))

        realized = clamp((m.realized_pnl_30d / 100000.0))
        pnl_ratio = clamp(m.pnl_ratio / 2.0)
        wr = clamp((m.win_rate_7d + m.win_rate_30d) / 2)
        distribution = clamp(1.0 - lottery_share)
        diversity = clamp(m.token_diversity_30d / 10.0)
        holding = clamp(m.hold_consistency)
        entry = clamp(m.early_actionable_rate)
        conviction = clamp(m.current_conviction)
        funding = clamp(1.0 - min(1.0, transfer_ratio + fast_ratio + (m.common_funder_count > 0) * 0.25 + max(0, m.cluster_size - 1) * 0.1))
        actionability = clamp((m.early_actionable_rate + m.current_conviction) / 2 - m.crowding_score)
        return 10 * (
            realized * s.realized_performance_weight
            + pnl_ratio * s.pnl_ratio_weight
            + wr * s.win_rate_weight
            + distribution * s.profit_distribution_weight
            + diversity * s.token_diversity_weight
            + holding * s.holding_consistency_weight
            + entry * s.entry_timing_weight
            + conviction * s.current_conviction_weight
            + funding * s.funding_cleanliness_weight
            + cross_token_score * s.cross_token_weight
            + actionability * s.actionability_weight
        )

    def screen_many(self, addresses: list[str]) -> list[ScreeningResult]:
        return [self.screen(address) for address in addresses]

    @staticmethod
    def to_dict(result: ScreeningResult) -> dict:
        payload = {"address": result.address, "passed": result.passed, "stage": result.stage, "score": result.score, "reasons": result.reasons, "failed_rules": result.failed_rules}
        if result.metrics:
            payload["metrics"] = asdict(result.metrics)
        return payload
