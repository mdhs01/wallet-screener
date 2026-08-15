# Phase 16 — GMGN Market Source

Phase 16 adds a read-only GMGN market-data source that converts the existing GMGN CLI market response into the normalized `MarketSnapshot` contract used by the paper-tracking feed.

## Flow

`gmgn-cli market trending -> GMGNMarketSnapshotSource -> MarketSnapshot -> LiveMarketFeed -> PersistentPaperRuntime`

## Safety

This source performs no trading, signing, or wallet mutation. It only reads and normalizes market data.

## Boundary

The adapter does not invent wallet-entry, wallet-exit, actionability, or launch-time evidence when the upstream market payload does not provide it. Missing required market fields cause the row to be skipped.

The exact upstream market payload must still be validated in a runtime environment with configured GMGN credentials before this connector can be considered live-verified.
