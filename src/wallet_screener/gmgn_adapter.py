from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .api_client import ApiClient, ApiError
from .api_config import ProviderConfig
from .normalized import first_list, first_mapping


@dataclass(slots=True)
class GmgnEndpointMap:
    """Endpoint paths are intentionally empty until the official API contract is supplied."""

    discovery: str = ""
    wallet_metrics: str = ""
    holdings: str = ""
    trades: str = ""
    cross_token: str = ""
    funding_cluster: str = ""


class GMGNAdapter:
    """GMGN transport adapter with no hard-coded undocumented endpoints."""

    def __init__(self, config: ProviderConfig, endpoints: GmgnEndpointMap | None = None) -> None:
        self.config = config
        self.endpoints = endpoints or GmgnEndpointMap()
        headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
        if not config.base_url:
            raise ApiError("GMGN base URL is not configured")
        self.client = ApiClient(
            base_url=config.base_url,
            headers=headers,
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
            requests_per_second=config.requests_per_second,
            cache_ttl_seconds=config.cache_ttl_seconds,
        )

    def _require(self, path: str, operation: str) -> str:
        if not path:
            raise ApiError(f"GMGN endpoint for {operation} is not configured")
        return path

    def discover_wallets(self, params: dict[str, Any] | None = None) -> list[str]:
        payload = self.client.get(self._require(self.endpoints.discovery, "discovery"), params=params).data
        rows = first_list(payload, "data", "items", "wallets", "results")
        addresses: list[str] = []
        for row in rows:
            if isinstance(row, str):
                addresses.append(row)
            elif isinstance(row, dict):
                address = row.get("address") or row.get("wallet") or row.get("wallet_address")
                if address:
                    addresses.append(str(address))
        return addresses

    def wallet_metrics(self, address: str) -> dict[str, Any]:
        payload = self.client.get(self._require(self.endpoints.wallet_metrics, "wallet_metrics"), params={"address": address}).data
        return first_mapping(payload, "data", "wallet", "result")

    def holdings(self, address: str) -> list[dict[str, Any]]:
        payload = self.client.get(self._require(self.endpoints.holdings, "holdings"), params={"address": address}).data
        return [row for row in first_list(payload, "data", "items", "holdings", "results") if isinstance(row, dict)]

    def trades(self, address: str, limit: int = 20) -> list[dict[str, Any]]:
        payload = self.client.get(self._require(self.endpoints.trades, "trades"), params={"address": address, "limit": limit}).data
        return [row for row in first_list(payload, "data", "items", "trades", "results") if isinstance(row, dict)][:limit]

    def cross_token(self, address: str) -> dict[str, Any]:
        payload = self.client.get(self._require(self.endpoints.cross_token, "cross_token"), params={"address": address}).data
        return first_mapping(payload, "data", "result")

    def funding_cluster(self, address: str) -> dict[str, Any]:
        payload = self.client.get(self._require(self.endpoints.funding_cluster, "funding_cluster"), params={"address": address}).data
        return first_mapping(payload, "data", "result")
