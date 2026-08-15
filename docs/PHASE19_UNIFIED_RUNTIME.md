# Phase 19 — Unified Runtime Job

`UnifiedRuntimeJob` runs one read-only end-to-end cycle:

1. discovery and wallet screening
2. lifecycle evaluation of screening results
3. market-feed ingestion into persistent paper tracking

The job aggregates screening and market-feed counters into `UnifiedRuntimeReport`.

The implementation does not place trades, sign transactions, or invent market observations. A real market source must provide valid `MarketSnapshot` values.

The lifecycle intentionally runs from the persisted screening result before market ingestion so the current cycle's new observation does not retroactively alter the screening decision that produced the candidate.
