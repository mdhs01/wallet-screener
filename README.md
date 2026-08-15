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
- Phase 19 unified one-cycle runtime joining screening, market feed, persistence, and lifecycle
- Phase 21 runtime CLI shell with explicit once/scheduled/validate/health commands
- Phase 22 unified environment/runtime configuration with validation

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 22: Configuration & Secrets

`configuration.py` provides `RuntimeSettings` and `ConfigurationError` as the central runtime configuration contract.

Supported environment variables:

```text
WALLET_SCREENER_PROVIDER
WALLET_SCREENER_DB
WALLET_SCREENER_MAX_CANDIDATES
WALLET_SCREENER_INTERVAL_SECONDS
GMGN_CLI_PATH
GMGN_CHAIN
GMGN_CLI_TIMEOUT
GMGN_API_KEY
```

The configuration layer validates numeric values and supported providers. Secrets are read from environment variables and are not accepted as CLI arguments or stored in source code.

This keeps runtime settings separate from screening logic and gives the deployment layer one consistent configuration object.

## Phase 21: Runtime CLI

`cli.py` provides a small operational entrypoint with four explicit modes:

```bash
python -m src.wallet_screener.cli health --db data/wallet_screener.db
python -m src.wallet_screener.cli validate --db data/wallet_screener.db
python -m src.wallet_screener.cli once --db data/wallet_screener.db --max-candidates 50
python -m src.wallet_screener.cli scheduled --db data/wallet_screener.db --interval 300 --cycles 10
```

The CLI intentionally does not accept API keys or other secrets as command-line arguments. Provider construction and credentials remain configuration/runtime concerns.

## Phase 19: Unified Runtime Job

`unified_runtime.py` provides `UnifiedRuntimeJob` for one read-only end-to-end cycle. Lifecycle evaluation occurs from the screening result before the current cycle's market observations are ingested.

## Phase 18: Scheduler & Continuous Runtime

`scheduler.py` provides `ScheduledRuntime` for controlled recurring execution of an existing read-only job, with configurable interval, bounded cycles, singleton protection, graceful stop, and cycle accounting.

## Phase 17: Live Market Loop

`market_loop.py` adds a bounded orchestration layer around `LiveMarketFeed`.

## Phase 15: Market Feed

`market_feed.py` provides a source-agnostic polling layer. Each cycle reports fetched, accepted, duplicate, rejected, and source-error counts. Duplicate observations are protected by the persistent paper store's deterministic idempotency guard.

## Phase 13: Persistent Live Paper Tracking

`paper_persistence.py` stores every paper observation in SQLite with a deterministic unique key. Duplicate observations are ignored, so repeated polling/restarts do not inflate the sample.

## Phase 12: Live Validation

`live_validation.py` provides a read-only runtime validation report. It checks provider capabilities, live candidate discovery, wallet metrics, current holdings, and recent activity.

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
