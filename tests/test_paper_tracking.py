from src.wallet_screener.paper_tracking import PaperObservation, PaperTracker


def test_paper_tracker_calculates_metrics():
    tracker = PaperTracker(min_observations=3, min_actionable_rate=0.5, max_false_signal_rate=0.4, max_missed_rate=0.5)
    for i, ret in enumerate([10.0, -5.0, 15.0], start=1):
        tracker.add(
            PaperObservation(
                wallet="w1",
                token=f"T{i}",
                signal_ts=1000 * i,
                hypothetical_entry_ts=1000 * i + 120,
                hypothetical_entry_price=100.0,
                hypothetical_exit_price=100.0 * (1.0 + ret / 100.0),
                actionable=True,
                slippage_pct=0.5,
            )
        )

    summary = tracker.summarize("w1")
    assert summary.observations == 3
    assert summary.actionable_rate == 1.0
    assert summary.false_signal_rate == 0.0
    assert summary.missed_rate == 0.0
    assert summary.average_return_pct > 0
    assert summary.cumulative_return_pct > 0
    assert summary.average_latency_minutes == 2.0


def test_paper_tracker_flags_false_and_missed_signals():
    tracker = PaperTracker(min_observations=2, max_false_signal_rate=0.4, max_missed_rate=0.4)
    tracker.add(PaperObservation(wallet="w2", token="A", signal_ts=100, false_signal=True))
    tracker.add(PaperObservation(wallet="w2", token="B", signal_ts=200, missed=True))

    summary = tracker.summarize("w2")
    assert "false_signal_rate_high" in summary.warnings
    assert "missed_signal_rate_high" in summary.warnings
    assert summary.ready_for_watchlist is False


def test_export_contains_observations_and_summary():
    tracker = PaperTracker(min_observations=1)
    tracker.add(
        PaperObservation(
            wallet="w3",
            token="A",
            signal_ts=100,
            hypothetical_entry_price=10,
            hypothetical_exit_price=12,
            actionable=True,
        )
    )
    exported = tracker.export("w3")
    assert exported["summary"]["wallet"] == "w3"
    assert len(exported["observations"]) == 1
