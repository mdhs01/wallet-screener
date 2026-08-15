# Phase 20 — Scheduled Unified Runtime

Phase 20 composes `UnifiedRuntimeJob` with `ScheduledRuntime` so the complete read-only wallet-screener lifecycle can run on a recurring schedule.

## Flow

```text
ScheduledRuntime
      ↓
UnifiedRuntimeJob
      ├─ Discovery / Screening
      ├─ Lifecycle evaluation
      └─ Market feed / Paper tracking
             ↓
          SQLite
```

The scheduler remains responsible only for timing, singleton protection, graceful stop, and cycle accounting. Business logic stays inside `UnifiedRuntimeJob`.

## Safety

This phase is read-only. It does not place orders, sign transactions, execute swaps, or perform live trading.

## Recovery

A failed cycle is recorded by the scheduler and does not terminate the scheduler process. The next scheduled cycle can run again. Singleton protection prevents overlapping local runtime instances.
