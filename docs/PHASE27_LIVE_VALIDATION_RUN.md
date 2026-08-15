# Phase 27 — Actual Live Read-Only Validation Run

Phase 27 provides `LiveValidationRunner`, which executes explicitly supplied read-only capability checks and optionally persists an auditable JSON report.

## What this phase does

- runs the Phase 26 live contract checks in a deployment environment
- records each capability as pass/fail with detail
- persists the complete report to JSON when an output path is provided
- keeps live validation separate from deterministic CI
- has no trade, signing, or wallet-mutation capability

## Required live environment

The actual run requires the deployment environment to provide the configured `gmgn-cli` runtime and any credentials required by the selected read-only GMGN operations.

The repository itself does not contain or request the user's API key. Do not commit secrets.

## Evidence rule

A repository implementation is not considered live-verified merely because the runner exists. Phase 27 is only marked **LIVE VERIFIED** after a real environment produces a report where all required checks pass.

Until then the state is **IMPLEMENTED / LIVE RUN PENDING**.

## Example integration shape

```python
from wallet_screener.live_validation_run import LiveValidationRunner

runner = LiveValidationRunner({
    "gmgn_cli_available": check_cli,
    "smart_money_discovery": check_discovery,
    "wallet_metrics": check_wallet_metrics,
    "holdings": check_holdings,
    "activity": check_activity,
    "market_source": check_market_source,
})
result = runner.run("data/live_validation.json")
print(result.to_dict())
```
