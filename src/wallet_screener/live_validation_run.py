from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .live_contract import LiveContractReport, LiveContractValidator


@dataclass(slots=True)
class LiveValidationRun:
    report: LiveContractReport
    output_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = self.report.to_dict()
        payload["output_path"] = str(self.output_path) if self.output_path else None
        return payload


class LiveValidationRunner:
    """Executes supplied read-only live checks and persists an auditable report."""

    def __init__(self, checks: Mapping[str, Callable[[], Any]]) -> None:
        self.validator = LiveContractValidator(checks)

    def run(self, output_path: str | Path | None = None) -> LiveValidationRun:
        report = self.validator.run()
        destination = Path(output_path) if output_path else None
        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return LiveValidationRun(report=report, output_path=destination)
