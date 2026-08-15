from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class HealthReport:
    status: str
    database_ok: bool
    api_configured: bool
    detail: str = ""


def check_health(db_path: str | Path, *, api_configured: bool) -> HealthReport:
    path = Path(db_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    except OSError as exc:
        return HealthReport("unhealthy", False, api_configured, str(exc))
    status = "healthy" if api_configured else "degraded"
    detail = "api credentials/endpoints are not configured" if not api_configured else ""
    return HealthReport(status, True, api_configured, detail)
