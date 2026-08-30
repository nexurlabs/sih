"""Campaign graph via NetworkX, rebuilt from stored cases."""
from __future__ import annotations

from typing import Any

import networkx as nx


def _keys(parsed: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for k in ("reply_domain", "from_domain", "return_domain"):
        v = (parsed.get(k) or "").lower()
        if v and v not in ("gmail.com", "google.com"):
            keys.add("dom:" + v)
    origin = parsed.get("origin") or {}
    if origin.get("ip"):
        keys.add("ip:" + origin["ip"])
    rt = (parsed.get("reply_to") or "").lower()
    if "@" in rt:
        keys.add("rt:" + rt)
    return keys


def build(cases: list[dict[str, Any]]) -> dict[str, Any]:
    g = nx.Graph()
    for c in cases:
        g.add_node(c["id"], label=c["parsed"]["filename"], score=c["fusion"]["score"])
    for i, a in enumerate(cases):
        ka = _keys(a["parsed"])
        for b in cases[i + 1 :]:
            shared = sorted(ka & _keys(b["parsed"]))
            if shared:
                g.add_edge(a["id"], b["id"], shared=shared[:4])
    return {
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [
            {"from": u, "to": v, "shared": data.get("shared", [])}
            for u, v, data in g.edges(data=True)
        ],
    }
