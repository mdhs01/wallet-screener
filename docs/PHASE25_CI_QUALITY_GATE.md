# Phase 25 — CI Quality Gate

The repository now has a GitHub Actions quality gate at `.github/workflows/ci.yml`.

Checks run on pushes to `main` and pull requests targeting `main`.

The matrix covers Python 3.11 and 3.12. Each job:

1. checks out the repository;
2. installs `pytest`;
3. runs the complete `pytest` suite;
4. runs `compileall` against `src`.

The gate is intentionally deterministic and does not require GMGN credentials, network access, wallet signing, or live trading. Live provider validation remains a separate operational phase.

A green workflow indicates that the committed source passes the repository's automated test and compile checks. It does not by itself prove live API connectivity or 3–7 day paper-tracking performance.
