from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class FundingObservation:
    wallet: str
    funder: str | None
    timestamp: int | None = None
    amount_native: float = 0.0


@dataclass(frozen=True, slots=True)
class WalletLink:
    wallet_a: str
    wallet_b: str
    shared_funder: str
    time_delta_seconds: int | None = None


@dataclass(slots=True)
class ClusterReport:
    wallet: str
    direct_funders: list[str] = field(default_factory=list)
    common_funder_count: int = 0
    linked_wallets: list[str] = field(default_factory=list)
    cluster_size: int = 1
    synchronized_links: int = 0
    independence_score: float = 1.0
    warnings: list[str] = field(default_factory=list)


def analyze_cluster(
    wallet: str,
    observations: Iterable[FundingObservation],
    *,
    wallet_universe: Iterable[str] = (),
    synchronization_window_seconds: int = 120,
) -> ClusterReport:
    all_obs = list(observations)
    obs = [o for o in all_obs if o.wallet == wallet]
    funders = sorted({o.funder for o in obs if o.funder and o.funder != wallet})
    report = ClusterReport(wallet=wallet, direct_funders=funders, common_funder_count=len(funders))

    if not funders:
        return report

    links: list[WalletLink] = []
    for other in sorted(set(wallet_universe) - {wallet}):
        other_obs = [o for o in all_obs if o.wallet == other and o.funder in funders]
        for a in obs:
            if not a.funder:
                continue
            for b in other_obs:
                if a.funder != b.funder:
                    continue
                delta = None
                if a.timestamp is not None and b.timestamp is not None:
                    delta = abs(a.timestamp - b.timestamp)
                links.append(WalletLink(wallet, other, a.funder, delta))

    report.linked_wallets = sorted({link.wallet_b for link in links})
    report.cluster_size = 1 + len(report.linked_wallets)
    report.synchronized_links = sum(
        1 for link in links if link.time_delta_seconds is not None and link.time_delta_seconds <= synchronization_window_seconds
    )

    funder_penalty = min(0.60, 0.20 * len(funders))
    cluster_penalty = min(0.30, 0.05 * len(report.linked_wallets))
    sync_penalty = min(0.25, 0.05 * report.synchronized_links)
    report.independence_score = max(0.0, min(1.0, 1.0 - funder_penalty - cluster_penalty - sync_penalty))

    if report.common_funder_count:
        report.warnings.append("shared_funding_source_detected")
    if report.linked_wallets:
        report.warnings.append("wallet_cluster_links_detected")
    if report.synchronized_links:
        report.warnings.append("synchronized_funding_detected")
    return report
