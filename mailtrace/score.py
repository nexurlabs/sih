"""Hybrid fusion: deterministic forensic rules plus a bounded local NLP component."""
from __future__ import annotations

from typing import Any

from mailtrace.nlp_model import analyze as nlp_analyze

BASE_SCORE = 8


def fuse(parsed: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    signals: list[dict[str, Any]] = []
    score = BASE_SCORE

    def add_signal(code: str, points: int, reason: str, source: str) -> None:
        nonlocal score
        score += points
        reasons.append(reason)
        signals.append(
            {
                "code": code,
                "points": points,
                "reason": reason,
                "source": source,
            }
        )

    auth = parsed.get("auth") or {}
    if parsed.get("gmail_wearing_title"):
        add_signal(
            "gmail_official_title",
            28,
            "Visible From is Gmail wearing an official title.",
            "message-header",
        )
    if parsed.get("reply_mismatch"):
        add_signal(
            "reply_to_mismatch",
            18,
            "Reply-To domain does not match From.",
            "message-header",
        )
    if parsed.get("return_mismatch"):
        add_signal(
            "return_path_mismatch",
            10,
            "Return-Path domain does not match From.",
            "message-header",
        )
    if auth.get("spf") == "fail":
        add_signal(
            "spf_fail",
            22,
            "SPF fail. This server is not allowed to send as the claimed domain.",
            "message-header",
        )
    if auth.get("dkim") == "fail":
        add_signal(
            "dkim_fail",
            12,
            "DKIM fail. Signature does not match.",
            "message-header",
        )
    if auth.get("dmarc") == "fail":
        add_signal("dmarc_fail", 12, "DMARC fail.", "message-header")
    if parsed.get("lookalike"):
        add_signal(
            "lookalike_domain",
            20,
            "Lookalike domain in the message (paypa1 / pec-edu style).",
            "body/url heuristic",
        )

    intel = parsed.get("intel") or []
    if any(x.get("young") for x in intel):
        young = [x["domain"] for x in intel if x.get("young")]
        add_signal(
            "young_domain",
            14,
            "Young domain in offline cache: " + ", ".join(young),
            "offline-cache",
        )
    origin = parsed.get("origin") or {}
    if origin.get("kind") == "cloud":
        city = origin.get("city") or "unknown"
        isp = origin.get("isp") or "cloud"
        add_signal(
            "cloud_origin",
            10,
            f"First public hop is {isp}, {city} — cloud, not campus mail.",
            "Received header + geo resolver",
        )

    body = (parsed.get("body") or "").lower()
    if any(w in body for w in ("verify your password", "confirm your password", "login to continue")):
        add_signal(
            "password_or_login",
            16,
            "Body asks for a password or login.",
            "body heuristic",
        )
    if any(w in body for w in ("wire the amount", "new bank account", "urgent payment", "change of account")):
        add_signal(
            "payment_redirect",
            18,
            "Invoice / payment-redirect language (BEC-style).",
            "body heuristic",
        )
    if any(w in body for w in ("urgent", "immediately", "suspended", "act now")):
        add_signal("urgency", 8, "Urgency language.", "body heuristic")

    if any((item.get("risk") == "high") for item in (parsed.get("attachments") or [])):
        add_signal(
            "dangerous_attachment",
            8,
            "Attachment has a high-risk executable or macro-type extension. Metadata only; not executed.",
            "attachment-metadata",
        )

    nlp = nlp_analyze(parsed.get("subject") or "", parsed.get("body") or "")
    forensic_score = max(0, min(100, score))
    nlp_points = int(nlp.get("points") or 0)
    if nlp_points:
        add_signal(
            f"nlp_{nlp.get('label')}",
            nlp_points,
            f"Local NLP ({nlp.get('label')}) added a bounded {nlp_points} points. Not a probability.",
            "local-nlp",
        )
    score = max(0, min(100, score))

    if score >= 70 and any("password" in r.lower() or "lookalike" in r.lower() or "credential" in r.lower() for r in reasons):
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

    uncertainty = [
        "Hybrid score is an explainable risk indicator, not a probability or accuracy percentage.",
        "Forensic rules remain the primary detector. Local NLP adds bounded points only.",
        "Authentication results are stated in the .eml headers unless a live DNS TXT check is shown separately.",
        "Origin and campaign relationships describe observed infrastructure and shared indicators, not human identity.",
    ]
    if auth.get("conflicts"):
        uncertainty.append(
            "Conflicting authentication stamps are marked conflict and do not count as a pass or fail signal."
        )

    return {
        "score": score,
        "forensic_score": forensic_score,
        "nlp": nlp,
        "label": label.upper(),
        "reasons": reasons[:8],
        "signals": signals,
        "method": "hybrid-forensic-nlp",
        "probability": None,
        "model": {
            "status": "local-tfidf-logreg",
            "validated": False,
            "note": "Local NLP is a bounded score component. Optional Groq Qwen output is advisory and does not change the score.",
        },
        "uncertainty": uncertainty,
        "origin_note": "Geo is hosting/infrastructure context for the probable earliest observed public hop, not a person's GPS or identity.",
    }
