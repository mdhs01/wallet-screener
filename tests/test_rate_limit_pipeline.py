from __future__ import annotations

from src.wallet_screener.config import ScreenerConfig
from src.wallet_screener.persistence import ScreeningStore
from src.wallet_screener.pipeline import ScreeningPipeline
from src.wallet_screener.providers import CrossTokenEvidence, WalletDataProvider


class CountingProvider(WalletDataProvider):
    def __init__(self):
        self.stats_calls = 0
        self.holdings_calls = 0
        self.activity_calls = 0

    def discover_wallets(self):
        return ["wallet-bad", "wallet-good"]

    def get_wallet_metrics(self, address):
        self.stats_calls += 1
        if address == "wallet-bad":
            return {
                "address": address,
                "win_rate_7d": 0.20,
                "win_rate_30d": 0.25,
                "realized_pnl_7d": -10,
                "realized_pnl_30d": 100,
                "total_cost_30d": 10000,
                "cost_7d": 1000,
                "cost_30d": 10000,
                "tx_7d": 100,
                "tx_30d": 500,
                "token_diversity_30d": 100,
                "balance_native": 1.0,
            }
        return {
            "address": address,
            "win_rate_7d": 0.60,
            "win_rate_30d": 0.60,
            "realized_pnl_7d": 1000,
            "realized_pnl_30d": 5000,
            "total_cost_30d": 10000,
            "cost_7d": 3000,
            "cost_30d": 10000,
            "tx_7d": 100,
            "tx_30d": 500,
            "token_diversity_30d": 100,
            "balance_native": 1.0,
            "hold_consistency": 0.8,
        }

    def get_current_holdings(self, address):
        self.holdings_calls += 1
        return []

    def get_trade_sample(self, address, limit=20):
        self.activity_calls += 1
        return []

    def get_cross_token_evidence(self, address):
        return CrossTokenEvidence(
            runner_tokens=["A", "B", "C", "D"],
            repeated_early=4,
            repeated_profitable=4,
            shared_holdings_hits=3,
            earliest_bought_hits=3,
        )

    def get_funding_cluster(self, address):
        return {"common_funder_count": 0, "cluster_size": 1, "independence_score": 1.0}


def test_pipeline_does_not_deep_query_surface_rejections(tmp_path):
    provider = CountingProvider()
    report = ScreeningPipeline(provider, config=ScreenerConfig(), store=ScreeningStore(tmp_path / "db.sqlite")).run()

    assert report.discovered == 2
    assert report.surface_rejected == 1
    assert report.deep_screened == 1
    assert provider.stats_calls == 2
    assert provider.holdings_calls == 1
    assert provider.activity_calls == 1
