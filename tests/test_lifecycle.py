from src.wallet_screener.lifecycle import WalletLifecycle
from src.wallet_screener.paper_tracking import PaperObservation
from src.wallet_screener.watchlist import WatchlistStatus


def make_observation(i: int) -> PaperObservation:
    return PaperObservation(
        wallet="wallet-1",
        token=f"token-{i}",
        signal_ts=1_000 + i,
        hypothetical_entry_ts=1_001 + i,
        hypothetical_exit_ts=1_061 + i,
        hypothetical_entry_price=1.0,
        hypothetical_exit_price=1.02,
        liquidity_at_signal_usd=100_000,
        hypothetical_position_usd=100,
        slippage_pct=0.2,
        actionable=True,
    )


def test_lifecycle_blocks_watchlist_until_paper_ready():
    lifecycle = WalletLifecycle()
    result = lifecycle.evaluate_wallet(
        wallet="wallet-1",
        score=8.5,
        passed=True,
    )
    assert result.status == WatchlistStatus.REVIEW.value
    assert result.paper_summary["ready_for_watchlist"] is False


def test_lifecycle_can_promote_after_paper_tracking():
    lifecycle = WalletLifecycle()
    for i in range(10):
        lifecycle.add_paper_observation(make_observation(i))

    result = lifecycle.evaluate_wallet(
        wallet="wallet-1",
        score=8.5,
        passed=True,
    )
    assert result.paper_summary["ready_for_watchlist"] is True
    assert result.status == WatchlistStatus.ACTIVE.value
