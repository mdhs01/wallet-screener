from src.wallet_screener.live_paper_session import LivePaperSession
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperTracker, PaperObservation


def _observation(ts):
    return PaperObservation(
        wallet="wallet-session",
        token="token-session",
        signal_ts=ts,
        wallet_entry_ts=ts,
        wallet_exit_ts=None,
        hypothetical_entry_ts=ts,
        hypothetical_exit_ts=ts + 60,
        wallet_entry_price=1.0,
        wallet_exit_price=1.02,
        hypothetical_entry_price=1.0,
        hypothetical_exit_price=1.02,
        liquidity_at_signal_usd=100_000,
        hypothetical_position_usd=100,
        slippage_pct=0.0,
        actionable=True,
        false_signal=False,
        missed=False,
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
