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
- Phase 9 conservative funding-source and wallet-cluster verification
- Phase 10 unified wallet lifecycle connecting screening, paper tracking, and watchlist promotion

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 9: Funding & Cluster Verification

The funding layer verifies evidence that can make multiple wallets non-independent signals. It uses Solana JSON-RPC transaction history and a normalized evidence model.

Components:

- `cluster_analysis.py`: shared-funder, linked-wallet, synchronized-funding and independence calculations.
- `funding_verifier.py`: collects native balance-transfer evidence using `getSignaturesForAddress` and `getTransaction`.
- `cluster_provider.py`: decorates an existing wallet provider with funding/cluster evidence.

The implementation is intentionally conservative: missing data is not treated as clean evidence, and common ownership is not asserted solely from similar trading behavior. See `docs/PHASE9_FUNDING_CLUSTER.md`.

## Phase 10: Unified Wallet Lifecycle

`WalletLifecycle` connects the existing screening result, paper-tracking state, and dynamic watchlist.

A wallet can be evaluated through one lifecycle call:

```text
screening result
    ↓
paper tracking readiness
    ↓
watchlist decision
    ↓
ACTIVE / REVIEW / DROPPED
```

The lifecycle does not invent paper observations. Real observations must be added by the market-data/runtime layer. Until the paper gate is satisfied, a wallet remains `review` even when the historical screening score is high. This preserves the framework's separation between historical edge and actionability validation.

## Phase 7: Verified GMGN Mapping

The live integration uses the official `gmgn-cli` interface rather than scraping `gmgn.ai`. Current documented read-only wallet queries include:

- `portfolio stats --period 7d|30d`
- `portfolio holdings`
- `portfolio activity`
- `track smartmoney`
- `market trending`

The project records the documented GMGN OpenAPI route paths and rate-limit weights in `gmgn_openapi_contract.py`.

`GMGNLiveProvider` maps documented portfolio stats, holdings and activity into the internal screening models and deduplicates wallet candidates from Smart Money activity.

The provider does **not** fabricate evidence for source-framework layers that are not directly established by these queries. Wallet Radar / Shared Holdings / Earliest Bought and verified launch-to-entry/liquidity trade evidence remain explicit capability gaps.

## Phase 8: End-to-End Pipeline

`ScreeningPipeline` is the single orchestration entry point. It discovers wallets, deduplicates candidates, applies the screening stack, serializes explainable results, persists runs/results to SQLite, and returns one machine-readable `PipelineReport`.

## Run

Python 3.11+

```bash
python -m src.wallet_screener --provider null
python -m src.wallet_screener --provider gmgn --max-candidates 50 --db data/wallet_screener.db
```

Run tests:

```bash
python -m pytest
```
