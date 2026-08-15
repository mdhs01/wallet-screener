# Wallet Screener

Wallet screening engine based on the uploaded GMGN Wallet Screening Framework.

## Current scope

- Provider/API-agnostic architecture
- No API keys required yet
- Mock/in-memory provider for development and tests
- Tunable layered screening pipeline
- Explainable scores, warnings, and rejection reasons
- Current-holdings conviction analysis
- 15–20 trade behavior sample support
- Profit distribution and daily profit-series analysis
- Holding-time consistency and winner/loser behavior
- 7D vs 30D divergence detection
- Funding/cluster independence checks
- Cross-token repeatability scoring
- Style and public-crowding checks
- Separate actionability score

## Screening flow

Discovery → Surface Filter → Realized Performance → Profit Distribution → Holding Behavior → Risk/Phishing → Cross-Token → Funding/Cluster → 7D/30D Consistency → Conviction/Style → Actionability → Final Score

The later stages for manual QA, 3–7 day paper tracking, watchlist persistence, and weekly revalidation will be implemented after the core deep screener is stable.

## Phase 2

Phase 2 expands the engine around the framework's key principle: realized performance is necessary but not sufficient. The screener now treats distribution, behavior, current conviction, network independence, cross-token consistency, style match, crowding, and actionability as separate evidence.

Thresholds remain configurable so the system can be tuned later without rewriting the screening engine.

## API strategy

External API integration is intentionally deferred. Provider interfaces are the boundary for GMGN, Solana RPC, Solscan/Etherscan, or future data sources. The screening engine must remain usable with fixture/mock data before real API credentials are added.

## Run

Python 3.11+

```bash
python -m src.wallet_screener
```

Run tests:

```bash
python -m pytest
```
