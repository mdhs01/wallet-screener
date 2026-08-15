# Phase 9 — Funding & Cluster Verification

Phase 9 adds a conservative funding/cluster evidence layer for Solana wallets.

## Goal

The source framework requires funding source and cluster analysis so multiple wallets with the same funding and timing are not treated as independent signals.

## Components

- `cluster_analysis.py`: deterministic evidence model over normalized funding observations.
- `funding_verifier.py`: collects recent Solana transaction evidence through JSON-RPC.
- `cluster_provider.py`: decorates an existing `WalletDataProvider` and exposes funding evidence through `get_funding_cluster()`.

## Evidence model

The analyzer records:

- direct funders
- shared funders across the supplied wallet universe
- linked wallets
- synchronized funding links
- cluster size
- independence score
- explicit warnings

The model is deliberately conservative. Missing evidence is not turned into a clean result, and no cluster is inferred merely because two wallets share a token or trade at similar times.

## RPC behavior

The verifier uses:

- `getSignaturesForAddress`
- `getTransaction` with `jsonParsed`

It currently extracts positive native-balance deltas and identifies the largest negative account-balance delta in the same transaction as a candidate funder.

This is evidence, not proof of common ownership. Further attribution should combine explorer data, token transfers, timing, and broader transaction context before any operational decision.

## Integration

Use `FundingAwareProvider(base_provider, verifier)` around the live provider before passing it to `WalletScreener` or `ScreeningPipeline`.

No live API keys or RPC credentials are stored in source control.
