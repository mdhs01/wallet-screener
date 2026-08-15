from src.wallet_screener.market_feed import InMemoryMarketSource, LiveMarketFeed
from src.wallet_screener.market_observation import MarketSnapshot
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperTracker
from src.wallet_screener.persistence import ScreeningStore


def _runtime(tmp_path):
    store = ScreeningStore(tmp_path / "db.sqlite")
    paper_store = PaperObservationStore(store.path)
    return PersistentPaperRuntime(paper_store, PaperTracker())


def _snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=1.0,
        liquidity_usd=10000,
        wallet_entry_ts=101,
        wallet_entry_price_usd=1.0,
        wallet_exit_ts=110,
        wallet_exit_price_usd=1.1,
        actionable=True,
    )


def test_feed_accepts_snapshot_and_deduplicates(tmp_path):
    runtime = _runtime(tmp_path)
    feed = LiveMarketFeed(InMemoryMarketSource([_snapshot()]), runtime)

    first = feed.cycle()
    second = feed.cycle()

    assert first.accepted == 1
    assert second.duplicates == 1


def test_feed_rejects_invalid_snapshot(tmp_path):
    snapshot = MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=0.0,
        liquidity_usd=10000,
    )
    runtime = _runtime(tmp_path)
    feed = LiveMarketFeed(InMemoryMarketSource([snapshot]), runtime)
    report = feed.cycle()
    assert report.rejected == 1


def test_polling_cycles(tmp_path):
    runtime = _runtime(tmp_path)
    feed = LiveMarketFeed(InMemoryMarketSource([_snapshot()]), runtime)
    reports = feed.run_polling(interval_seconds=0.001, cycles=2)
    assert len(reports) == 2
    assert reports[0].accepted == 1
    assert reports[1].duplicates == 1
