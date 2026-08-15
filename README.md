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
- Phase 4 paper-tracking engine for 3–7 day validation

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

## Phase 4: Paper Tracking

`PaperTracker` is API-agnostic and never places live orders. It records hypothetical observations and evaluates the evidence needed before watchlist promotion.

The default tracking window is configurable from 3 to 7 days.

The tracker records and summarizes:

- signal timestamp and token
- wallet entry/exit and hypothetical entry/exit
- liquidity at signal
- actionable / false-signal / missed-signal status
- entry latency
- hypothetical return
- slippage
- cumulative return
- maximum drawdown

The implementation includes readiness gates for minimum observations, actionable rate, false signals, missed signals, positive average hypothetical return, and maximum drawdown. These numeric gates are implementation defaults and remain tunable; the uploaded framework itself specifies the 3–7 day tracking period and the metrics to record.

## Configuration

All Phase 3 and Phase 4 thresholds are configurable through `ScreenerConfig.manual_qa`, `ScreenerConfig.actionability`, and `ScreenerConfig.paper_track`.

## Status

Phase 0–2: foundation, schemas, configuration, provider interfaces, analytics, and layered screening.

Phase 3: manual trade sample verification engine and watchlist gate implemented.

Phase 4: paper-tracking engine implemented and exported; external API integration is intentionally deferred.

## Run

Python 3.11+

```bash
python -m src.wallet_screener
```

Run tests:

```bash
python -m pytest
```
