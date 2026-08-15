from src.wallet_screener.gmgn_market_source import GMGNMarketSnapshotSource


def test_normalize_market_row():
    snapshot = GMGNMarketSnapshotSource._normalize({
        "address": "token-1",
        "price_usd": 1.5,
        "liquidity_usd": 10000,
        "timestamp": 123,
    })
    assert snapshot is not None
    assert snapshot.token == "token-1"
    assert snapshot.market_price_usd == 1.5
    assert snapshot.liquidity_usd == 10000


def test_normalize_rejects_missing_market_fields():
    assert GMGNMarketSnapshotSource._normalize({"address": "token-1"}) is None


def test_rows_extracts_common_payload_shapes():
    assert len(GMGNMarketSnapshotSource._rows({"data": {"items": [{"address": "x"}]}})) == 1
