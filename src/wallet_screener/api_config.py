from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class ProviderConfig:
    name: str
    base_url: str = ""
    api_key: str = ""
    timeout_seconds: float = 15.0
    retries: int = 2
    requests_per_second: float = 5.0
    cache_ttl_seconds: float = 5.0
    enabled: bool = False

    @classmethod
    def from_env(cls, prefix: str, *, name: str) -> "ProviderConfig":
        return cls(
            name=name,
            base_url=os.getenv(f"{prefix}_BASE_URL", "").strip(),
            api_key=os.getenv(f"{prefix}_API_KEY", "").strip(),
            timeout_seconds=float(os.getenv(f"{prefix}_TIMEOUT", "15")),
            retries=int(os.getenv(f"{prefix}_RETRIES", "2")),
            requests_per_second=float(os.getenv(f"{prefix}_RPS", "5")),
            cache_ttl_seconds=float(os.getenv(f"{prefix}_CACHE_TTL", "5")),
            enabled=os.getenv(f"{prefix}_ENABLED", "false").lower() == "true",
        )


@dataclass(slots=True)
class ApiConfig:
    gmgn: ProviderConfig
    solana_rpc: ProviderConfig
    solscan: ProviderConfig

    @classmethod
    def from_env(cls) -> "ApiConfig":
        return cls(
            gmgn=ProviderConfig.from_env("GMGN", name="gmgn"),
            solana_rpc=ProviderConfig.from_env("SOLANA_RPC", name="solana_rpc"),
            solscan=ProviderConfig.from_env("SOLSCAN", name="solscan"),
        )
