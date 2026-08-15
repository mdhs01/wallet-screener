# Phase 23 — Observability

Phase 23 adds provider-neutral operational visibility without changing screening semantics.

## Structured logging

`configure_logging()` installs a JSON formatter suitable for systemd/journal or log aggregation. Events include timestamp, level, logger, message, and structured context.

## Metrics

`RuntimeMetrics` provides thread-safe in-process counters, gauges, and timing observations. `Observability` exposes standard runtime counters for cycles, errors, market snapshots, accepted paper observations, duplicates, and rejected observations.

The metrics layer is intentionally dependency-free. Export to Prometheus or another monitoring system can be added later without changing the screening engine.

## Safety

This phase does not add trading, wallet signing, or external alert side effects. It only records operational state.
