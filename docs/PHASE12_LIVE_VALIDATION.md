# Phase 12 — Live Validation & Runtime Integration

Phase 12 verifies the runtime path without placing live trades.

## Validation sequence

1. Validate provider capabilities.
2. Run real GMGN discovery through the configured provider.
3. Select a discovered wallet only when discovery returns real data.
4. Fetch wallet metrics, holdings, and recent activity.
5. Confirm the responses map into the internal provider contract.
6. Run the normal screening pipeline only after provider checks pass.

## Safety boundary

This phase is read-only. No swap/order execution is introduced. An empty discovery result is treated as **not live-validated**, not as success.

## Readiness

The live validation report is ready only when provider capabilities, discovery, wallet metrics, holdings, and activity checks all pass and at least one live wallet was observed.

API credentials remain environment-only and are never stored in source control.
