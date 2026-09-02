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
    for key in shared:
        kind, _, value = key.partition(":")
        if kind == "rt":
            bits.append(f"Reply-To: {value}")
        elif kind == "ip":
            bits.append(f"same hop: {value}")
        elif kind == "dom":
            bits.append(f"domain: {value}")
    return " + ".join(bits) or "linked"


def _is_meaningful(shared: list[str]) -> bool:
    """Require a specific or composite indicator; never link on IP alone."""
    if any(key.startswith("rt:") for key in shared):
        return True
    non_ip = [key for key in shared if not key.startswith("ip:")]
    return len(non_ip) >= 2


def latest_by_filename(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by: dict[str, dict[str, Any]] = {}
    for c in cases:
        by[c["parsed"]["filename"]] = c
    return list(by.values())


def build(cases: list[dict[str, Any]], focus_id: str | None = None) -> dict[str, Any]:
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
            if _is_meaningful(shared):
                g.add_edge(
                    a["id"],
                    b["id"],
                    shared=shared[:6],
                    caption=_edge_caption(shared),
                    strength="strong" if any(key.startswith("rt:") for key in shared) else "composite",
                    relation="campaign-candidate",
                )
    if focus_id is not None:
        if focus_id in g:
            visible = {focus_id, *g.neighbors(focus_id)}
            g = g.subgraph(visible).copy()
        else:
            g = nx.Graph()
    return {
        "note": "Shared indicators form a campaign candidate; they do not prove common control, identity, or responsibility.",
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [
            {
                "from": u,
                "to": v,
                "shared": data.get("shared", []),
                "caption": data.get("caption", "linked"),
                "strength": data.get("strength", "unknown"),
                "relation": data.get("relation", "campaign-candidate"),
            }
            for u, v, data in g.edges(data=True)
        ],
    }
