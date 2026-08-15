# Phase 26 — Live Contract Validation

Phase 26 adds a read-only contract-validation boundary for real provider/runtime validation.

## Purpose

The deterministic CI suite must not depend on GMGN credentials or network access. Live verification therefore uses a separate contract validator that executes explicitly supplied checks and reports every failure without hiding it.

## Contract targets

A future live run should validate, at minimum:

1. GMGN CLI is installed and executable.
2. Provider configuration is valid.
3. Smart Money discovery returns a valid wallet candidate set.
4. Wallet metrics can be retrieved and normalized.
5. Holdings can be retrieved and normalized when credentials permit.
6. Recent activity can be retrieved and normalized.
7. Market data can be retrieved and normalized into `MarketSnapshot`.
8. No trade, signing, or wallet mutation operation is invoked.

## Result semantics

`LiveContractReport.passed` is true only when every configured check passes. An exception or explicit false result is recorded as a failed check.

This validator does not claim that a live test has run merely because the code exists. A real validation still requires the deployment environment, credentials, and an actual provider response.

## Safety

Phase 26 is read-only. It must not place swaps, sign transactions, submit orders, or modify wallets.
