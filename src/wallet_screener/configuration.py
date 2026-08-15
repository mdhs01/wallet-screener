from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    provider: str = "null"
    db_path: Path = Path("data/wallet_screener.db")
    max_candidates: int = 50
    schedule_interval_seconds: float = 300.0
    gmgn_cli_path: str = "gmgn-cli"
    gmgn_chain: str = "sol"
    gmgn_cli_timeout: float = 30.0
    gmgn_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        provider = os.getenv("WALLET_SCREENER_PROVIDER", "null").strip().lower()
        max_candidates = _int_env("WALLET_SCREENER_MAX_CANDIDATES", 50)
        interval = _float_env("WALLET_SCREENER_INTERVAL_SECONDS", 300.0)
        timeout = _float_env("GMGN_CLI_TIMEOUT", 30.0)
        if max_candidates <= 0:
            raise ConfigurationError("WALLET_SCREENER_MAX_CANDIDATES must be > 0")
        if interval < 0:
            raise ConfigurationError("WALLET_SCREENER_INTERVAL_SECONDS must be >= 0")
        if timeout <= 0:
            raise ConfigurationError("GMGN_CLI_TIMEOUT must be > 0")
        return cls(
            provider=provider,
            db_path=Path(os.getenv("WALLET_SCREENER_DB", "data/wallet_screener.db")),
            max_candidates=max_candidates,
            schedule_interval_seconds=interval,
            gmgn_cli_path=os.getenv("GMGN_CLI_PATH", "gmgn-cli"),
            gmgn_chain=os.getenv("GMGN_CHAIN", "sol"),
            gmgn_cli_timeout=timeout,
            gmgn_api_key=_optional_env("GMGN_API_KEY"),
        )

    def validate(self) -> None:
        if self.provider not in {"null", "gmgn"}:
            raise ConfigurationError(f"Unsupported provider: {self.provider}")
        if self.provider == "gmgn" and not self.gmgn_cli_path:
            raise ConfigurationError("GMGN_CLI_PATH is required for gmgn provider")


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be numeric") from exc
