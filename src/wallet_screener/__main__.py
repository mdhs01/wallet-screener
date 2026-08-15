from __future__ import annotations

import argparse
import json
import os

from .gmgn_provider import GMGNLiveProvider
from .persistence import ScreeningStore
from .pipeline import ScreeningPipeline
from .providers import NullProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Run wallet screening pipeline")
    parser.add_argument("--provider", choices=("null", "gmgn"), default=os.getenv("WALLET_SCREENER_PROVIDER", "null"))
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--db", default=os.getenv("WALLET_SCREENER_DB", "data/wallet_screener.db"))
    args = parser.parse_args()

    provider = GMGNLiveProvider() if args.provider == "gmgn" else NullProvider()
    pipeline = ScreeningPipeline(provider=provider, store=ScreeningStore(args.db))
    report = pipeline.run(max_candidates=args.max_candidates)
    print(json.dumps({
        "run_id": report.run_id,
        "status": report.status,
        "discovered": report.discovered,
        "screened": report.screened,
        "passed": report.passed,
        "results": report.results,
        "error": report.error,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
