"""Live SPF/DMARC DNS lookup. Never claimed as DKIM cryptographic verification."""
from __future__ import annotations

import os
import re
from typing import Any

_SPF_RE = re.compile(r"v=spf1\b", re.I)
_DMARC_RE = re.compile(r"v=DMARC1\b", re.I)


def _truthy(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def status() -> dict[str, Any]:
    enabled = _truthy("MAILTRACE_LIVE_DNS")
    return {
        "enabled": enabled,
        "resolver": "dnspython" if enabled else "disabled",
        "verifies_dkim_signatures": False,
        "note": "Live lookup reads published SPF/DMARC TXT records. It does not verify DKIM signatures.",
    }


def _txt(name: str, timeout: float) -> tuple[str, list[str]]:
    try:
        import dns.resolver
    except ImportError:
        return "unavailable", []
    try:
        answers = dns.resolver.resolve(name, "TXT", lifetime=timeout)
    except Exception as exc:
        name_exc = type(exc).__name__
        if name_exc in {"NXDOMAIN", "NoAnswer", "NoNameservers", "Timeout", "LifetimeTimeout"}:
            return "absent" if name_exc in {"NXDOMAIN", "NoAnswer"} else "unavailable", []
        return "unavailable", []
    out: list[str] = []
    for item in answers:
        try:
            parts = [p.decode("utf-8", "replace") if isinstance(p, bytes) else str(p) for p in item.strings]
            out.append("".join(parts))
        except Exception:
            continue
    return "ok", out


def live_check(parsed: dict[str, Any]) -> dict[str, Any]:
    domain = (parsed.get("from_domain") or parsed.get("return_domain") or "").strip().lower()
    base = {
        "enabled": _truthy("MAILTRACE_LIVE_DNS"),
        "domain": domain or None,
        "spf_txt": None,
        "dmarc_txt": None,
        "spf_published": "unavailable",
        "dmarc_published": "unavailable",
        "hop_in_spf": "not-evaluated",
        "source": "live-dns" if _truthy("MAILTRACE_LIVE_DNS") else "disabled",
        "verified_dkim": False,
        "note": "Published TXT presence only. Not cryptographic DKIM verification.",
    }
    if not base["enabled"] or not domain:
        if not domain:
            base["note"] = "No From/Return-Path domain to query."
        return base

    timeout = 2.5
    try:
        timeout = max(1.0, min(6.0, float(os.getenv("MAILTRACE_DNS_TIMEOUT", "2.5"))))
    except ValueError:
        timeout = 2.5

    spf_status, spf_all = _txt(domain, timeout)
    dmarc_status, dmarc_all = _txt(f"_dmarc.{domain}", timeout)
    spf_records = [row for row in spf_all if _SPF_RE.search(row)]
    dmarc_records = [row for row in dmarc_all if _DMARC_RE.search(row)]
    base["spf_txt"] = (spf_records[0][:300] if spf_records else None)
    base["dmarc_txt"] = (dmarc_records[0][:300] if dmarc_records else None)
    if spf_records:
        base["spf_published"] = "present"
    elif spf_status == "ok":
        base["spf_published"] = "absent"
    else:
        base["spf_published"] = spf_status
    if dmarc_records:
        base["dmarc_published"] = "present"
    elif dmarc_status == "ok":
        base["dmarc_published"] = "absent"
    else:
        base["dmarc_published"] = dmarc_status

    hop_ip = (parsed.get("origin") or {}).get("ip") or ""
    if spf_records and hop_ip and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", hop_ip):
        blob = " ".join(spf_records).lower()
        if hop_ip in blob or any(token.startswith("ip4:") and hop_ip.startswith(token[4:].split("/")[0]) for token in blob.split()):
            base["hop_in_spf"] = "mentioned"
        elif "ip4:" in blob or "include:" in blob or "a:" in blob or "mx" in blob:
            base["hop_in_spf"] = "not-in-literal-record"
        else:
            base["hop_in_spf"] = "unknown"
    return base
