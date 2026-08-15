from src.wallet_screener.live_paper_session import LivePaperSession
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperTracker
from src.wallet_screener.paper_tracking import PaperObservation


def _observation(ts):
    return PaperObservation(
        wallet="wallet-session",
        token="token-session",
        signal_ts=ts,
        wallet_entry_ts=ts,
        wallet_exit_ts=None,
        hypothetical_entry_ts=ts,
        hypothetical_exit_ts=None,
        entry_price_usd=1.0,
        exit_price_usd=None,
        actionable=True,
        false_signal=False,
        missed_signal=False,
        slippage_pct=0.0,
        hypothetical_return_pct=2.0,
        max_drawdown_pct=1.0,
        latency_ms=100.0,
    )


def test_live_paper_session_ingests_idempotently(tmp_path):
    store = PaperObservationStore(tmp_path / "paper.sqlite")
    runtime = PersistentPaperRuntime(store, PaperTracker())
    session = LivePaperSession(store, runtime)

    first = session.ingest([_observation(100)])
    second = session.ingest([_observation(100)])
    ready = session.readiness(now_ts=100 + 3 * 86400)

    assert first.observations_seen == 1
    assert first.observations_accepted == 1
    assert second.duplicates == 1
    assert ready["observations"] == 1
    assert ready["minimum_days_met"] is True
    assert ready["maximum_days_reached"] is False
