"""Simple explainable fusion. Not an LLM. Not the teammates' spam pickle."""
from __future__ import annotations

from typing import Any


def fuse(parsed: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    score = 8
    label = "clean"

    auth = parsed.get("auth") or {}
    if parsed.get("gmail_wearing_title"):
        score += 28
        reasons.append("Visible From is Gmail wearing an official title.")
    if parsed.get("reply_mismatch"):
        score += 18
        reasons.append("Reply-To domain does not match From.")
    if parsed.get("return_mismatch"):
        score += 10
        reasons.append("Return-Path domain does not match From.")
    if auth.get("spf") == "fail":
        score += 22
        reasons.append("SPF fail. This server is not allowed to send as the claimed domain.")
    if auth.get("dkim") == "fail":
        score += 12
        reasons.append("DKIM fail. Signature does not match.")
    if auth.get("dmarc") == "fail":
        score += 12
        reasons.append("DMARC fail.")
    if parsed.get("lookalike"):
        score += 20
        reasons.append("Lookalike domain in the message (paypa1 / pec-edu style).")

    intel = parsed.get("intel") or []
    if any(x.get("young") for x in intel):
        young = [x["domain"] for x in intel if x.get("young")]
        score += 14
        reasons.append("Young domain in offline cache: " + ", ".join(young))
    origin = parsed.get("origin") or {}
    if origin.get("kind") == "cloud":
        score += 10
        city = origin.get("city") or "unknown"
        isp = origin.get("isp") or "cloud"
        reasons.append(f"First public hop is {isp}, {city} — cloud, not campus mail.")

    body = (parsed.get("body") or "").lower()
    if any(w in body for w in ("verify your password", "confirm your password", "login to continue")):
        score += 16
        reasons.append("Body asks for a password or login.")
    if any(w in body for w in ("wire the amount", "new bank account", "urgent payment", "change of account")):
        score += 18
        reasons.append("Invoice / payment-redirect language (BEC-style).")
    if any(w in body for w in ("urgent", "immediately", "suspended", "act now")):
        score += 8
        reasons.append("Urgency language.")

    score = max(0, min(100, score))
    if score >= 70 and any("password" in r.lower() or "lookalike" in r.lower() for r in reasons):
        label = "phish"
    elif score >= 50 and any("payment" in r.lower() or "bec" in r.lower() or "invoice" in r.lower() for r in reasons):
        label = "bec"
    elif score >= 55 and any("title" in r.lower() or "spf" in r.lower() or "reply-to" in r.lower() for r in reasons):
        label = "spoof"
    elif score >= 45:
        label = "spoof"
    else:
        label = "clean"
        if not reasons:
            reasons.append("Auth stamps look aligned. No spoof / phish cues in this sample.")

    return {
        "score": score,
        "label": label.upper(),
        "reasons": reasons[:6],
        "origin_note": "Geo is hosting city / ISP of the earliest reliable hop. Not a person's GPS.",
    }
