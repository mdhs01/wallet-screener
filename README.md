# Wallet Screener

Wallet screening engine based on the uploaded GMGN Wallet Screening Framework.

## Current scope

- Provider-agnostic architecture
- No API keys required yet
- Mock/in-memory provider for development and tests
- Layered screening pipeline
- Configurable thresholds
- Explainable scoring and rejection reasons

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Paper Track → Watchlist

## Status

Phase 0–1 implementation: foundation, schemas, configuration, provider interfaces, and screening layers.

External API integration is intentionally deferred until the engine is complete and testable.

## Run

Python 3.11+

```bash
python -m src.wallet_screener
```

Run tests:

```bash
python -m pytest
```
