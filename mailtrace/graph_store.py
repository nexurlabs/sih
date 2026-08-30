"""In-process campaign graph: link cases that share domain, IP, or Reply-To."""
from __future__ import annotations

from typing import Any


class CampaignGraph:
    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []

    def add(self, case: dict[str, Any]) -> dict[str, Any]:
        self.cases.append(case)
        return self.links_for(case)

    def _keys(self, case: dict[str, Any]) -> set[str]:
        p = case.get("parsed") or case
        keys = set()
        for k in ("reply_domain", "from_domain", "return_domain"):
            v = (p.get(k) or "").lower()
            if v and v not in ("gmail.com", "google.com"):
                keys.add("dom:" + v)
        origin = p.get("origin") or {}
        if origin.get("ip"):
            keys.add("ip:" + origin["ip"])
        rt = (p.get("reply_to") or "").lower()
        if rt:
            keys.add("rt:" + rt)
        return keys

    def links_for(self, case: dict[str, Any]) -> dict[str, Any]:
        me = self._keys(case)
        nodes = [{"id": c["id"], "label": c["parsed"]["filename"], "score": c["fusion"]["score"]} for c in self.cases]
        edges = []
        for other in self.cases:
            if other["id"] == case["id"]:
                continue
            shared = me & self._keys(other)
            if shared:
                edges.append(
                    {
                        "from": case["id"],
                        "to": other["id"],
                        "shared": sorted(shared)[:4],
                    }
                )
        return {"nodes": nodes, "edges": edges}
