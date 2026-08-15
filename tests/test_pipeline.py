from __future__ import annotations

from pathlib import Path

from src.wallet_screener.models import WalletMetrics
from src.wallet_screener.persistence import ScreeningStore
from src.wallet_screener.pipeline import ScreeningPipeline
from src.wallet_screener.providers import CrossTokenEvidence, WalletDataProvider


class FixtureProvider(WalletDataProvider):
    def discover_wallets(self):
        return ["wallet-a", "wallet-b", "wallet-a"]

    def get_wallet_metrics(self, address):
        return {
            "address": address,
            "win_rate_7d": 0.6,
            "win_rate_30d": 0.58,
            "realized_pnl_7d": 1000,
            "realized_pnl_30d": 5000,
            "unrealized_pnl": 500,
            "total_cost_30d": 2500,
            "tx_7d": 100,
            "tx_30d": 700,
            "token_diversity_30d": 18,
            "balance_native": 1.0,
            "cost_7d": 1000,
            "cost_30d": 2500,
            "trade_count_30d": 54,
            "profit_buckets": {"<-50%": 2, "-50%–0%": 8, "0–2x": 30, "2–5x": 12, ">5x": 2},
            "hold_consistency": 0.8,
            "profit_top_token_share": 0.3,
            "profit_top_two_token_share": 0.45,
            "early_actionable_rate": 0.75,
            "current_conviction": 0.75,
            "style_match_score": 0.8,
            "daily_profit_series": [12, 9, 15, 11, 8, 13, 10],
            "recent_profit_stability": 0.6,
        }

    def get_current_holdings(self, address):
        return []

    def get_trade_sample(self, address, limit=20):
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


def test_pipeline_deduplicates_and_persists(tmp_path: Path):
    store = ScreeningStore(tmp_path / "screen.db")
    report = ScreeningPipeline(FixtureProvider(), store=store).run()

    assert report.status == "completed"
    assert report.discovered == 2
    assert report.screened == 2
    latest = store.latest_results(limit=10)
    assert len(latest) == 2
    assert {item["address"] for item in latest} == {"wallet-a", "wallet-b"}


def test_pipeline_candidate_limit(tmp_path: Path):
    store = ScreeningStore(tmp_path / "screen.db")
    report = ScreeningPipeline(FixtureProvider(), store=store).run(max_candidates=1)

    assert report.discovered == 1
    assert report.screened == 1
