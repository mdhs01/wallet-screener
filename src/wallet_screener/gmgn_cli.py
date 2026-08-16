from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any


class GmgnCliError(RuntimeError):
    pass


@dataclass(slots=True)
class GmgnCliConfig:
    binary: str = "gmgn-cli"
    chain: str = "sol"
    timeout_seconds: int = 30
    min_request_interval_seconds: float = 1.0
    cache_ttl_seconds: float = 30.0
    default_429_cooldown_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "GmgnCliConfig":
        return cls(
            binary=os.getenv("GMGN_CLI_PATH", "gmgn-cli"),
            chain=os.getenv("GMGN_CHAIN", "sol"),
            timeout_seconds=int(os.getenv("GMGN_CLI_TIMEOUT", "30")),
            min_request_interval_seconds=float(os.getenv("GMGN_MIN_REQUEST_INTERVAL_SECONDS", "1.0")),
            cache_ttl_seconds=float(os.getenv("GMGN_CACHE_TTL_SECONDS", "30")),
            default_429_cooldown_seconds=float(os.getenv("GMGN_429_COOLDOWN_SECONDS", "5")),
        )


class GmgnCli:
    """Verified GMGN integration path with conservative pacing and 429 protection."""

    _RESET_RE = re.compile(r"~\s*(\d+)s remaining", re.IGNORECASE)

    def __init__(self, config: GmgnCliConfig | None = None) -> None:
        self.config = config or GmgnCliConfig.from_env()
        self._lock = threading.Lock()
        self._last_request_at = 0.0
        self._blocked_until = 0.0
        self._cache: dict[tuple[str, ...], tuple[float, Any]] = {}

    def _wait_for_pacing(self) -> None:
        with self._lock:
            now = time.monotonic()
            if now < self._blocked_until:
                remaining = self._blocked_until - now
                raise GmgnCliError(
                    f"GMGN rate-limit circuit open; retry after {remaining:.1f}s without sending another request"
                )
            delay = self.config.min_request_interval_seconds - (now - self._last_request_at)
            if delay > 0:
                time.sleep(delay)
            self._last_request_at = time.monotonic()

    def _set_rate_limit_cooldown(self, detail: str) -> None:
        match = self._RESET_RE.search(detail)
        cooldown = float(match.group(1)) if match else self.config.default_429_cooldown_seconds
        with self._lock:
            self._blocked_until = max(self._blocked_until, time.monotonic() + cooldown)

    def run(self, *args: str) -> Any:
        key = tuple(args)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and now - cached[0] < self.config.cache_ttl_seconds:
            return cached[1]

        self._wait_for_pacing()
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

        detail = (completed.stderr or completed.stdout).strip()
        if completed.returncode != 0:
            if "429" in detail or "RATE_LIMIT" in detail or "rate limit" in detail.lower():
                self._set_rate_limit_cooldown(detail)
            raise GmgnCliError(detail[:1000] or f"gmgn-cli exited with {completed.returncode}")

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise GmgnCliError("gmgn-cli did not return valid JSON") from exc

        self._cache[key] = (time.monotonic(), payload)
        return payload

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
