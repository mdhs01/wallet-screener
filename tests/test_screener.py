from src.wallet_screener import ScreenerConfig, WalletScreener
from src.wallet_screener.models import WalletMetrics
from src.wallet_screener.providers import CrossTokenEvidence, WalletDataProvider


class FixtureProvider(WalletDataProvider):
    def __init__(self, metrics: WalletMetrics, cross: CrossTokenEvidence | None = None, holdings=None, trades=None, funding=None):
        self.metrics = metrics
        self.cross = cross or CrossTokenEvidence(
            runner_tokens=["A", "B", "C", "D"],
            repeated_early=4,
            repeated_profitable=4,
            shared_holdings_hits=3,
            earliest_bought_hits=3,
        )
        self.holdings = holdings or []
        self.trades = trades or []
        self.funding = funding or {"common_funder_count": metrics.common_funder_count, "cluster_size": metrics.cluster_size}

    def discover_wallets(self):
        return [self.metrics.address]

    def get_wallet_metrics(self, address):
        from dataclasses import asdict
        return asdict(self.metrics)

    def get_current_holdings(self, address):
        return self.holdings

    def get_trade_sample(self, address, limit=20):
        return self.trades[:limit]

    def get_cross_token_evidence(self, address):
        return self.cross

    def get_funding_cluster(self, address):
        return self.funding


def good_metrics():
    return WalletMetrics(
        address="wallet-good",
        win_rate_7d=0.60,
        win_rate_30d=0.58,
        realized_pnl_7d=1000,
        realized_pnl_30d=5000,
        unrealized_pnl=500,
        total_cost_30d=2500,
        tx_7d=100,
        tx_30d=700,
        token_diversity_30d=18,
        balance_native=1.0,
        cost_7d=1000,
        cost_30d=2500,
        avg_realized_profit=250,
        avg_token_cost=140,
        profit_buckets={"<-50%": 2, "-50%–0%": 8, "0–2x": 30, "2–5x": 12, ">5x": 2},
        avg_hold_minutes=360,
        winner_hold_minutes=500,
        loser_hold_minutes=120,
        hold_consistency=0.80,
        transfer_in_count=2,
        trade_count_30d=54,
        blacklist_count=0,
        honeypot_count=0,
        rug_count=0,
        buy_sell_under_10s=1,
        sold_more_than_bought=0,
        did_not_buy_count=0,
        common_funder_count=0,
        cluster_size=1,
        profit_top_token_share=0.30,
        profit_top_two_token_share=0.45,
        early_actionable_rate=0.75,
        current_conviction=0.75,
        crowding_score=0.0,
        style_match_score=0.80,
        daily_profit_series=[12, 9, 15, 11, 8, 13, 10],
        recent_profit_stability=0.60,
    )


def test_good_wallet_passes_deep_pipeline():
    screener = WalletScreener(FixtureProvider(good_metrics()), ScreenerConfig())
    result = screener.screen("wallet-good")
    assert result.passed is True
    assert result.stage == "final_watchlist"
    assert result.score >= 7.0
    assert "cross_token" in result.layer_scores
    assert "actionability" in result.layer_scores


def test_low_win_rate_is_rejected_at_surface():
    metrics = good_metrics()
    metrics.win_rate_7d = 0.20
    screener = WalletScreener(FixtureProvider(metrics), ScreenerConfig())
    result = screener.screen(metrics.address)
    assert result.passed is False
    assert "win_rate_7d_below_min" in result.failed_rules
    assert result.stage == "surface_filter"


def test_cluster_risk_is_rejected():
    metrics = good_metrics()
    metrics.cluster_size = 10
    screener = WalletScreener(FixtureProvider(metrics), ScreenerConfig())
    result = screener.screen(metrics.address)
    assert result.passed is False
    assert "cluster_too_large" in result.failed_rules


def test_lottery_dependency_is_warning_not_automatic_surface_rejection():
    metrics = good_metrics()
    metrics.profit_buckets = {"<-50%": 1, "-50%–0%": 1, "0–2x": 2, "2–5x": 1, ">5x": 10}
    result = WalletScreener(FixtureProvider(metrics), ScreenerConfig()).screen(metrics.address)
    assert "lottery_dependency" in result.warnings
    assert result.stage in {"deep_review", "final_watchlist"}


def test_current_holdings_can_reduce_conviction():
    metrics = good_metrics()
    holdings = [
        {"token": "A", "current_value": 100, "original_value": 1000, "unrealized_pnl": -900},
        {"token": "B", "current_value": 50, "original_value": 1000, "unrealized_pnl": -950},
    ]
    result = WalletScreener(FixtureProvider(metrics, holdings=holdings), ScreenerConfig()).screen(metrics.address)
    assert result.metrics is not None
    assert result.metrics.current_conviction < 0.30
    assert "current_conviction_low" in result.failed_rules


def test_style_change_is_a_warning():
    metrics = good_metrics()
    metrics.style_change_score = 0.90
    result = WalletScreener(FixtureProvider(metrics), ScreenerConfig()).screen(metrics.address)
    assert "style_change_detected" in result.warnings
