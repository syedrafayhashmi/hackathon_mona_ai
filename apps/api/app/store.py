from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import DB_PATH
from .models import RunRecord


def _connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )"""
        )


def save_run(run: RunRecord) -> None:
    with _connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO runs (id, problem_id, created_at, payload) VALUES (?, ?, ?, ?)",
            (run.id, run.problem_id, run.created_at, run.model_dump_json()),
        )


def get_run(run_id: str) -> RunRecord | None:
    with _connect() as db:
        row = db.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
    return RunRecord.model_validate_json(row["payload"]) if row else None


def list_runs() -> list[RunRecord]:
    with _connect() as db:
        rows = db.execute("SELECT payload FROM runs ORDER BY created_at DESC").fetchall()
    return [RunRecord.model_validate_json(row["payload"]) for row in rows]


def clear_runs() -> None:
    with _connect() as db:
        db.execute("DELETE FROM runs")

