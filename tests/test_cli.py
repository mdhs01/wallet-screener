from src.wallet_screener.cli import main


def test_health_command(tmp_path):
    assert main(["health", "--db", str(tmp_path / "db.sqlite")]) in {0, 1}


def test_validate_command(tmp_path, capsys):
    rc = main(["validate", "--db", str(tmp_path / "db.sqlite")])
    assert rc == 0
    assert "configuration_shell_ready" in capsys.readouterr().out


def test_once_command(tmp_path, capsys):
    rc = main(["once", "--db", str(tmp_path / "db.sqlite"), "--max-candidates", "10"])
    assert rc == 0
    assert "runtime_entrypoint_ready" in capsys.readouterr().out
