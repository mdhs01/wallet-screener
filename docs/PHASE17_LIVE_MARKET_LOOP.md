# Phase 17 — Live Market Loop

Phase 17 connects the existing market source, observation adapter, and persistent paper runtime into a bounded orchestration loop.

```text
Market Source
    ↓
MarketSnapshot
    ↓
LiveMarketFeed
    ↓
MarketObservationAdapter
    ↓
PersistentPaperRuntime
    ↓
SQLite
```

`LiveMarketLoop` intentionally runs a bounded number of cycles. This makes integration testing deterministic and prevents this phase from silently creating an unbounded background process.

## Scope

- read-only market observation ingestion
- polling interval configuration
- duplicate accounting
- rejected observation accounting
- provider error accounting
- persistent paper observations

## Explicitly out of scope

- live orders
- wallet signing
- swaps
- trade execution
- claims of live verification without a configured real market source

A real GMGN source can be passed through `LiveMarketFeed` once the runtime has valid credentials and an upstream payload contract.
