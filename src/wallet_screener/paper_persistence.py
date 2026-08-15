from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .paper_tracking import PaperObservation, PaperTrackSummary, PaperTracker


class PaperObservationStore:
    """SQLite persistence for paper observations with idempotent inserts."""

    def __init__(self, path: str | Path = "data/wallet_screener.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS paper_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_key TEXT NOT NULL UNIQUE,
                    wallet TEXT NOT NULL,
                    token TEXT NOT NULL,
                    signal_ts INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_ts INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_paper_wallet ON paper_observations(wallet);
                CREATE INDEX IF NOT EXISTS idx_paper_signal_ts ON paper_observations(signal_ts);
                """
            )

    @staticmethod
    def key(observation: PaperObservation) -> str:
        return "|".join(
            [
                observation.wallet,
                observation.token,
                str(observation.signal_ts),
                str(observation.hypothetical_entry_ts or ""),
                str(observation.hypothetical_entry_price),
            ]
        )

    def add(self, observation: PaperObservation, created_ts: int) -> bool:
        key = self.key(observation)
        payload = json.dumps(asdict(observation), separators=(",", ":"), sort_keys=True)
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT OR IGNORE INTO paper_observations
                (observation_key, wallet, token, signal_ts, payload_json, created_ts)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, observation.wallet, observation.token, observation.signal_ts, payload, created_ts),
            )
            return cursor.rowcount == 1

    def observations(self, wallet: str) -> list[PaperObservation]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload_json FROM paper_observations WHERE wallet=? ORDER BY signal_ts ASC, id ASC",
                (wallet,),
            ).fetchall()
        return [PaperObservation(**json.loads(row["payload_json"])) for row in rows]

    def count_observations(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COUNT(*) AS count FROM paper_observations").fetchone()
        return int(row["count"] if row else 0)

    def oldest_observation_ts(self) -> int | None:
        with self._connect() as db:
            row = db.execute("SELECT MIN(signal_ts) AS oldest FROM paper_observations").fetchone()
        return int(row["oldest"]) if row and row["oldest"] is not None else None

    def summary(self, wallet: str, tracker: PaperTracker) -> PaperTrackSummary:
        tracker_for_wallet = PaperTracker(
            min_days=tracker.min_days,
            max_days=tracker.max_days,
            min_observations=tracker.min_observations,
            min_actionable_rate=tracker.min_actionable_rate,
            max_false_signal_rate=tracker.max_false_signal_rate,
            max_missed_rate=tracker.max_missed_rate,
            min_positive_expectancy_pct=tracker.min_positive_expectancy_pct,
            max_drawdown_pct=tracker.max_drawdown_pct,
        )
        for observation in self.observations(wallet):
            tracker_for_wallet.add(observation)
        return tracker_for_wallet.summarize(wallet)
