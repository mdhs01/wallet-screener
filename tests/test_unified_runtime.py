from src.wallet_screener.lifecycle import WalletLifecycle
from src.wallet_screener.market_feed import InMemoryMarketSource, LiveMarketFeed
from src.wallet_screener.market_observation import MarketSnapshot
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.pipeline import ScreeningPipeline
from src.wallet_screener.providers import NullProvider
from src.wallet_screener.persistence import ScreeningStore
from src.wallet_screener.unified_runtime import UnifiedRuntimeJob


def test_unified_runtime_runs_one_cycle(tmp_path):
    store = ScreeningStore(tmp_path / "db.sqlite")
    lifecycle = WalletLifecycle(store=store)
    paper_store = PaperObservationStore(store.path)
    runtime = PersistentPaperRuntime(lifecycle=lifecycle, store=paper_store)
    snapshot = MarketSnapshot(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        market_price_usd=1.0,
        liquidity_usd=10000,
        actionable=True,
    )
    feed = LiveMarketFeed(InMemoryMarketSource([snapshot]), runtime)
    job = UnifiedRuntimeJob(
        screening_pipeline=ScreeningPipeline(NullProvider(), store=store),
        market_feed=feed,
        lifecycle=lifecycle,
    )

    report = job.run_once()

    assert report.screening_run_id is not None
    assert report.market_fetched == 1
    assert report.market_accepted == 1
