from __future__ import annotations

from .cluster_analysis import analyze_cluster
from .funding_verifier import FundingVerifier
from .providers import CrossTokenEvidence, WalletDataProvider


class FundingAwareProvider(WalletDataProvider):
    """Decorates a wallet provider with conservative Solana funding analysis."""

    def __init__(self, base: WalletDataProvider, verifier: FundingVerifier, *, universe_limit: int = 50) -> None:
        self.base = base
        self.verifier = verifier
        self.universe_limit = universe_limit

    def discover_wallets(self) -> list[str]:
        return self.base.discover_wallets()

    def get_wallet_metrics(self, address: str) -> dict:
        return self.base.get_wallet_metrics(address)

    def get_current_holdings(self, address: str) -> list[dict]:
        return self.base.get_current_holdings(address)

    def get_trade_sample(self, address: str, limit: int = 20) -> list[dict]:
        return self.base.get_trade_sample(address, limit=limit)

    def get_cross_token_evidence(self, address: str) -> CrossTokenEvidence:
        return self.base.get_cross_token_evidence(address)

    def get_funding_cluster(self, address: str) -> dict:
        universe = self.base.discover_wallets()[: self.universe_limit]
        observations = []
        for wallet in universe:
            try:
                observations.extend(self.verifier.collect(wallet))
            except Exception:
                # Funding verification must fail closed: unknown evidence is not
                # converted into a clean score.
                continue
        report = analyze_cluster(address, observations, wallet_universe=universe)
        return {
            "common_funder_count": report.common_funder_count,
            "cluster_size": report.cluster_size,
            "independence_score": report.independence_score,
            "linked_wallets": report.linked_wallets,
            "warnings": report.warnings,
        }
