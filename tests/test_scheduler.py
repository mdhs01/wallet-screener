from src.wallet_screener.scheduler import ScheduledRuntime, SingletonLock


def test_scheduler_runs_bounded_cycles():
    calls = []
    runtime = ScheduledRuntime(lambda: calls.append(1))
    report = runtime.run(interval_seconds=0, cycles=3)
    assert report.cycles == 3
    assert report.succeeded == 3
    assert len(calls) == 3


def test_singleton_lock_skips_second_runtime():
    lock = SingletonLock()
    first = ScheduledRuntime(lambda: None, lock=lock)
    second = ScheduledRuntime(lambda: None, lock=lock)
    assert lock.acquire() is True
    try:
        report = second.run(interval_seconds=0, cycles=1)
        assert report.skipped_locked == 1
    finally:
        lock.release()
    assert first.run(interval_seconds=0, cycles=1).succeeded == 1


def test_scheduler_stops():
    holder = {}
    calls = []

    def job():
        calls.append(1)
        holder["runtime"].stop()

    runtime = ScheduledRuntime(job)
    holder["runtime"] = runtime
    report = runtime.run(interval_seconds=0, cycles=None)
    assert report.stopped is True
    assert report.cycles == 1
