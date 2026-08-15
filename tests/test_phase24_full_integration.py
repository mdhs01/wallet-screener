from src.wallet_screener.lifecycle import WalletLifecycle
from src.wallet_screener.market_feed import InMemoryMarketSource, LiveMarketFeed
from src.wallet_screener.market_observation import MarketSnapshot
from src.wallet_screener.observability import Observability, RuntimeMetrics
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperTracker
from src.wallet_screener.persistence import ScreeningStore
from src.wallet_screener.pipeline import ScreeningPipeline
from src.wallet_screener.providers import NullProvider
from src.wallet_screener.unified_runtime import UnifiedRuntimeJob


def _build_runtime(tmp_path, snapshots):
    store = ScreeningStore(tmp_path / "integration.sqlite")
    paper_store = PaperObservationStore(store.path)
    paper_runtime = PersistentPaperRuntime(paper_store, PaperTracker())
    feed = LiveMarketFeed(InMemoryMarketSource(snapshots), paper_runtime)
    lifecycle = WalletLifecycle(store=store)
    metrics = RuntimeMetrics()
    observability = Observability(metrics=metrics, logger_name="wallet_screener.integration")
    job = UnifiedRuntimeJob(
        screening_pipeline=ScreeningPipeline(NullProvider(), store=store),
        market_feed=feed,
        lifecycle=lifecycle,
        observability=observability,
    )
    return job, metrics


def test_full_runtime_cycle_persists_market_observation_and_metrics(tmp_path):
    snapshot = MarketSnapshot(
        wallet="wallet-integration",
        token="token-integration",
        signal_ts=1_700_000_000,
        market_price_usd=1.0,
        liquidity_usd=50_000,
        actionable=True,
    )
    job, metrics = _build_runtime(tmp_path, [snapshot])

    report = job.run_once()
    observed = metrics.snapshot()

    assert report.screening_run_id is not None
    assert report.market_fetched == 1
    assert report.market_accepted == 1
    assert report.market_duplicates == 0
    assert report.errors == []
    assert observed["counters"]["runtime_cycles_total"] == 1
    assert observed["counters"]["runtime_cycles_success_total"] == 1
    assert observed["counters"]["market_snapshots_fetched_total"] == 1
    assert observed["counters"]["paper_observations_accepted_total"] == 1
    assert observed["timings_ms"]["runtime_cycle"]["count"] == 1


def test_full_runtime_duplicate_cycle_is_idempotent(tmp_path):
    snapshot = MarketSnapshot(
        wallet="wallet-duplicate",
        token="token-duplicate",
        signal_ts=1_700_000_001,
        market_price_usd=2.0,
        liquidity_usd=75_000,
        actionable=True,
    )
    job, metrics = _build_runtime(tmp_path, [snapshot])

    first = job.run_once()
    second = job.run_once()
    observed = metrics.snapshot()

    assert first.market_accepted == 1
    assert second.market_accepted == 0
    assert second.market_duplicates == 1
    assert observed["counters"]["runtime_cycles_total"] == 2
    assert observed["counters"]["paper_observations_accepted_total"] == 1
    assert observed["counters"]["paper_observations_duplicate_total"] == 1
