"""Campaign graph via NetworkX. One node per filename. Slide-readable labels."""
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


def _short(filename: str) -> str:
    name = (filename or "").replace(".eml", "").replace("_", " ")
    return name


def _edge_caption(shared: list[str]) -> str:
    bits = []
    if any(s.startswith("rt:") for s in shared):
        bits.append("Reply-To")
    if any(s.startswith("ip:") for s in shared):
        bits.append("same hop")
    if any(s.startswith("dom:") for s in shared):
        bits.append("domain")
    return " + ".join(bits) or "linked"


def latest_by_filename(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by: dict[str, dict[str, Any]] = {}
    for c in cases:
        by[c["parsed"]["filename"]] = c
    return list(by.values())


def build(cases: list[dict[str, Any]]) -> dict[str, Any]:
    cases = latest_by_filename(cases)
    g = nx.Graph()
    for c in cases:
        g.add_node(
            c["id"],
            label=_short(c["parsed"]["filename"]),
            score=c["fusion"]["score"],
        )
    for i, a in enumerate(cases):
        ka = _keys(a["parsed"])
        for b in cases[i + 1 :]:
            shared = sorted(ka & _keys(b["parsed"]))
            if shared:
                g.add_edge(a["id"], b["id"], shared=shared[:4], caption=_edge_caption(shared))
    return {
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [
            {
                "from": u,
                "to": v,
                "shared": data.get("shared", []),
                "caption": data.get("caption", "linked"),
            }
            for u, v, data in g.edges(data=True)
        ],
    }
