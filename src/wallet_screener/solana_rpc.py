from __future__ import annotations

from typing import Any

from .api_client import ApiClient
from .api_config import ProviderConfig


class SolanaRpcClient:
    """Minimal JSON-RPC transport. Method semantics stay isolated from screening logic."""

    def __init__(self, config: ProviderConfig) -> None:
        if not config.base_url:
            raise ValueError("SOLANA_RPC_BASE_URL is not configured")
        self.client = ApiClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"} if config.api_key else {},
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
            requests_per_second=config.requests_per_second,
            cache_ttl_seconds=config.cache_ttl_seconds,
        )

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        response = self.client.request("POST", "", json_body=payload)
        data = response.data
        if not isinstance(data, dict):
            raise ValueError("Invalid Solana RPC response")
        if data.get("error") is not None:
            raise RuntimeError(f"Solana RPC error: {data['error']}")
        return data.get("result")
