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
- Phase 23 structured observability and runtime metrics
- Phase 24 deterministic full-runtime integration coverage
- Phase 25 CI quality gate
- Phase 26 read-only live provider contract validation boundary
- Phase 27 auditable read-only live validation runner

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 27: Actual Live Read-Only Validation Run

`live_validation_run.py` provides `LiveValidationRunner`, which executes the explicit Phase 26 capability checks and can persist the result as an auditable JSON report.

The runner is deliberately provider- and environment-neutral: the caller supplies the concrete read-only checks. This lets deployment bind the verified GMGN CLI/runtime without embedding secrets or network assumptions into the screening engine.

**Important:** implementation of the runner is not the same as a successful live validation. Phase 27 becomes **LIVE VERIFIED** only after the runner is executed in a real environment with the required GMGN runtime/credentials and every required check passes.

See `docs/PHASE27_LIVE_VALIDATION_RUN.md`.

## Phase 26: Live Contract Validation

`live_contract.py` provides a provider-neutral, read-only contract validator. It executes explicitly supplied capability checks and reports every failed check with its exception/detail rather than hiding live dependency failures.

## Phase 25: CI Quality Gate

GitHub Actions runs the Python test suite and source compilation checks on pushes and pull requests. CI is deterministic and does not require live API credentials.

## Phase 24: Full Integration Testing

Phase 24 connects Phase 23 observability directly to `UnifiedRuntimeJob` and adds deterministic integration coverage for the complete read-only runtime boundary.

## Phase 23: Observability & Monitoring

`observability.py` adds provider-neutral operational visibility: JSON structured logging, runtime counters/gauges, cycle timings, market/paper counters, standardized errors, and thread-safe snapshots.

## Phase 22: Configuration & Secrets

`configuration.py` provides `RuntimeSettings` and `ConfigurationError` as the central runtime configuration contract.

## Phase 21: Runtime CLI

`cli.py` provides explicit health, validate, once, and scheduled modes without accepting secrets as command-line arguments.

## Phase 19: Unified Runtime Job

`unified_runtime.py` provides `UnifiedRuntimeJob` for one read-only end-to-end cycle. Lifecycle evaluation occurs from the screening result before the current cycle's market observations are ingested.

## Phase 18: Scheduler & Continuous Runtime

`scheduler.py` provides `ScheduledRuntime` for controlled recurring execution with configurable interval, bounded cycles, singleton protection, graceful stop, and cycle accounting.

## Phase 17: Live Market Loop

`market_loop.py` adds a bounded orchestration layer around `LiveMarketFeed`.

## Phase 15: Market Feed

`market_feed.py` provides a source-agnostic polling layer with duplicate protection.

## Phase 13: Persistent Live Paper Tracking

`paper_persistence.py` stores every paper observation in SQLite with deterministic idempotency protection.

## Phase 12: Live Validation

`live_validation.py` provides a read-only runtime validation report for configured GMGN capabilities.

## Phase 11: Production Hardening

Operational helpers provide retry, circuit breaker, database health checks, and explicit degraded status when API configuration is incomplete.

## Phase 10: Unified Wallet Lifecycle

`WalletLifecycle` connects screening, paper tracking, and dynamic watchlist promotion.

## Phase 9: Funding & Cluster Verification

Funding/cluster analysis remains conservative: missing data is not treated as clean evidence, and similar trading behavior alone does not assert common ownership.

## Phase 7: Verified GMGN Mapping

The live integration uses the official `gmgn-cli` interface rather than scraping `gmgn.ai`. Documented read-only wallet queries include portfolio stats, holdings, activity, Smart Money tracking, and market trending.

The provider does **not** fabricate evidence for source-framework layers that are not directly established by these queries. Wallet Radar / Shared Holdings / Earliest Bought and verified launch-to-entry/liquidity trade evidence remain explicit capability gaps.

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
