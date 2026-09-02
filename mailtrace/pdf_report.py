"""One-page forensic PDF. Hash of the .eml, not a blockchain."""
from __future__ import annotations

from pathlib import Path
import textwrap
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "data" / "reports"


def write_pdf(case: dict[str, Any]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{case['id']}.pdf"
    p = case["parsed"]
    f = case["fusion"]
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    left = 18 * mm
    top = h - 18 * mm
    bottom = 18 * mm
    y = top

    def new_page() -> None:
        nonlocal y
        c.showPage()
        y = top

    def write_lines(value: Any, size: int = 9, font: str = "Times-Roman", gap: float = 4.5) -> None:
        nonlocal y
        text = str(value if value is not None else "") or "-"
        lines = textwrap.wrap(text, width=105, break_long_words=True, break_on_hyphens=False) or [""]
        needed = len(lines) * gap
        if y - needed < bottom:
            new_page()
        c.setFont(font, size)
        for line in lines:
            c.drawString(left, y, line)
            y -= gap

    def heading(value: str) -> None:
        nonlocal y
        if y - 8 * mm < bottom:
            new_page()
        y -= 2 * mm
        c.setFont("Times-Bold", 11)
        c.drawString(left, y, value)
        y -= 5 * mm

    def field(label: str, value: Any, font: str = "Courier", size: int = 8) -> None:
        write_lines(f"{label}: {value if value not in (None, '') else 'unknown'}", size, font, 4.2)

    c.setFont("Times-Bold", 18)
    c.drawString(left, y, "MailTrace case file")
    y -= 8 * mm
    write_lines(f"id {case['id']}   {f.get('label', 'UNKNOWN')}   score {f.get('score', '?')}", 9, "Courier", 5)
    field("Evidence file", p.get("filename"))
    field("Evidence size", f"{p.get('size', '?')} bytes")
    field("SHA-256", p.get("sha256"))
    evidence = case.get("evidence") or {}
    field("Raw evidence stored", "yes" if evidence.get("stored") else "unknown/not stored")
    field("Evidence storage key", evidence.get("storage_key"))

    heading("Sender and header evidence")
    field("Subject", p.get("subject"), "Times-Roman", 9)
    field("From", f"{p.get('from_display', '')} <{p.get('from_addr', '')}>")
    field("Reply-To", p.get("reply_to"))
    field("Return-Path", p.get("return_path"))
    field("Message-ID", p.get("message_id"))
    alignment = p.get("alignment") or {}
    field("From/Reply-To alignment", alignment.get("from_reply_to"))
    field("From/Return-Path alignment", alignment.get("from_return_path"))
    field("Overall alignment", alignment.get("overall"))

    heading("Authentication evidence")
    auth = p.get("auth") or {}
    field("Header SPF", auth.get("spf"))
    field("Header DKIM", auth.get("dkim"))
    field("Header DMARC", auth.get("dmarc"))
    field("Authentication source", auth.get("source"))
    field("Verification mode", auth.get("verification_mode"))
    field("Independent DKIM crypto", "no")
    live = p.get("live_auth") or {}
    field("Live DNS enabled", live.get("enabled"))
    field("Live SPF published", live.get("spf_published"))
    field("Live DMARC published", live.get("dmarc_published"))
    field("Live hop in SPF record", live.get("hop_in_spf"))
    field("Live SPF TXT", live.get("spf_txt"))
    field("Live DMARC TXT", live.get("dmarc_txt"))
    field("Raw authentication headers", auth.get("raw"))
    if auth.get("conflicts"):
        field("Conflicting mechanisms", ", ".join(auth["conflicts"]))

    heading("URLs and attachments")
    urls = p.get("urls") or []
    if urls:
        for url in urls:
            write_lines(f"URL: {url}", 8, "Courier", 4)
    else:
        write_lines("URL: none extracted", 8, "Courier", 4)
    attachments = p.get("attachments") or []
    if attachments:
        for attachment in attachments:
            field(
                "Attachment",
                f"{attachment.get('filename')} | {attachment.get('content_type')} | "
                f"{attachment.get('size')} bytes | risk={attachment.get('risk', 'low')} | "
                f"SHA-256 {attachment.get('sha256')}",
            )
    else:
        write_lines("Attachment: none; metadata-only handling, never executed", 8, "Courier", 4)

    heading("Detection and origin")
    field("Method", f.get("method"))
    field("Forensic score", f.get("forensic_score"))
    field("NLP label/points", f"{(f.get('nlp') or {}).get('label')} / {(f.get('nlp') or {}).get('points')}")
    field("Model status", (f.get("model") or {}).get("status"))
    field("Probability", f.get("probability"))
    assist = f.get("llm_assist") or {}
    heading("Qwen analyst assist")
    field("Assist status", assist.get("status"))
    field("Assist provider", assist.get("provider"))
    field("Assist model", assist.get("model"))
    field("Assist validated", "yes" if assist.get("validated") else "no")
    if assist.get("threat_types"):
        field("Assist threat types", ", ".join(str(item) for item in assist["threat_types"]))
    for item in assist.get("observations") or []:
        write_lines(f"Observation: {item}", 8, "Times-Roman", 4)
    for item in assist.get("recommended_actions") or []:
        write_lines(f"Recommended action: {item}", 8, "Times-Roman", 4)
    if assist.get("analyst_note"):
        write_lines(f"Analyst note: {assist['analyst_note']}", 8, "Times-Roman", 4)
    write_lines(assist.get("note") or "No Qwen analyst assist was requested.", 8, "Times-Italic", 4)
    for signal in f.get("signals") or []:
        write_lines(
            f"Signal +{signal.get('points', 0)} [{signal.get('code')}] "
            f"{signal.get('reason')} (source: {signal.get('source')})",
            8,
            "Times-Roman",
            4,
        )
    if not f.get("signals"):
        write_lines("No positive detection signals.", 8, "Times-Roman", 4)
    origin = p.get("origin") or {}
    field("Probable earliest observed public hop", f"{origin.get('ip')} | {origin.get('city')} | {origin.get('isp')} | {origin.get('kind')} | {origin.get('source')}")
    field("Origin interpretation", "hosting/infrastructure context; not a person's GPS or identity")
    for hop in (p.get("hops") or [])[:12]:
        write_lines(
            f"Hop {hop.get('index')}: {hop.get('ip') or '-'} | {hop.get('city')} | {hop.get('isp')} | {hop.get('source')} | {hop.get('raw')}",
            8,
            "Courier",
            4,
        )

    heading("Campaign candidate")
    graph = case.get("graph") or {}
    write_lines(graph.get("note") or "Shared indicators are not identity proof.", 8, "Times-Italic", 4)
    edges = graph.get("edges") or []
    if not edges:
        write_lines("No focused relationship yet. Analyse a second related .eml.", 8, "Times-Roman", 4)
    for edge in edges[:8]:
        field(
            "Relationship",
            f"{edge.get('from')} -- {edge.get('to')} | {edge.get('caption')} | "
            f"strength={edge.get('strength')} | shared={', '.join(edge.get('shared') or [])}",
        )

    heading("Provenance and uncertainty")
    provenance = p.get("provenance") or {}
    for key, value in provenance.items():
        field(f"Provenance {key}", value)
    for item in f.get("uncertainty") or p.get("uncertainty") or []:
        write_lines(f"Uncertainty: {item}", 8, "Times-Roman", 4)
    retention = evidence.get("retention") or {}
    field("Retention", retention.get("policy") or "not configured")
    for event in evidence.get("custody_events") or []:
        field("Custody event", f"{event.get('action')} | {event.get('actor')} | {event.get('at')}")
    write_lines(
        "SHA-256 is an integrity fingerprint. This local prototype trace is not legal-grade chain of custody, "
        "a public blockchain, or human attribution. Live DNS reads published SPF/DMARC TXT records; it does not verify DKIM signatures.",
        8,
        "Times-Italic",
        4,
    )
    c.showPage()
    c.save()
    return path
