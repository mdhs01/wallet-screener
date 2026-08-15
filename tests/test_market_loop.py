from src.wallet_screener.market_feed import InMemoryMarketSource, LiveMarketFeed
from src.wallet_screener.market_loop import LiveMarketLoop
from src.wallet_screener.market_observation import MarketSnapshot
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperTracker
from src.wallet_screener.persistence import ScreeningStore


def _runtime(tmp_path):
    store = ScreeningStore(tmp_path / "db.sqlite")
    paper_store = PaperObservationStore(store.path)
    return PersistentPaperRuntime(paper_store, PaperTracker())


def test_bounded_live_market_loop(tmp_path):
    snapshot = MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=1.0,
        liquidity_usd=10000,
        wallet_entry_ts=101,
        wallet_entry_price_usd=1.0,
        actionable=True,
    )
    runtime = _runtime(tmp_path)
    feed = LiveMarketFeed(InMemoryMarketSource([snapshot]), runtime)
    report = LiveMarketLoop(feed).run(interval_seconds=0.001, cycles=2)
    assert report.cycles == 2
    assert report.accepted == 1
    assert report.duplicates == 1


def test_loop_requires_positive_cycles(tmp_path):
    runtime = _runtime(tmp_path)
    feed = LiveMarketFeed(InMemoryMarketSource([]), runtime)
    try:
        LiveMarketLoop(feed).run(interval_seconds=0.001, cycles=0)
    except ValueError as exc:
        assert "cycles must be > 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
