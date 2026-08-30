"""Parse a raw .eml into headers, hops, URLs, auth flags, hash."""
from __future__ import annotations

import hashlib
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from typing import Any

IP_RE = re.compile(r"\[?(?:\d{1,3}\.){3}\d{1,3}\]?")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
RECEIVED_IP_RE = re.compile(
    r"(?:from\s+\S+\s+)?(?:\(|\[)?((?:\d{1,3}\.){3}\d{1,3})(?:\)|\])?",
    re.I,
)

# Offline demo intel only — IPs we stamp into sample .eml files.
GEO = {
    "18.184.10.20": {"city": "Frankfurt", "isp": "AWS", "kind": "cloud", "lat": 50.1109, "lon": 8.6821},
    "52.94.76.10": {"city": "Dublin", "isp": "AWS", "kind": "cloud", "lat": 53.3498, "lon": -6.2603},
    "8.8.8.8": {"city": "unknown", "isp": "public-dns", "kind": "other", "lat": None, "lon": None},
    "103.25.60.12": {"city": "Chandigarh", "isp": "campus-like", "kind": "org", "lat": 30.7333, "lon": 76.7794},
    "185.199.108.153": {"city": "unknown", "isp": "fastly", "kind": "cdn", "lat": None, "lon": None},
}


def _domain(addr: str) -> str:
    _, email_addr = parseaddr(addr or "")
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[1].lower()


def _auth_flags(msg) -> dict[str, Any]:
    blob = " ".join(
        str(v)
        for k, v in msg.items()
        if k.lower() in ("authentication-results", "received-spf", "arc-authentication-results")
    ).lower()
    def flag(name: str) -> str:
        if f"{name}=pass" in blob or f"{name} pass" in blob:
            return "pass"
        if f"{name}=fail" in blob or f"{name} fail" in blob:
            return "fail"
        if f"{name}=none" in blob:
            return "none"
        return "unknown"

    return {
        "spf": flag("spf"),
        "dkim": flag("dkim"),
        "dmarc": flag("dmarc"),
        "raw": blob[:400],
    }


def _hops(msg) -> list[dict[str, Any]]:
    received = msg.get_all("Received") or []
    hops: list[dict[str, Any]] = []
    for i, line in enumerate(received):
        ips = RECEIVED_IP_RE.findall(line) or IP_RE.findall(line)
        ip = ""
        for cand in ips:
            cand = cand.strip("[]")
            if cand.startswith("127.") or cand.startswith("10.") or cand.startswith("192.168."):
                continue
            ip = cand
            break
        geo = GEO.get(ip) if ip else None
        if not geo:
            geo = {"city": "unknown", "isp": "unknown", "kind": "internal" if not ip else "unknown", "lat": None, "lon": None}
        hops.append(
            {
                "index": i,
                "raw": " ".join(line.split())[:240],
                "ip": ip,
                **geo,
            }
        )
    return hops


def earliest_public(hops: list[dict[str, Any]]) -> dict[str, Any] | None:
    public = [h for h in hops if h.get("ip") and h.get("kind") != "internal"]
    if not public:
        return hops[-1] if hops else None
    return public[-1]


def parse_eml(data: bytes, filename: str = "upload.eml") -> dict[str, Any]:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    from_raw = msg.get("From", "") or ""
    reply_raw = msg.get("Reply-To", "") or ""
    return_raw = msg.get("Return-Path", "") or ""
    display, from_addr = parseaddr(from_raw)
    body = ""
    attachments: list[dict[str, Any]] = []
    if msg.is_multipart():
        for part in msg.walk():
            disposition = part.get_content_disposition()
            filename_part = part.get_filename()
            if disposition == "attachment" or filename_part:
                payload = part.get_payload(decode=True)
                if payload is None:
                    raw_payload = part.get_payload()
                    payload = raw_payload.encode("utf-8", errors="replace") if isinstance(raw_payload, str) else bytes(raw_payload or b"")
                attachments.append(
                    {
                        "filename": filename_part or "unnamed-attachment",
                        "content_type": part.get_content_type(),
                        "size": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
            elif part.get_content_type() == "text/plain":
                try:
                    body += str(part.get_content())
                except Exception:
                    pass
    else:
        try:
            body = str(msg.get_content())
        except Exception:
            body = ""

    urls = URL_RE.findall(body) + URL_RE.findall(from_raw)
    hops = _hops(msg)
    origin = earliest_public(hops)
    from_dom = _domain(from_raw)
    reply_dom = _domain(reply_raw)
    return_dom = _domain(return_raw)
    lookalike = bool(re.search(r"paypa1|pec-edu\.in|g00gle|micr0soft", (body + " ".join(urls)).lower()))

    return {
        "filename": filename,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "subject": msg.get("Subject", "") or "",
        "from_display": display,
        "from_addr": from_addr,
        "from_domain": from_dom,
        "reply_to": reply_raw,
        "reply_domain": reply_dom,
        "return_path": return_raw,
        "return_domain": return_dom,
        "message_id": msg.get("Message-ID", "") or "",
        "body": body[:4000],
        "urls": list(dict.fromkeys(urls))[:20],
        "attachments": attachments[:20],
        "hops": hops,
        "origin": origin,
        "auth": _auth_flags(msg),
        "reply_mismatch": bool(reply_dom and from_dom and reply_dom != from_dom),
        "return_mismatch": bool(return_dom and from_dom and return_dom != from_dom),
        "lookalike": lookalike,
        "gmail_wearing_title": bool(from_addr.endswith("@gmail.com") and display and len(display) > 3),
    }
