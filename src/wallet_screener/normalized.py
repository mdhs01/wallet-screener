from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizedWallet:
    address: str
    metrics: dict[str, Any] = field(default_factory=dict)
    holdings: list[dict[str, Any]] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    cross_token: dict[str, Any] = field(default_factory=dict)
    funding_cluster: dict[str, Any] = field(default_factory=dict)

    def as_provider_payload(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "metrics": self.metrics,
            "holdings": self.holdings,
            "trades": self.trades,
            "cross_token": self.cross_token,
            "funding_cluster": self.funding_cluster,
        }


class SchemaError(ValueError):
    pass


def require_mapping(payload: Any, context: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SchemaError(f"{context} must be an object")
    return payload


def first_mapping(payload: Any, *keys: str) -> dict[str, Any]:
    root = require_mapping(payload, "API payload")
    for key in keys:
        value = root.get(key)
        if isinstance(value, dict):
            return value
    return root


def first_list(payload: Any, *keys: str) -> list[Any]:
    root = require_mapping(payload, "API payload")
    for key in keys:
        value = root.get(key)
        if isinstance(value, list):
            return value
    return []
