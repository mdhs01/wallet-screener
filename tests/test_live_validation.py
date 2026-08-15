from src.wallet_screener.live_validation import validate_gmgn_provider


class FakeProvider:
    capabilities = {"discovery": True}

    def discover_wallets(self):
        return ["wallet-1"]

    def get_wallet_metrics(self, address):
        return {"address": address}

    def get_current_holdings(self, address):
        return []

    def get_trade_sample(self, address, limit=20):
        return []


def test_live_validation_ready_with_provider_data():
    report = validate_gmgn_provider(FakeProvider())
    assert report.ready is True
    assert report.live is True
    assert report.failed_checks == 0


class EmptyProvider(FakeProvider):
    def discover_wallets(self):
        return []


def test_live_validation_does_not_claim_live_readiness_on_empty_discovery():
    report = validate_gmgn_provider(EmptyProvider())
    assert report.ready is False
    assert report.live is False
