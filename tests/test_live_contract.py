from src.wallet_screener.live_contract import LiveContractValidator


def test_live_contract_all_checks_pass():
    report = LiveContractValidator({"discovery": lambda: ["wallet"], "metrics": lambda: True}).run()
    assert report.passed is True
    assert report.failed == []


def test_live_contract_failure_is_explicit():
    def fail():
        raise RuntimeError("provider unavailable")

    report = LiveContractValidator({"discovery": fail, "metrics": lambda: True}).run()
    assert report.passed is False
    assert report.failed[0].name == "discovery"
    assert "provider unavailable" in report.failed[0].detail
