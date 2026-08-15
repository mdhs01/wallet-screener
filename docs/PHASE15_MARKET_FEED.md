# Phase 15 — Live Market Feed

Phase 15 adds a read-only polling layer between a market-data source and the persistent paper tracker.

## Flow

MarketSnapshotSource → MarketObservationAdapter → PersistentPaperRuntime → SQLite

## Guarantees

- no wallet signing
- no order placement
- duplicate observations are ignored by the persistent paper store
- invalid market snapshots are rejected
- source failures are reported as cycle errors instead of crashing the polling loop
- polling cadence is configurable

## Source contract

A source implements:

```python
def fetch() -> Iterable[MarketSnapshot]: ...
```

The repository currently includes `InMemoryMarketSource` for deterministic testing. A GMGN-specific market source should be added only after the exact supported market endpoint/CLI contract is verified; this phase does not invent undocumented endpoints.

## Runtime

`LiveMarketFeed.cycle()` performs one read-only ingestion cycle.

`LiveMarketFeed.run_polling(interval_seconds=..., cycles=...)` repeats cycles. Use `cycles=None` for continuous operation in a supervised process.

The feed reports:

- fetched
- accepted
- duplicates
- rejected
- errors

## Safety boundary

The feed only creates paper observations. It never executes trades.
