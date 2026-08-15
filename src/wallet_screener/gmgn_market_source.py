from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .gmgn_cli import GmgnCli
from .market_observation import MarketSnapshot


@dataclass(slots=True)
class GmgnMarketSourceConfig:
    chain: str = "sol"
    limit: int = 100


class GMGNMarketSnapshotSource:
    """Read-only GMGN market source with explicit normalization boundaries.

    The source consumes the existing GMGN CLI adapter and emits normalized
    MarketSnapshot objects. It does not place trades or sign transactions.
    """

    def __init__(self, cli: GmgnCli | None = None, config: GmgnMarketSourceConfig | None = None) -> None:
        self.cli = cli or GmgnCli()
        self.config = config or GmgnMarketSourceConfig()

    def fetch(self) -> Iterable[MarketSnapshot]:
        payload = self.cli.market_trending(chain=self.config.chain, limit=self.config.limit)
        rows = self._rows(payload)
        return [snapshot for row in rows if (snapshot := self._normalize(row)) is not None]

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        body = payload.get("data") if isinstance(payload, dict) else payload
        if isinstance(body, dict):
            for key in ("items", "tokens", "results", "data"):
                value = body.get(key)
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
        if isinstance(body, list):
            return [row for row in body if isinstance(row, dict)]
        return []

    @staticmethod
    def _normalize(row: dict[str, Any]) -> MarketSnapshot | None:
        token = row.get("address") or row.get("token_address") or row.get("base_address")
        price = row.get("price_usd") or row.get("price")
        liquidity = row.get("liquidity_usd") or row.get("liquidity")
        ts = row.get("timestamp") or row.get("ts")
        if not token or price is None or liquidity is None:
            return None
        try:
            price_f = float(price)
            liquidity_f = float(liquidity)
            ts_i = int(ts) if ts is not None else 0
        except (TypeError, ValueError):
            return None
        if price_f <= 0 or liquidity_f < 0 or ts_i <= 0:
            return None
        return MarketSnapshot(
            wallet=str(row.get("wallet") or row.get("wallet_address") or "unknown"),
            token=str(token),
            signal_ts=ts_i,
            market_price_usd=price_f,
            liquidity_usd=liquidity_f,
            actionable=bool(row.get("actionable", False)),
            missed=bool(row.get("missed", False)),
            false_signal=bool(row.get("false_signal", False)),
            notes="gmgn_market_trending",
        )
