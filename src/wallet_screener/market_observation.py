from __future__ import annotations

from dataclasses import dataclass
from time import time

from .paper_tracking import PaperObservation


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    wallet: str
    token: str
    signal_ts: int
    market_price_usd: float
    liquidity_usd: float
    wallet_entry_ts: int | None = None
    wallet_exit_ts: int | None = None
    wallet_entry_price_usd: float = 0.0
    wallet_exit_price_usd: float = 0.0
    actionable: bool = False
    missed: bool = False
    false_signal: bool = False
    slippage_pct: float = 0.0
    hypothetical_position_usd: float = 0.0
    notes: str = ""


class MarketObservationAdapter:
    """Converts normalized market snapshots into paper observations.

    This adapter intentionally has no network or trading responsibilities.
    """

    def __init__(self, *, default_position_usd: float = 100.0) -> None:
        if default_position_usd <= 0:
            raise ValueError("default_position_usd must be > 0")
        self.default_position_usd = default_position_usd

    def to_paper_observation(self, snapshot: MarketSnapshot, *, exit_price_usd: float | None = None, exit_ts: int | None = None) -> PaperObservation:
        if snapshot.market_price_usd <= 0:
            raise ValueError("market_price_usd must be > 0")
        hypothetical_exit_price = exit_price_usd or snapshot.wallet_exit_price_usd
        hypothetical_exit_ts = exit_ts or snapshot.wallet_exit_ts
        return PaperObservation(
            wallet=snapshot.wallet,
            token=snapshot.token,
            signal_ts=snapshot.signal_ts,
            wallet_entry_ts=snapshot.wallet_entry_ts,
            wallet_exit_ts=snapshot.wallet_exit_ts,
            wallet_entry_price=snapshot.wallet_entry_price_usd,
            wallet_exit_price=snapshot.wallet_exit_price_usd,
            hypothetical_entry_ts=snapshot.signal_ts,
            hypothetical_exit_ts=hypothetical_exit_ts,
            hypothetical_entry_price=snapshot.market_price_usd,
            hypothetical_exit_price=hypothetical_exit_price,
            liquidity_at_signal_usd=snapshot.liquidity_usd,
            hypothetical_position_usd=snapshot.hypothetical_position_usd or self.default_position_usd,
            slippage_pct=snapshot.slippage_pct,
            missed=snapshot.missed,
            false_signal=snapshot.false_signal,
            actionable=snapshot.actionable,
            notes=snapshot.notes,
        )

    @staticmethod
    def timestamp_now() -> int:
        return int(time())
