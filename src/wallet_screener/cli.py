from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from .health import check_health


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallet-screener")
    sub = parser.add_subparsers(dest="command", required=True)

    once = sub.add_parser("once", help="run one read-only screening cycle")
    once.add_argument("--db", default="data/wallet_screener.db")
    once.add_argument("--max-candidates", type=int, default=None)

    scheduled = sub.add_parser("scheduled", help="run scheduled read-only cycles")
    scheduled.add_argument("--db", default="data/wallet_screener.db")
    scheduled.add_argument("--interval", type=float, default=300.0)
    scheduled.add_argument("--cycles", type=int, default=None)
    scheduled.add_argument("--max-candidates", type=int, default=None)

    validate = sub.add_parser("validate", help="validate runtime configuration without trading")
    validate.add_argument("--db", default="data/wallet_screener.db")

    health = sub.add_parser("health", help="check local runtime health")
    health.add_argument("--db", default="data/wallet_screener.db")

    return parser


def _print(data: dict) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _api_configured() -> bool:
    """Return whether the minimum GMGN credential is configured in environment."""
    return bool(os.getenv("GMGN_API_KEY", "").strip())


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "health":
        report = check_health(
            db_path=Path(args.db),
            api_configured=_api_configured(),
        )
        _print(asdict(report))
        return 0 if report.status == "healthy" else 1

    # CLI is deliberately configuration/runtime-shell only in Phase 21.
    # Provider construction and credentials remain outside the core parser so
    # no secret is accepted as a command-line argument.
    if args.command == "validate":
        _print({
            "command": "validate",
            "db": args.db,
            "status": "configuration_shell_ready",
            "note": "Provider credentials are loaded from environment/configuration, not CLI arguments.",
        })
        return 0

    if args.command in {"once", "scheduled"}:
        _print({
            "command": args.command,
            "db": args.db,
            "interval": getattr(args, "interval", None),
            "cycles": getattr(args, "cycles", None),
            "max_candidates": getattr(args, "max_candidates", None),
            "status": "runtime_entrypoint_ready",
            "note": "Bind UnifiedRuntimeJob here when a concrete provider/runtime configuration is supplied.",
        })
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
