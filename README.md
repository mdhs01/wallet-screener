# Wallet Screener

Wallet screening engine based on the uploaded GMGN Wallet Screening Framework.

## Current scope

- Provider-agnostic architecture
- No API keys required yet
- Mock/in-memory provider for development and tests
- Layered screening pipeline
- Configurable thresholds
- Explainable scoring, rejection reasons, warnings, and layer scores
- Phase 3 automated preparation and gating for the required 15–20 trade manual review

## Screening flow

Discovery → Surface Filter → Performance → Profit Distribution → Behavior → Risk → Cross-Token → Funding/Cluster → Manual Trade Sample → Manual Review → Paper Track → Watchlist

## Phase 3: Manual Trade Verification

Before a wallet can enter the final watchlist, the engine requests a trade sample of up to 20 trades and requires at least 15 by default.

The automated QA layer checks:

- launch time vs entry time and entry latency
- entry size and liquidity-at-entry completeness
- actionable-entry rate
- transfer-in rate
- repeated trade-behavior patterns
- partial TP / residual hold / cut-loss / underwater accumulation evidence
- whether the sample is sufficiently complete for human review

The engine does **not** claim that automated checks replace the manual review described by the source framework. By default, a passing automated sample produces `manual_review_required` rather than `final_watchlist`.

## Configuration

Phase 3 thresholds are configurable through `ScreenerConfig.manual_qa` and `ScreenerConfig.actionability`.

Important defaults:

- minimum manual sample: 15 trades
- maximum sample: 20 trades
- minimum actionable rate: 50%
- maximum transfer-in rate: 20%
- minimum complete trade-data rate: 90%
- minimum repeated-behavior rate: 50%
- manual review gate: enabled

These are implementation defaults, not claims that the source framework specifies identical numeric thresholds for every manual-QA metric.

## Status

Phase 0–2: foundation, schemas, configuration, provider interfaces, analytics, and layered screening.

Phase 3: manual trade sample verification engine and watchlist gate implemented.

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
