from __future__ import annotations

from .config import ScreenerConfig
from .models import WalletMetrics


def frequency_tier(tx_7d: int, config: ScreenerConfig) -> str:
    if tx_7d <= config.surface.normal_tx_7d_max:
        return "normal"
    if tx_7d <= config.surface.active_tx_7d_max:
        return "active"
    if tx_7d <= config.surface.max_tx_7d:
        return "high_frequency"
    return "very_high_frequency"


def evaluate_surface(metrics: WalletMetrics, config: ScreenerConfig) -> tuple[list[str], list[str], list[str], str]:
    """Evaluate only the cheap stats-based surface layer.

    This function deliberately does not call holdings, activity, cross-token,
    or funding providers. It is safe to run before expensive/deeper requests.
    """
    warnings: list[str] = []
    reasons: list[str] = []
    failed: list[str] = []

    if metrics.win_rate_7d < config.surface.min_win_rate_7d:
        failed.append("win_rate_7d_below_min")
    if metrics.win_rate_30d < config.surface.min_win_rate_30d:
        failed.append("win_rate_30d_below_min")
    if metrics.realized_pnl_7d < config.surface.min_realized_pnl_7d:
        failed.append("realized_pnl_7d_not_meaningful")
    if metrics.realized_pnl_30d < config.surface.min_realized_pnl_30d:
        failed.append("realized_pnl_30d_not_meaningful")
    if metrics.pnl_ratio < config.surface.min_pnl_ratio:
        failed.append("pnl_ratio_below_min")

    tier = frequency_tier(metrics.tx_7d, config)
    if tier == "active":
        warnings.append("high_frequency_active")
    elif tier == "high_frequency":
        warnings.append("high_frequency_deep_screen_required")
    elif tier == "very_high_frequency":
        failed.append("tx_7d_too_high")

    if metrics.tx_30d > config.surface.investigate_tx_30d:
        warnings.append("tx_30d_requires_investigation")
    if metrics.token_diversity_30d < config.surface.min_token_diversity_30d:
        failed.append("token_diversity_too_low")
    if metrics.balance_native < config.surface.min_balance_native:
        failed.append("balance_too_low")
    if config.surface.require_cost and (metrics.cost_7d <= 0 or metrics.cost_30d <= 0):
        failed.append("zero_cost_anomaly")
    if metrics.profit_top_token_share >= config.surface.max_top_token_profit_share:
        failed.append("single_token_profit_dependency")
    if (
        metrics.win_rate_7d >= config.surface.max_win_rate_for_investigation
        or metrics.win_rate_30d >= config.surface.max_win_rate_for_investigation
    ):
        warnings.append("extreme_win_rate_requires_investigation")

    if not failed:
        reasons.append(f"transaction_frequency_{tier}")

    return failed, warnings, reasons, tier
