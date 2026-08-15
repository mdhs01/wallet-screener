from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GMGNRoute:
    name: str
    method: str
    path: str
    weight: int
    auth: str


# Routes verified against the current GMGN Agent Skills documentation.
PORTFOLIO_ROUTES = {
    "info": GMGNRoute("portfolio.info", "GET", "/v1/user/info", 1, "api_key"),
    "holdings": GMGNRoute("portfolio.holdings", "GET", "/v1/user/wallet_holdings", 5, "api_key+private_key"),
    "activity": GMGNRoute("portfolio.activity", "GET", "/v1/user/wallet_activity", 3, "api_key"),
    "stats": GMGNRoute("portfolio.stats", "GET", "/v1/user/wallet_stats", 3, "api_key"),
    "token_balance": GMGNRoute("portfolio.token_balance", "GET", "/v1/user/wallet_token_balance", 1, "api_key"),
    "created_tokens": GMGNRoute("portfolio.created_tokens", "GET", "/v1/user/created_tokens", 2, "api_key"),
}

TRACK_ROUTES = {
    "follow_wallet": GMGNRoute("track.follow_wallet", "GET", "/v1/trade/follow_wallet", 3, "api_key+private_key"),
    "kol": GMGNRoute("track.kol", "GET", "/v1/user/kol", 1, "api_key"),
    "smartmoney": GMGNRoute("track.smartmoney", "GET", "/v1/user/smartmoney", 1, "api_key"),
}

MARKET_ROUTES = {
    "trending": GMGNRoute("market.trending", "GET", "/v1/market/rank", 1, "api_key"),
    "kline": GMGNRoute("market.kline", "GET", "/v1/market/token_kline", 2, "api_key"),
    "signal": GMGNRoute("market.signal", "POST", "/v1/market/token_signal", 3, "api_key"),
}


def route_table() -> dict[str, GMGNRoute]:
    return {**PORTFOLIO_ROUTES, **TRACK_ROUTES, **MARKET_ROUTES}
