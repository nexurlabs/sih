"""SQLite case store."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB = Path(__file__).resolve().parents[1] / "data" / "mailtrace.db"


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            filename TEXT,
            sha256 TEXT,
            payload TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    con.commit()
    return con


def save_case(case: dict[str, Any]) -> None:
    con = connect()
    con.execute(
        "INSERT OR REPLACE INTO cases (id, filename, sha256, payload) VALUES (?, ?, ?, ?)",
        (
            case["id"],
            case["parsed"]["filename"],
            case["parsed"]["sha256"],
            json.dumps(case),
        ),
    )
    con.commit()
    con.close()


def load_case(case_id: str) -> dict[str, Any] | None:
    con = connect()
    row = con.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
    con.close()
    return json.loads(row["payload"]) if row else None


def all_cases() -> list[dict[str, Any]]:
    con = connect()
    rows = con.execute("SELECT payload FROM cases ORDER BY created_at").fetchall()
    con.close()
    return [json.loads(r["payload"]) for r in rows]


def clear_cases() -> None:
    con = connect()
    con.execute("DELETE FROM cases")
    con.commit()
    con.close()
