from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any


class GmgnCliError(RuntimeError):
    pass


@dataclass(slots=True)
class GmgnCliConfig:
    binary: str = "gmgn-cli"
    chain: str = "sol"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "GmgnCliConfig":
        return cls(
            binary=os.getenv("GMGN_CLI_PATH", "gmgn-cli"),
            chain=os.getenv("GMGN_CHAIN", "sol"),
            timeout_seconds=int(os.getenv("GMGN_CLI_TIMEOUT", "30")),
        )


class GmgnCli:
    """Verified GMGN integration path using the official gmgn-cli interface.

    The official GMGN skill documentation instructs integrations to use gmgn-cli
    rather than scraping gmgn.ai. Commands below are read-only wallet/market
    queries and request raw JSON for machine consumption.
    """

    def __init__(self, config: GmgnCliConfig | None = None) -> None:
        self.config = config or GmgnCliConfig.from_env()

    def run(self, *args: str) -> Any:
        command = [self.config.binary, *args, "--raw"]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GmgnCliError("gmgn-cli is not installed or GMGN_CLI_PATH is invalid") from exc
        except subprocess.TimeoutExpired as exc:
            raise GmgnCliError("gmgn-cli command timed out") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise GmgnCliError(detail[:1000] or f"gmgn-cli exited with {completed.returncode}")

        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise GmgnCliError("gmgn-cli did not return valid JSON") from exc

    def portfolio_stats(self, wallet: str, period: str) -> Any:
        return self.run("portfolio", "stats", "--chain", self.config.chain, "--wallet", wallet, "--period", period)

    def portfolio_holdings(self, wallet: str, limit: int = 50) -> Any:
        return self.run("portfolio", "holdings", "--chain", self.config.chain, "--wallet", wallet, "--order-by", "usd_value", "--direction", "desc", "--limit", str(limit))

    def portfolio_activity(self, wallet: str, limit: int = 50) -> Any:
        return self.run("portfolio", "activity", "--chain", self.config.chain, "--wallet", wallet, "--limit", str(limit))

    def track_smartmoney(self, limit: int = 100) -> Any:
        return self.run("track", "smartmoney", "--chain", self.config.chain, "--limit", str(limit))

    def market_trending(self, interval: str = "1h", limit: int = 50) -> Any:
        return self.run("market", "trending", "--chain", self.config.chain, "--interval", interval, "--order-by", "volume", "--limit", str(limit))
