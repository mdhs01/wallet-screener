from src.wallet_screener.gmgn_cli import GmgnCli, GmgnCliConfig
from src.wallet_screener.gmgn_provider import GMGNLiveProvider


class FakeCli(GmgnCli):
    def __init__(self):
        super().__init__(GmgnCliConfig(binary="fake", chain="sol"))

    def portfolio_stats(self, wallet, period):
        common = {
            "follow_count": 12,
            "created_token_count": 0,
            "fund_from_address": "funding-wallet",
        }
        return {"data": {"winrate": 0.60 if period == "7d" else 0.58,
                           "realized_profit": 1000 if period == "7d" else 5000,
                           "unrealized_profit": 500,
                           "total_cost": 2500,
                           "buy_count": 20 if period == "7d" else 80,
                           "sell_count": 15 if period == "7d" else 60,
                           "token_num": 15,
                           "common": common}}

    def track_smartmoney(self, limit=100):
        return {"data": {"trades": [
            {"wallet_address": "w1"},
            {"wallet_address": "w2"},
            {"wallet_address": "w1"},
        ]}}

    def portfolio_holdings(self, wallet, limit=50):
        return {"data": {"holdings": [{
            "token": {"address": "token-a", "symbol": "AAA"},
            "usd_value": 500,
            "cost": 300,
            "unrealized_profit": 200,
            "sell_tx_count": 1,
        }]}}

    def portfolio_activity(self, wallet, limit=50):
        return {"data": {"activities": [{
            "type": "buy",
            "token": {"address": "token-a"},
            "timestamp": 1000,
            "cost_usd": 300,
        }, {
            "type": "transferIn",
            "token": {"address": "token-b"},
            "timestamp": 1100,
            "cost_usd": 0,
        }]}}


def test_discovery_deduplicates_wallets():
    provider = GMGNLiveProvider(FakeCli())
    assert provider.discover_wallets() == ["w1", "w2"]


def test_metrics_maps_documented_stats_fields():
    provider = GMGNLiveProvider(FakeCli())
    metrics = provider.get_wallet_metrics("w1")
    assert metrics["realized_pnl_7d"] == 1000
    assert metrics["realized_pnl_30d"] == 5000
    assert metrics["win_rate_7d"] == 0.60
    assert metrics["token_diversity_30d"] == 15


def test_activity_marks_transfer_in():
    provider = GMGNLiveProvider(FakeCli())
    trades = provider.get_trade_sample("w1", 20)
    assert any(t["transfer_in"] for t in trades)


def test_unsupported_layers_are_not_fabricated():
    provider = GMGNLiveProvider(FakeCli())
    assert provider.get_cross_token_evidence("w1").score == 0.0
    assert provider.get_funding_cluster("w1")["independence_score"] == 0.0
