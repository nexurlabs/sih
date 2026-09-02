"""Local privacy helpers for masked views and opt-in evidence retention."""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

EMAIL_RE = re.compile(
    r"\b[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+\b",
    re.IGNORECASE,
)


def mask_email_address(value: str) -> str:
    local, separator, domain = value.rpartition("@")
    if not separator or not local or not domain:
        return "***"
    return f"{local[0]}***@{domain}"


def mask_text(value: str) -> str:
    return EMAIL_RE.sub(lambda match: mask_email_address(match.group(0)), value or "")


def masked_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted display copy without changing stored evidence."""
    masked = deepcopy(case)
    parsed = masked.get("parsed") or {}
    for key in ("from_addr", "reply_to", "return_path", "raw_headers", "body"):
        if key in parsed:
            parsed[key] = mask_text(str(parsed[key]))
    return masked
