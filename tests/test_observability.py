import logging

from src.wallet_screener.observability import Observability, RuntimeMetrics, configure_logging


def test_metrics_counters_and_snapshot():
    metrics = RuntimeMetrics()
    metrics.inc("cycles", 2)
    metrics.set_gauge("passed", 3)
    metrics.observe_ms("runtime", 10)
    metrics.observe_ms("runtime", 20)

    snapshot = metrics.snapshot()
    assert snapshot["counters"]["cycles"] == 2
    assert snapshot["gauges"]["passed"] == 3.0
    assert snapshot["timings_ms"]["runtime"]["count"] == 2
    assert snapshot["timings_ms"]["runtime"]["avg"] == 15


def test_observability_records_runtime_and_market():
    obs = Observability()
    obs.record_cycle(success=True, duration_ms=25, discovered=10, passed=2)
    obs.record_market(fetched=5, accepted=3, duplicates=1, rejected=1, errors=0)

    snapshot = obs.metrics.snapshot()
    assert snapshot["counters"]["runtime_cycles_total"] == 1
    assert snapshot["counters"]["runtime_cycles_success_total"] == 1
    assert snapshot["counters"]["market_snapshots_fetched_total"] == 5
    assert snapshot["counters"]["paper_observations_accepted_total"] == 3


def test_configure_logging_adds_json_handler():
    logger = logging.getLogger()
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    configure_logging("INFO")
    assert logger.handlers
