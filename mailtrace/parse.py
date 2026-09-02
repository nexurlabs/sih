"""Parse a raw .eml into headers, hops, URLs, auth flags, hash."""
from __future__ import annotations

import hashlib
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from html.parser import HTMLParser
from typing import Any

from mailtrace.geo import lookup_ip

IP_RE = re.compile(r"\[?(?:\d{1,3}\.){3}\d{1,3}\]?")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
RECEIVED_IP_RE = re.compile(
    r"(?:from\s+\S+\s+)?(?:\(|\[)?((?:\d{1,3}\.){3}\d{1,3})(?:\)|\])?",
    re.I,
)
HREF_RE = re.compile(r"""href\s*=\s*['"](https?://[^'"]+)['"]""", re.I)
DANGEROUS_EXT = {
    ".exe", ".scr", ".js", ".vbs", ".iso", ".hta", ".bat", ".cmd",
    ".ps1", ".dll", ".jar", ".docm", ".xlsm", ".lnk", ".com", ".msi",
}


class _HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.urls: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip += 1
        href = dict(attrs).get("href") or ""
        if tag == "a" and href.lower().startswith("http"):
            self.urls.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def _domain(addr: str) -> str:
    _, email_addr = parseaddr(addr or "")
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[1].lower()


def _auth_flags(msg) -> dict[str, Any]:
    observed: dict[str, list[str]] = {"spf": [], "dkim": [], "dmarc": []}
    raw_lines: list[str] = []
    status_re = re.compile(
        r"\b(spf|dkim|dmarc)\s*=\s*"
        r"(pass|fail|none|neutral|softfail|temperror|permerror)\b",
        re.I,
    )
    received_spf_re = re.compile(
        r"^\s*(pass|fail|none|neutral|softfail|temperror|permerror)\b", re.I
    )
    for key, value in msg.raw_items():
        if key.lower() not in ("authentication-results", "received-spf", "arc-authentication-results"):
            continue
        line = f"{key}: {value}"
        raw_lines.append(" ".join(line.split()))
        if key.lower() == "received-spf":
            match = received_spf_re.search(str(value))
            if match:
                observed["spf"].append(match.group(1).lower())
            continue
        for match in status_re.finditer(str(value)):
            observed[match.group(1).lower()].append(match.group(2).lower())

    def flag(name: str) -> str:
        statuses = list(dict.fromkeys(observed[name]))
        if not statuses:
            return "unknown"
        if len(statuses) > 1:
            return "conflict"
        return statuses[0]

    conflicts = [name for name in observed if flag(name) == "conflict"]

    return {
        "spf": flag("spf"),
        "dkim": flag("dkim"),
        "dmarc": flag("dmarc"),
        "raw": " ".join(raw_lines)[:400],
        "observed": observed,
        "conflicts": conflicts,
        "source": "message-header" if raw_lines else "none-present",
        "verification_mode": "header-stated",
        "verified": False,
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
        geo = lookup_ip(ip) if ip else lookup_ip("")
        hops.append(
            {
                "index": i,
                "raw": " ".join(line.split())[:240],
                **geo,
                "ip": ip or geo.get("ip", ""),
            }
        )
    return hops


def earliest_public(hops: list[dict[str, Any]]) -> dict[str, Any] | None:
    public = [h for h in hops if h.get("ip") and h.get("kind") != "internal"]
    if not public:
        return hops[-1] if hops else None
    return public[-1]


def _alignment(from_domain: str, reply_domain: str, return_domain: str) -> dict[str, str]:
    def compare(other: str) -> str:
        if not from_domain or not other:
            return "unknown"
        return "aligned" if other == from_domain else "mismatch"

    from_reply = compare(reply_domain)
    from_return = compare(return_domain)
    if "mismatch" in (from_reply, from_return):
        overall = "mismatch"
    elif from_reply == "aligned" and from_return == "aligned":
        overall = "aligned"
    else:
        overall = "unknown"
    return {
        "from_reply_to": from_reply,
        "from_return_path": from_return,
        "overall": overall,
    }


def _attachment_risk(filename: str, content_type: str) -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    if any(name.endswith(ext) for ext in DANGEROUS_EXT):
        return "high"
    if "javascript" in ctype or "executable" in ctype:
        return "high"
    return "low"


def _html_parts(raw: str) -> tuple[str, list[str]]:
    parser = _HTMLText()
    try:
        parser.feed(raw)
        parser.close()
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw), HREF_RE.findall(raw)
    return " ".join(parser.parts), parser.urls


def parse_eml(data: bytes, filename: str = "upload.eml") -> dict[str, Any]:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    header_end = min(
        [i for i in (data.find(b"\r\n\r\n"), data.find(b"\n\n")) if i >= 0],
        default=len(data),
    )
    raw_headers = data[:header_end].decode("utf-8", errors="replace")[:12000]
    from_raw = msg.get("From", "") or ""
    reply_raw = msg.get("Reply-To", "") or ""
    return_raw = msg.get("Return-Path", "") or ""
    display, from_addr = parseaddr(from_raw)
    body = ""
    html_body = ""
    attachments: list[dict[str, Any]] = []
    html_urls: list[str] = []
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
                        "risk": _attachment_risk(filename_part or "", part.get_content_type()),
                    }
                )
            elif part.get_content_type() == "text/plain":
                try:
                    body += str(part.get_content())
                except Exception:
                    pass
            elif part.get_content_type() == "text/html":
                try:
                    raw_html = str(part.get_content())
                except Exception:
                    raw_html = ""
                html_body += raw_html
                text, urls = _html_parts(raw_html)
                body += ("\n" + text if body else text)
                html_urls.extend(urls)
    else:
        try:
            content = str(msg.get_content())
        except Exception:
            content = ""
        if (msg.get_content_type() or "").lower() == "text/html":
            html_body = content
            text, urls = _html_parts(content)
            body = text
            html_urls.extend(urls)
        else:
            body = content

    urls = URL_RE.findall(body) + URL_RE.findall(from_raw) + URL_RE.findall(html_body) + html_urls
    hops = _hops(msg)
    origin = earliest_public(hops)
    if origin:
        origin = {
            **origin,
            "confidence": "heuristic",
            "selection_method": "last public Received entry in parsed header order",
            "interpretation": "hosting/infrastructure context",
        }
    else:
        origin = {
            "ip": "",
            "city": "unknown",
            "isp": "unknown",
            "kind": "unknown",
            "lat": None,
            "lon": None,
            "source": "Received headers + geo resolver",
            "status": "unknown",
            "confidence": "unknown",
            "selection_method": "no public Received entry observed",
            "interpretation": "hosting/infrastructure context",
        }
    from_dom = _domain(from_raw)
    reply_dom = _domain(reply_raw)
    return_dom = _domain(return_raw)
    reply_mismatch = bool(reply_dom and from_dom and reply_dom != from_dom)
    return_mismatch = bool(return_dom and from_dom and return_dom != from_dom)
    lookalike = bool(re.search(r"paypa1|pec-edu\.in|g00gle|micr0soft", (body + " ".join(urls)).lower()))

    return {
        "filename": filename,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "raw_headers": raw_headers,
        "provenance": {
            "input": "local-upload",
            "parser": "Python email BytesParser",
            "hash_algorithm": "SHA-256",
        },
        "uncertainty": [
            "Authentication values are stated in message headers; no live DNS or independent DKIM verification unless live_auth is present.",
            "Earliest public hop is a heuristic from Received headers.",
            "Hosting context is not a person's location or identity.",
        ],
        "subject": msg.get("Subject", "") or "",
        "from_display": display,
        "from_addr": from_addr,
        "from_domain": from_dom,
        "reply_to": reply_raw,
        "reply_domain": reply_dom,
        "return_path": return_raw,
        "return_domain": return_dom,
        "message_id": msg.get("Message-ID", "") or "",
        "alignment": _alignment(from_dom, reply_dom, return_dom),
        "body": body[:4000],
        "html_present": bool(html_body),
        "urls": list(dict.fromkeys(urls))[:20],
        "attachments": attachments[:20],
        "hops": hops,
        "origin": origin,
        "auth": _auth_flags(msg),
        "reply_mismatch": reply_mismatch,
        "return_mismatch": return_mismatch,
        "lookalike": lookalike,
        "gmail_wearing_title": bool(from_addr.endswith("@gmail.com") and display and len(display) > 3),
    }
