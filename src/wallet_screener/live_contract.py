from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


@dataclass(slots=True)
class ContractCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass(slots=True)
class LiveContractReport:
    checks: list[ContractCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(item.passed for item in self.checks)

    @property
    def failed(self) -> list[ContractCheck]:
        return [item for item in self.checks if not item.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [
                {"name": item.name, "passed": item.passed, "detail": item.detail}
                for item in self.checks
            ],
        }


class LiveContractValidator:
    """Read-only contract validator; never performs trade/signing operations."""

    def __init__(self, checks: Mapping[str, Callable[[], Any]]) -> None:
        self.checks = dict(checks)

    def run(self) -> LiveContractReport:
        report = LiveContractReport()
        for name, check in self.checks.items():
            try:
                value = check()
                ok = bool(value)
                report.checks.append(ContractCheck(name=name, passed=ok, detail="ok" if ok else "returned false"))
            except Exception as exc:
                report.checks.append(ContractCheck(name=name, passed=False, detail=f"{type(exc).__name__}: {exc}"))
        return report
