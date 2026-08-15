# API Integration Layer

Phase 6 introduces a provider-neutral transport and adapter layer. No API key or undocumented endpoint is required yet.

## Layers

```text
Provider config
    ↓
ApiClient (retry / rate limit / cache / timeout)
    ↓
Provider adapters
    ├── GMGNAdapter
    ├── SolanaRpcClient
    └── SolscanAdapter
    ↓
NormalizedWallet / normalized provider payloads
    ↓
WalletDataProvider / screening engine
```

## Design rules

1. Screening logic must not depend on provider-specific JSON.
2. Endpoint paths must come from the verified provider contract; they are not invented in this repository.
3. API credentials belong in environment variables, never source code.
4. GET responses may use short TTL caching to reduce duplicate reads.
5. 429/5xx and transient transport failures use bounded retries with exponential backoff.
6. Rate limiting happens before every outbound request.
7. Provider adapters convert response shapes into the internal models consumed by the screener.

## Pending endpoint mapping

The following GMGN operations still require verified endpoint documentation before they are enabled:

- discovery
- wallet metrics
- current holdings
- trade sample
- cross-token / radar evidence
- funding / cluster evidence

The same rule applies to Solscan REST endpoints used for explorer verification.
