from __future__ import annotations

from src.wallet_screener.config import ScreenerConfig
from src.wallet_screener.models import WalletMetrics
from src.wallet_screener.surface_filter import evaluate_surface, frequency_tier


def metrics(**overrides):
    data = dict(
        address="wallet",
        win_rate_7d=0.60,
        win_rate_30d=0.60,
        realized_pnl_7d=1000,
        realized_pnl_30d=5000,
        total_cost_30d=10000,
        cost_7d=3000,
        cost_30d=10000,
        tx_7d=400,
        tx_30d=1000,
        token_diversity_30d=100,
        balance_native=1.0,
    )
    data.update(overrides)
    return WalletMetrics(**data)


def test_frequency_tiers():
    config = ScreenerConfig()
    assert frequency_tier(300, config) == "normal"
    assert frequency_tier(301, config) == "active"
    assert frequency_tier(500, config) == "active"
    assert frequency_tier(501, config) == "high_frequency"
    assert frequency_tier(750, config) == "high_frequency"
    assert frequency_tier(751, config) == "very_high_frequency"


def test_surface_prefilter_rejects_without_deep_data():
    config = ScreenerConfig()
    failed, warnings, reasons, tier = evaluate_surface(metrics(tx_7d=900), config)
    assert tier == "very_high_frequency"
    assert "tx_7d_too_high" in failed
    assert reasons == []


def test_surface_prefilter_allows_high_frequency():
    config = ScreenerConfig()
    failed, warnings, reasons, tier = evaluate_surface(metrics(tx_7d=700), config)
    assert failed == []
    assert tier == "high_frequency"
    assert "high_frequency_deep_screen_required" in warnings
    assert "transaction_frequency_high_frequency" in reasons


def test_calibrated_pnl_ratio_gate():
    config = ScreenerConfig()
    failed, _, _, _ = evaluate_surface(metrics(realized_pnl_30d=1500, total_cost_30d=10000), config)
    assert "pnl_ratio_below_min" in failed

    failed, _, _, _ = evaluate_surface(metrics(realized_pnl_30d=2500, total_cost_30d=10000), config)
    assert "pnl_ratio_below_min" not in failed
