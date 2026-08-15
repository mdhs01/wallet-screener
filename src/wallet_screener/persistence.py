from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ScreeningStore:
    """Small SQLite store for screening, paper-tracking, and watchlist state."""

    def __init__(self, path: str | Path = "data/wallet_screener.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS screening_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_ts INTEGER NOT NULL,
                    finished_ts INTEGER,
                    discovered_count INTEGER NOT NULL DEFAULT 0,
                    screened_count INTEGER NOT NULL DEFAULT 0,
                    passed_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    error TEXT
                );
                CREATE TABLE IF NOT EXISTS screening_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    wallet TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    score REAL NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_ts INTEGER NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES screening_runs(id)
                );
                CREATE INDEX IF NOT EXISTS idx_screening_wallet ON screening_results(wallet);
                CREATE INDEX IF NOT EXISTS idx_screening_run ON screening_results(run_id);
                """
            )

    def start_run(self, started_ts: int) -> int:
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO screening_runs(started_ts, status) VALUES (?, ?)",
                (started_ts, "running"),
            )
            return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        *,
        finished_ts: int,
        discovered_count: int,
        screened_count: int,
        passed_count: int,
        status: str,
        error: str | None = None,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """UPDATE screening_runs
                   SET finished_ts=?, discovered_count=?, screened_count=?,
                       passed_count=?, status=?, error=?
                   WHERE id=?""",
                (finished_ts, discovered_count, screened_count, passed_count, status, error, run_id),
            )

    def save_result(self, run_id: int, wallet: str, result: dict[str, Any], created_ts: int) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO screening_results
                   (run_id, wallet, passed, stage, score, payload_json, created_ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    wallet,
                    int(bool(result.get("passed"))),
                    str(result.get("stage", "unknown")),
                    float(result.get("score", 0.0)),
                    json.dumps(result, separators=(",", ":"), sort_keys=True),
                    created_ts,
                ),
            )

    def latest_results(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload_json FROM screening_results ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]
