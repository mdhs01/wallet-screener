# Phase 7 — Verified GMGN Data Mapping

## Source of truth

GMGN's current official Agent Skills documentation exposes a read-only wallet workflow through `gmgn-cli`:

- `portfolio stats --period 7d|30d`
- `portfolio holdings`
- `portfolio activity`
- `track smartmoney`
- `market trending`

The documented API routes are also recorded in `gmgn_openapi_contract.py`.

## Implemented mapping

`GMGNLiveProvider` maps the documented portfolio statistics into the internal `WalletMetrics` schema and wallet holdings/activity into the existing `HoldingSnapshot` / `TradeObservation` contracts.

The provider also deduplicates Smart Money wallet discovery from `track smartmoney` results.

## Intentionally unsupported for now

The source framework requires evidence that is not equivalent to generic wallet statistics:

- Wallet Radar / Shared Holdings / Earliest Bought cross-token validation
- synchronized funding / cluster analysis
- launch-to-entry timing plus liquidity-at-entry for a verified 15–20 trade sample

Those layers return an explicit unavailable/zero evidence state instead of being inferred from unrelated data. This prevents the live provider from manufacturing evidence that the upstream API does not directly provide.

## Authentication notes

The current GMGN documentation states that normal portfolio stats/activity and Smart Money tracking use an API key, while portfolio holdings requires critical authentication with the API key plus GMGN private API signing key. The project does not store either credential in source control.

## Rate-limit policy

The documented GMGN route weights are preserved in the contract so the next phase can align request scheduling with the provider's leaky-bucket limits. The existing generic `ApiClient` also has a local limiter, cache and retry layer.

## Next phase

Phase 8 will combine:

1. GMGN live data
2. Solana RPC / explorer funding verification
3. token-level cross-token evidence
4. manual QA and paper tracking persistence
5. end-to-end candidate → watchlist pipeline
