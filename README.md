# Wallet Screener

Wallet screening engine based on the uploaded GMGN Wallet Screening Framework.

## Current scope

- Provider-agnostic architecture
- Mock/in-memory provider for development and tests
- Layered screening pipeline
- Configurable thresholds
- Explainable scoring, rejection reasons, warnings, and layer scores
- Phase 3 automated preparation and gating for the required 15–20 trade manual review
- Phase 4 paper-tracking engine for 3–7 day validation
- Phase 5 dynamic watchlist and edge-decay revalidation
- Phase 6 provider-neutral HTTP/API transport layer
- Phase 7 verified GMGN data contract and official `gmgn-cli` live-data adapter
- Phase 8 end-to-end orchestration and SQLite persistence

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 7: Verified GMGN Mapping

The live integration uses the official `gmgn-cli` interface rather than scraping `gmgn.ai`. Current documented read-only wallet queries include:

- `portfolio stats --period 7d|30d`
- `portfolio holdings`
- `portfolio activity`
- `track smartmoney`
- `market trending`

The project records the documented GMGN OpenAPI route paths and rate-limit weights in `gmgn_openapi_contract.py`.

`GMGNLiveProvider` maps documented portfolio stats, holdings and activity into the internal screening models and deduplicates wallet candidates from Smart Money activity.

The provider does **not** fabricate evidence for source-framework layers that are not directly established by these queries. Wallet Radar / Shared Holdings / Earliest Bought, synchronized funding/cluster analysis, and verified launch-to-entry/liquidity trade evidence remain explicit capabilities for later integration.

GMGN portfolio holdings currently require the provider's critical authentication flow; credentials are never stored in source control.

## Phase 8: End-to-End Pipeline

`ScreeningPipeline` is now the single orchestration entry point. It:

1. discovers wallets from the selected provider
2. deduplicates candidate addresses
3. applies the full `WalletScreener` stack
4. serializes explainable results
5. persists every run and result to SQLite
6. returns one machine-readable `PipelineReport`

The CLI supports a provider switch and a persistent database path:

```bash
python -m src.wallet_screener --provider null
python -m src.wallet_screener --provider gmgn --max-candidates 50 --db data/wallet_screener.db
```

The GMGN path still requires the user's configured `gmgn-cli` credentials and environment. No live credentials are included in the repository.

## Persistence

`ScreeningStore` stores:

- screening run status and counts
- per-wallet screening result payloads
- score, stage, pass/fail state
- full explainable JSON payload for later analysis

The SQLite schema is intentionally small so it can later be replaced or extended without changing the screening engine.

## Run

Python 3.11+

```bash
python -m src.wallet_screener --provider null
```

Run tests:

```bash
python -m pytest
```
