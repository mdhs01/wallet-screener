from __future__ import annotations

from typing import Any

from .gmgn_cli import GmgnCli
from .models import HoldingSnapshot, TradeObservation
from .providers import CrossTokenEvidence, WalletDataProvider


def _data(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("data"), (dict, list)):
        return payload["data"]
    return payload


def _rows(payload: Any, key: str) -> list[dict[str, Any]]:
    body = _data(payload)
    if isinstance(body, dict) and isinstance(body.get(key), list):
        return [x for x in body[key] if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []


def _stat(payload: Any) -> dict[str, Any]:
    body = _data(payload)
    if isinstance(body, list):
        return body[0] if body and isinstance(body[0], dict) else {}
    return body if isinstance(body, dict) else {}


class GMGNLiveProvider(WalletDataProvider):
    """Maps documented GMGN wallet/market queries into the screener contract."""

    def __init__(self, cli: GmgnCli | None = None) -> None:
        self.cli = cli or GmgnCli()
        self._capabilities = {
            "discovery": True,
            "stats_7d_30d": True,
            "activity": True,
            "holdings": True,
            "cross_token_radar": False,
            "funding_cluster": False,
            "manual_trade_launch_liquidity": False,
        }

    @property
    def capabilities(self) -> dict[str, bool]:
        return dict(self._capabilities)

    def discover_wallets(self) -> list[str]:
        payload = self.cli.track_smartmoney(limit=100)
        rows = (
            _rows(payload, "trades")
            or _rows(payload, "items")
            or _rows(payload, "results")
            or _rows(payload, "list")
        )
        addresses: list[str] = []
        for row in rows:
            value = row.get("maker") or row.get("wallet_address") or row.get("wallet") or row.get("address")
            if value:
                addresses.append(str(value))
        return list(dict.fromkeys(addresses))

    def get_wallet_metrics(self, address: str) -> dict[str, Any]:
        stats7 = _stat(self.cli.portfolio_stats(address, "7d"))
        stats30 = _stat(self.cli.portfolio_stats(address, "30d"))
        pnl7 = stats7.get("pnl_stat") if isinstance(stats7.get("pnl_stat"), dict) else {}
        pnl30 = stats30.get("pnl_stat") if isinstance(stats30.get("pnl_stat"), dict) else {}
        common = stats30.get("common") if isinstance(stats30.get("common"), dict) else {}

        realized7 = float(stats7.get("realized_profit") or 0.0)
        realized30 = float(stats30.get("realized_profit") or 0.0)
        cost30 = float(stats30.get("total_cost") or 0.0)
        tx7 = int(stats7.get("buy") or 0) + int(stats7.get("sell") or 0)
        tx30 = int(stats30.get("buy") or 0) + int(stats30.get("sell") or 0)
        token_diversity = int(pnl30.get("token_num") or 0)
        followers = int(common.get("follow_count") or common.get("followers_count") or 0)

        return {
            "address": address,
            "win_rate_7d": float(pnl7.get("winrate") or 0.0),
            "win_rate_30d": float(pnl30.get("winrate") or 0.0),
            "realized_pnl_7d": realized7,
            "realized_pnl_30d": realized30,
            "unrealized_pnl": float(stats30.get("unrealized_profit") or 0.0),
            "total_cost_30d": cost30,
            "tx_7d": tx7,
            "tx_30d": tx30,
            "token_diversity_30d": token_diversity,
            "cost_7d": float(stats7.get("total_cost") or 0.0),
            "cost_30d": cost30,
            "balance_native": float(stats30.get("native_balance") or 0.0),
            "trade_count_30d": tx30,
            "public_followers": followers,
            "creator_open_count": int(common.get("created_token_count") or 0),
            # Presence of a funder is evidence that needs deeper verification;
            # it is not equivalent to a failed cluster-independence score.
            "independence_score": 1.0,
            "avg_hold_minutes": float(pnl30.get("avg_holding_period") or 0.0) / 60.0,
        }

    def get_current_holdings(self, address: str) -> list[dict[str, Any]]:
        rows = _rows(self.cli.portfolio_holdings(address, limit=50), "holdings")
        if not rows:
            rows = _rows(self.cli.portfolio_holdings(address, limit=50), "list")
        output: list[dict[str, Any]] = []
        for row in rows:
            token = row.get("token") if isinstance(row.get("token"), dict) else {}
            output.append({
                "token": str(token.get("address") or token.get("symbol") or "unknown"),
                "current_value": float(row.get("usd_value") or 0.0),
                "original_value": float(row.get("cost") or row.get("history_bought_cost") or 0.0),
                "unrealized_pnl": float(row.get("unrealized_profit") or 0.0),
                "held_after_partial_tp": bool((row.get("sell_tx_count") or 0) > 0 and (row.get("usd_value") or 0) > 0),
                "is_zero_value": float(row.get("usd_value") or 0.0) <= 0.0,
            })
        return output

    def get_trade_sample(self, address: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = _rows(self.cli.portfolio_activity(address, limit=max(limit, 20)), "activities")
        trades: list[dict[str, Any]] = []
        for row in rows:
            kind = str(row.get("type") or "").lower()
            if kind not in {"buy", "sell", "transferin", "transfer"}:
                continue
            token = row.get("token") if isinstance(row.get("token"), dict) else {}
            ts = row.get("timestamp")
            trades.append({
                "token": str(token.get("address") or token.get("symbol") or "unknown"),
                "entry_ts": int(ts) if kind == "buy" and ts is not None else None,
                "exit_ts": int(ts) if kind == "sell" and ts is not None else None,
                "buy_size_usd": float(row.get("cost_usd") or 0.0) if kind == "buy" else 0.0,
                "realized_pnl_usd": 0.0,
                "transfer_in": kind == "transferin",
                "did_not_buy": kind == "transferin",
            })
        return trades[:limit]

    def get_cross_token_evidence(self, address: str) -> CrossTokenEvidence:
        return CrossTokenEvidence()

    def get_funding_cluster(self, address: str) -> dict[str, Any]:
        return {"common_funder_count": 0, "cluster_size": 1, "independence_score": 0.0}
