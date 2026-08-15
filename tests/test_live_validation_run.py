from src.wallet_screener.live_validation_run import LiveValidationRunner


def test_live_validation_runner_persists_report(tmp_path):
    output = tmp_path / "live-report.json"
    runner = LiveValidationRunner(
        {
            "cli_available": lambda: True,
            "wallet_discovery": lambda: True,
            "market_source": lambda: True,
        }
    )

    result = runner.run(output)

    assert result.report.passed is True
    assert result.output_path == output
    assert output.exists()
    assert '"passed": true' in output.read_text(encoding="utf-8")


def test_live_validation_runner_records_failed_check(tmp_path):
    runner = LiveValidationRunner({"gmgn_api": lambda: False})

    result = runner.run()

    assert result.report.passed is False
    assert len(result.report.failed) == 1
    assert result.report.failed[0].name == "gmgn_api"
