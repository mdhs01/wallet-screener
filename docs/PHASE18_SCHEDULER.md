# Phase 18 — Scheduler & Continuous Runtime

Phase 18 adds a bounded scheduler for continuous read-only runtime execution.

## Guarantees

- singleton protection so two schedulers do not run simultaneously in-process
- configurable polling interval
- bounded cycle mode for tests and controlled deployment
- graceful stop via `stop()`
- optional circuit-breaker integration
- cycle-level success/failure accounting

The scheduler does not place orders, sign transactions, or own screening logic. It only controls invocation of an existing job such as the discovery/screening/market-feed lifecycle.

## Runtime boundary

```text
ScheduledRuntime
      ↓
existing read-only job
      ↓
screening / market feed / paper runtime
```

A persistent service manager (systemd, container supervisor, etc.) can restart the process after a crash; the application-level singleton guard prevents duplicate instances inside the same Python process.
