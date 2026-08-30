"""Offline domain intel. No live WHOIS at demo time."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CACHE = Path(__file__).resolve().parents[1] / "data" / "whois_cache.json"


def lookup_domains(*domains: str) -> list[dict[str, Any]]:
    data = json.loads(CACHE.read_text()) if CACHE.is_file() else {}
    out = []
    seen = set()
    for d in domains:
        d = (d or "").lower().strip()
        if not d or d in seen:
            continue
        seen.add(d)
        row = data.get(d, {"age_days": None, "registrar": "unknown", "note": "not in offline cache"})
        young = isinstance(row.get("age_days"), int) and row["age_days"] < 30
        out.append({"domain": d, **row, "young": young})
    return out
