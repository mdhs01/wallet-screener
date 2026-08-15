from src.wallet_screener.paper_tracking import PaperTrackSummary
from src.wallet_screener.watchlist import (
    RevalidationSnapshot,
    WatchlistCategory,
    WatchlistManager,
    WatchlistStatus,
    classify_category,
)


def test_classify_swing_wallet():
    assert classify_category(
        style=None,
        early_actionable_rate=0.55,
        avg_hold_minutes=360,
        current_conviction=0.50,
    ) == WatchlistCategory.SWING


def test_watchlist_capacity_demotes_low_ranked_active_wallets():
    manager = WatchlistManager(max_size=2)
    for idx, score in enumerate([9.0, 8.0, 7.5]):
        manager.upsert(
            wallet=f"w{idx}",
            score=score,
            timestamp=idx,
            category=WatchlistCategory.SWING,
            passed=True,
        )
    active = manager.enforce_capacity()
    assert [item.wallet for item in active] == ["w0", "w1"]
    assert manager._entries["w2"].status == WatchlistStatus.REVIEW


def test_revalidation_detects_decay_and_drops_wallet():
    manager = WatchlistManager(max_edge_decay_score=0.20, drop_below_score=5.0)
    manager.revalidate(
        timestamp=1,
        wallet="wallet-a",
        snapshot=RevalidationSnapshot(
            timestamp=1,
            score=9.0,
            realized_pnl_7d=1000,
            realized_pnl_30d=10000,
            win_rate_7d=0.60,
            win_rate_30d=0.60,
            actionability_score=0.80,
            current_conviction=0.80,
        ),
    )
    entry = manager.revalidate(
        timestamp=2,
        wallet="wallet-a",
        snapshot=RevalidationSnapshot(
            timestamp=2,
            score=5.5,
            realized_pnl_7d=100,
            realized_pnl_30d=2000,
            win_rate_7d=0.40,
            win_rate_30d=0.45,
            actionability_score=0.20,
            current_conviction=0.20,
        ),
    )
    assert entry.status == WatchlistStatus.DROPPED
    assert entry.edge_decay_score > 0.20


def test_paper_readiness_can_gate_watchlist_activation():
    manager = WatchlistManager(max_size=5)
    summary = PaperTrackSummary(wallet="wallet-a", observations=5, actionable_rate=0.6, ready_for_watchlist=False)
    entry = manager.upsert(
        wallet="wallet-a",
        score=8.0,
        timestamp=1,
        category=WatchlistCategory.EARLY_RUNNER,
        passed=True,
        paper_summary=summary,
    )
    assert entry.status == WatchlistStatus.REVIEW
