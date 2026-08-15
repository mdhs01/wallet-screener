from src.wallet_screener.market_observation import MarketObservationAdapter, MarketSnapshot


def test_market_snapshot_converts_to_paper_observation():
    adapter = MarketObservationAdapter(default_position_usd=125.0)
    snapshot = MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=2.0,
        liquidity_usd=50_000,
        actionable=True,
        slippage_pct=0.5,
        notes="signal",
    )
    observation = adapter.to_paper_observation(snapshot, exit_price_usd=2.5, exit_ts=160)
    assert observation.wallet == "wallet-1"
    assert observation.hypothetical_entry_price == 2.0
    assert observation.hypothetical_exit_price == 2.5
    assert observation.hypothetical_position_usd == 125.0
    assert observation.actionable is True


def test_invalid_market_price_is_rejected():
    adapter = MarketObservationAdapter()
    snapshot = MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=0,
        liquidity_usd=10_000,
    )
    try:
        adapter.to_paper_observation(snapshot)
    except ValueError as exc:
        assert "market_price_usd" in str(exc)
    else:
        raise AssertionError("Expected invalid market price to fail")
