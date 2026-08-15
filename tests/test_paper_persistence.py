from pathlib import Path

from src.wallet_screener.lifecycle import WalletLifecycle
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_tracking import PaperObservation
from src.wallet_screener.persistence import ScreeningStore


def observation(signal_ts: int = 1) -> PaperObservation:
    return PaperObservation(
        wallet="wallet-1",
        token="token-1",
        signal_ts=signal_ts,
        hypothetical_entry_ts=signal_ts + 60,
        hypothetical_entry_price=10.0,
        hypothetical_exit_price=12.0,
        actionable=True,
    )


def test_persistent_store_is_idempotent(tmp_path: Path):
    store = PaperObservationStore(tmp_path / "paper.db")
    item = observation()
    assert store.add(item, 100) is True
    assert store.add(item, 101) is False
    assert len(store.observations("wallet-1")) == 1


def test_lifecycle_reloads_paper_observations_after_restart(tmp_path: Path):
    db = tmp_path / "wallet.db"
    first = WalletLifecycle(store=ScreeningStore(db))
    item = observation()
    assert first.add_paper_observation(item) is True

    second = WalletLifecycle(store=ScreeningStore(db))
    result = second.evaluate_wallet(wallet="wallet-1", score=8.0, passed=True)
    assert result.paper_summary is not None
    assert result.paper_summary["observations"] == 1
