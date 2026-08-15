from src.wallet_screener.scheduled_unified_runtime import ScheduledUnifiedRuntime
from src.wallet_screener.unified_runtime import UnifiedRuntimeReport


class FakeJob:
    def __init__(self):
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return UnifiedRuntimeReport(
            started_ts=100,
            finished_ts=101,
            screening_run_id=self.calls,
            discovered=2,
            screened=2,
            passed=1,
        )


def test_scheduled_unified_runtime_runs_bounded_cycles():
    job = FakeJob()
    runtime = ScheduledUnifiedRuntime(job)
    report = runtime.run(interval_seconds=0, cycles=3)

    assert report.scheduler.cycles == 3
    assert report.scheduler.succeeded == 3
    assert report.successful_cycles == 3
    assert len(report.cycles) == 3
    assert job.calls == 3


def test_scheduled_unified_runtime_serializes_report():
    job = FakeJob()
    report = ScheduledUnifiedRuntime(job).run(interval_seconds=0, cycles=1)
    payload = report.to_dict()

    assert payload["successful_cycles"] == 1
    assert payload["cycles"][0]["screening_run_id"] == 1
