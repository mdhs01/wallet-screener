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
- Phase 11 operational resilience and health checks
- Phase 12 read-only live validation for the configured GMGN runtime
- Phase 13 persistent, idempotent paper-tracking runtime
- Phase 14 market snapshot → paper-observation normalization
- Phase 15 read-only market feed polling with duplicate protection
- Phase 17 bounded live-market orchestration
- Phase 18 scheduled runtime with singleton protection, graceful stop, and optional circuit-breaker integration

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 18: Scheduler & Continuous Runtime

`scheduler.py` provides `ScheduledRuntime` for controlled recurring execution of an existing read-only job.

```text
ScheduledRuntime
      ↓
read-only pipeline / market feed job
      ↓
screening + paper tracking + watchlist
```

The runtime provides:

- configurable interval
- bounded cycle mode for deterministic tests/deployments
- singleton protection within the process
- graceful stop with `stop()`
- optional `CircuitBreaker` integration
- cycle-level success/failure/skipped accounting

The scheduler does not own screening semantics and does not place orders, sign transactions, or trade.

See `docs/PHASE18_SCHEDULER.md`.

## Phase 17: Live Market Loop

`market_loop.py` adds a bounded orchestration layer around `LiveMarketFeed`.

## Phase 15: Market Feed

`market_feed.py` provides a source-agnostic polling layer. Each cycle reports fetched, accepted, duplicate, rejected, and source-error counts. Duplicate observations are protected by the persistent paper store's deterministic idempotency guard.

## Phase 13: Persistent Live Paper Tracking

`paper_persistence.py` stores every paper observation in SQLite with a deterministic unique key. Duplicate observations are ignored, so repeated polling/restarts do not inflate the sample.

## Phase 12: Live Validation

`live_validation.py` provides a read-only runtime validation report. It checks provider capabilities, live candidate discovery, wallet metrics, current holdings, and recent activity.

The validator only reports `ready=true` after at least one wallet is returned and all required checks pass. Empty discovery is not treated as a successful live test.

## Phase 11: Production Hardening

Operational helpers provide retry with exponential backoff, circuit-breaker state for repeatedly failing dependencies, filesystem/database health checks, and explicit degraded status when API credentials/endpoints are not configured.

## Phase 10: Unified Wallet Lifecycle

`WalletLifecycle` connects the existing screening result, paper-tracking state, and dynamic watchlist. Until the paper gate is satisfied, a wallet remains `review` even when the historical screening score is high.

## Phase 9: Funding & Cluster Verification

The funding layer verifies evidence that can make multiple wallets non-independent signals. It uses Solana JSON-RPC transaction history and a normalized evidence model. The implementation is conservative: missing data is not treated as clean evidence, and common ownership is not asserted solely from similar trading behavior.

## Phase 7: Verified GMGN Mapping

The live integration uses the official `gmgn-cli` interface rather than scraping `gmgn.ai`. Current documented read-only wallet queries include:

- `portfolio stats --period 7d|30d`
- `portfolio holdings`
- `portfolio activity`
- `track smartmoney`
- `market trending`

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
