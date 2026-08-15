from pathlib import Path

from src.wallet_screener.lifecycle import WalletLifecycle
from src.wallet_screener.paper_persistence import PaperObservationStore
from src.wallet_screener.paper_runtime import PersistentPaperRuntime
from src.wallet_screener.paper_tracking import PaperObservation
from src.wallet_screener.persistence import ScreeningStore


def test_runtime_persists_and_deduplicates(tmp_path: Path):
    db = tmp_path / "runtime.db"
    lifecycle = WalletLifecycle(store=ScreeningStore(db))
    runtime = PersistentPaperRuntime(
        lifecycle=lifecycle,
        store=PaperObservationStore(db),
    )
    item = PaperObservation(
        wallet="wallet-1",
        token="token-1",
        signal_ts=100,
        hypothetical_entry_ts=160,
        hypothetical_entry_price=10,
        hypothetical_exit_price=11,
        actionable=True,
    )
    first = runtime.ingest_observations([item])
    second = runtime.ingest_observations([item])
    assert first.inserted == 1
    assert second.inserted == 0
    assert second.duplicates == 1
