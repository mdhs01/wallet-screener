import pytest

from src.wallet_screener.health import check_health
from src.wallet_screener.operational import CircuitBreaker, RetryPolicy, with_retry


def test_retry_eventually_succeeds():
    calls = {"n": 0}

    def op():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    assert with_retry(op, policy=RetryPolicy(retries=3, backoff_seconds=0)) == "ok"
    assert calls["n"] == 3


def test_retry_raises_after_exhaustion():
    with pytest.raises(RuntimeError):
        with_retry(lambda: (_ for _ in ()).throw(RuntimeError("x")), policy=RetryPolicy(retries=1, backoff_seconds=0))


def test_circuit_breaker_opens():
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    assert breaker.allow() is True
    breaker.record_failure()
    assert breaker.allow() is True
    breaker.record_failure()
    assert breaker.allow() is False
    breaker.record_success()
    assert breaker.allow() is True


def test_health_reports_degraded_without_api(tmp_path):
    report = check_health(tmp_path / "db.sqlite", api_configured=False)
    assert report.database_ok is True
    assert report.status == "degraded"


def test_health_reports_healthy_with_api(tmp_path):
    report = check_health(tmp_path / "db.sqlite", api_configured=True)
    assert report.database_ok is True
    assert report.status == "healthy"
