from __future__ import annotations

import json
import subprocess

import pytest

from src.wallet_screener.gmgn_cli import GmgnCli, GmgnCliConfig, GmgnCliError


def test_cli_caches_identical_read_only_request(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, json.dumps({"ok": True}), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    cli = GmgnCli(GmgnCliConfig(min_request_interval_seconds=0, cache_ttl_seconds=30))

    assert cli.run("portfolio", "stats", "--wallet", "wallet-1") == {"ok": True}
    assert cli.run("portfolio", "stats", "--wallet", "wallet-1") == {"ok": True}
    assert len(calls) == 1


def test_cli_opens_circuit_on_rate_limit(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            1,
            "",
            "HTTP 429 RATE_LIMIT_BANNED Rate limit resets at 2026-08-16 19:42:03 GMT+00:00 (~73s remaining)",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    cli = GmgnCli(GmgnCliConfig(min_request_interval_seconds=0, cache_ttl_seconds=0))

    with pytest.raises(GmgnCliError, match="429"):
        cli.run("portfolio", "stats", "--wallet", "wallet-1")

    with pytest.raises(GmgnCliError, match="circuit open"):
        cli.run("portfolio", "stats", "--wallet", "wallet-2")

    assert len(calls) == 1
