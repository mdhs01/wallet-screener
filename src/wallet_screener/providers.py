from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CrossTokenEvidence:
    runner_tokens: list[str] = field(default_factory=list)
    repeated_early: int = 0
    repeated_profitable: int = 0
    shared_holdings_hits: int = 0
    earliest_bought_hits: int = 0

    @property
    def score(self) -> float:
        if not self.runner_tokens:
            return 0.0
        independent_hits = self.repeated_early + self.repeated_profitable
        radar_hits = self.shared_holdings_hits + self.earliest_bought_hits
        return min(1.0, (independent_hits / (2 * len(self.runner_tokens))) * 0.7 + (radar_hits / (2 * len(self.runner_tokens))) * 0.3)


class WalletDataProvider(ABC):
    @abstractmethod
    def discover_wallets(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_wallet_metrics(self, address: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_current_holdings(self, address: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_trade_sample(self, address: str, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_cross_token_evidence(self, address: str) -> CrossTokenEvidence:
        raise NotImplementedError

    @abstractmethod
    def get_funding_cluster(self, address: str) -> dict[str, Any]:
        raise NotImplementedError


class NullProvider(WalletDataProvider):
    """Placeholder provider used until real APIs are connected."""

    def discover_wallets(self) -> list[str]:
        return []

    def get_wallet_metrics(self, address: str) -> dict[str, Any]:
        return {"address": address}

    def get_current_holdings(self, address: str) -> list[dict[str, Any]]:
        return []

    def get_trade_sample(self, address: str, limit: int = 20) -> list[dict[str, Any]]:
        return []

    def get_cross_token_evidence(self, address: str) -> CrossTokenEvidence:
        return CrossTokenEvidence()

    def get_funding_cluster(self, address: str) -> dict[str, Any]:
        return {"common_funder_count": 0, "cluster_size": 1}
