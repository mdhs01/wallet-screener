from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationCheck:
    name: str
    passed: bool
    severity: str = "info"
    details: str = ""


@dataclass(slots=True)
class LiveValidationReport:
    provider: str
    checks: list[ValidationCheck] = field(default_factory=list)
    live: bool = False
    ready: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def passed_checks(self) -> int:
        return sum(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> int:
        return sum(not check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "checks": [check.__dict__ for check in self.checks],
            "live": self.live,
            "ready": self.ready,
            "notes": self.notes,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
        }


def validate_gmgn_provider(provider: Any) -> LiveValidationReport:
    report = LiveValidationReport(provider="gmgn")
    try:
        capabilities = provider.capabilities
        report.checks.append(
            ValidationCheck(
                "provider_capabilities", bool(capabilities.get("discovery")), details=str(capabilities)
            )
        )
        wallets = provider.discover_wallets()
        report.checks.append(
            ValidationCheck("discovery", isinstance(wallets, list), details=f"wallets={len(wallets)}")
        )
        if wallets:
            address = wallets[0]
            metrics = provider.get_wallet_metrics(address)
            holdings = provider.get_current_holdings(address)
            trades = provider.get_trade_sample(address, limit=20)
            report.checks.append(ValidationCheck("wallet_metrics", isinstance(metrics, dict), details=address))
            report.checks.append(ValidationCheck("holdings", isinstance(holdings, list), details=f"rows={len(holdings)}"))
            report.checks.append(ValidationCheck("activity", isinstance(trades, list), details=f"rows={len(trades)}"))
            report.live = True
        else:
            report.notes.append("No live wallet candidates returned; provider is configured but discovery returned empty.")
    except Exception as exc:  # pragma: no cover - runtime integration path
        report.checks.append(ValidationCheck("runtime", False, severity="error", details=str(exc)))
        report.notes.append("Live validation failed before all checks could complete.")

    required = {"provider_capabilities", "discovery", "wallet_metrics", "holdings", "activity"}
    passed_names = {check.name for check in report.checks if check.passed}
    report.ready = required.issubset(passed_names) and report.live
    return report
