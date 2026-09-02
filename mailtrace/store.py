"""SQLite case store."""
from __future__ import annotations

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB = Path(__file__).resolve().parents[1] / "data" / "mailtrace.db"
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "data" / "evidence"


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence_record(
    case: dict[str, Any],
    raw_bytes: bytes,
    retention_days: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if retention_days is not None and (not isinstance(retention_days, int) or retention_days < 0):
        raise ValueError("retention_days must be a non-negative integer")
    expected = case["parsed"]["sha256"]
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if actual != expected:
        raise ValueError("raw evidence hash does not match parsed SHA-256")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{actual}.eml"
    path.write_bytes(raw_bytes)
    now_dt = now or datetime.now(timezone.utc)
    now_text = now_dt.isoformat()
    expires_at = (
        (now_dt + timedelta(days=retention_days)).isoformat()
        if retention_days is not None
        else None
    )
    return {
        "filename": case["parsed"]["filename"],
        "sha256": actual,
        "size": len(raw_bytes),
        "hash_algorithm": "SHA-256",
        "storage_key": path.name,
        "stored": True,
        "retention": {
            "days": retention_days,
            "expires_at": expires_at,
            "policy": "caller-configured; no default retention period",
        },
        "custody_events": [
            {"action": "received", "actor": "local-demo", "at": now_text},
            {"action": "hashed", "actor": "local-demo", "at": now_text},
            {"action": "stored", "actor": "local-demo", "at": now_text},
        ],
        "note": "Local prototype evidence trace; not legal-grade chain of custody.",
    }


def save_case(
    case: dict[str, Any],
    raw_bytes: bytes | None = None,
    retention_days: int | None = None,
    now: datetime | None = None,
) -> None:
    if raw_bytes is not None:
        case["evidence"] = _evidence_record(case, raw_bytes, retention_days, now)
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


def evidence_path(case: dict[str, Any]) -> Path | None:
    evidence = case.get("evidence") or {}
    storage_key = evidence.get("storage_key")
    if not storage_key or Path(storage_key).name != storage_key:
        return None
    path = EVIDENCE_DIR / storage_key
    if not path.is_file():
        return None
    expected = (case.get("parsed") or {}).get("sha256")
    if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        return None
    return path


def purge_expired(now: datetime | None = None) -> list[str]:
    now_dt = now or datetime.now(timezone.utc)
    removed: list[str] = []
    con = connect()
    rows = con.execute("SELECT id, payload FROM cases").fetchall()
    for row in rows:
        case = json.loads(row["payload"])
        evidence = case.get("evidence") or {}
        expires_at = (evidence.get("retention") or {}).get("expires_at")
        if not expires_at:
            continue
        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            continue
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry > now_dt:
            continue
        storage_key = evidence.get("storage_key")
        if storage_key and Path(storage_key).name == storage_key:
            path = EVIDENCE_DIR / storage_key
            if path.is_file():
                path.unlink()
        evidence["stored"] = False
        evidence["deleted_at"] = now_dt.isoformat()
        evidence.setdefault("custody_events", []).append(
            {"action": "deleted", "actor": "local-demo", "at": now_dt.isoformat()}
        )
        case["evidence"] = evidence
        con.execute("UPDATE cases SET payload = ? WHERE id = ?", (json.dumps(case), row["id"]))
        removed.append(row["id"])
    con.commit()
    con.close()
    return removed


def all_cases() -> list[dict[str, Any]]:
    con = connect()
    rows = con.execute("SELECT payload FROM cases ORDER BY created_at").fetchall()
    con.close()
    return [json.loads(r["payload"]) for r in rows]


def clear_cases() -> None:
    con = connect()
    rows = con.execute("SELECT payload FROM cases").fetchall()
    storage_keys = {
        (json.loads(row["payload"]).get("evidence") or {}).get("storage_key")
        for row in rows
    }
    con.execute("DELETE FROM cases")
    con.commit()
    con.close()
    for storage_key in storage_keys:
        if not storage_key or Path(storage_key).name != storage_key:
            continue
        try:
            (EVIDENCE_DIR / storage_key).unlink()
        except FileNotFoundError:
            pass
