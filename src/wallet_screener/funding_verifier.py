from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cluster_analysis import FundingObservation
from .solana_rpc import SolanaRpcClient


@dataclass(slots=True)
class FundingVerifier:
    rpc: SolanaRpcClient
    signatures_limit: int = 50

    def collect(self, wallet: str) -> list[FundingObservation]:
        signatures = self.rpc.call(
            "getSignaturesForAddress",
            [wallet, {"limit": self.signatures_limit}],
        ) or []
        observations: list[FundingObservation] = []
        for item in signatures:
            signature = item.get("signature") if isinstance(item, dict) else None
            if not signature:
                continue
            tx = self.rpc.call(
                "getTransaction",
                [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
            )
            observations.extend(self._extract_transfer_observations(wallet, tx))
        return observations

    @staticmethod
    def _extract_transfer_observations(wallet: str, payload: Any) -> list[FundingObservation]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") if "result" in payload else payload
        if not isinstance(result, dict):
            return []
        block_time = result.get("blockTime")
        meta = result.get("meta") or {}
        pre = meta.get("preBalances") or []
        post = meta.get("postBalances") or []
        message = ((result.get("transaction") or {}).get("message") or {})
        account_keys = message.get("accountKeys") or []
        addresses = []
        for key in account_keys:
            if isinstance(key, dict):
                addresses.append(key.get("pubkey"))
            else:
                addresses.append(key)
        try:
            idx = addresses.index(wallet)
        except ValueError:
            return []
        if idx >= len(pre) or idx >= len(post):
            return []
        delta = int(post[idx]) - int(pre[idx])
        if delta <= 0:
            return []
        funder = None
        candidates = []
        for i, before in enumerate(pre):
            if i == idx or i >= len(post):
                continue
            change = int(post[i]) - int(before)
            if change < 0 and i < len(addresses) and addresses[i]:
                candidates.append((abs(change), addresses[i]))
        if candidates:
            funder = max(candidates, key=lambda item: item[0])[1]
        return [FundingObservation(wallet=wallet, funder=funder, timestamp=block_time, amount_native=delta / 1_000_000_000)]
