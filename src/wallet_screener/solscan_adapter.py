from __future__ import annotations

from typing import Any

from .api_client import ApiClient, ApiError
from .api_config import ProviderConfig
from .normalized import first_list, first_mapping


class SolscanAdapter:
    """Generic Solscan REST adapter; endpoint paths are supplied explicitly later."""

    def __init__(self, config: ProviderConfig) -> None:
        if not config.base_url:
            raise ApiError("SOLSCAN_BASE_URL is not configured")
        headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
        self.client = ApiClient(
            base_url=config.base_url,
            headers=headers,
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
            requests_per_second=config.requests_per_second,
            cache_ttl_seconds=config.cache_ttl_seconds,
        )

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        if not endpoint:
            raise ApiError("Solscan endpoint is not configured")
        return self.client.get(endpoint, params=params).data

    @staticmethod
    def mapping(payload: Any) -> dict[str, Any]:
        return first_mapping(payload, "data", "result")

    @staticmethod
    def rows(payload: Any) -> list[dict[str, Any]]:
        return [row for row in first_list(payload, "data", "items", "results") if isinstance(row, dict)]
