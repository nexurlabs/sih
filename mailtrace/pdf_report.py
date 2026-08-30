"""One-page forensic PDF. Hash of the .eml, not a blockchain."""
from __future__ import annotations

from pathlib import Path
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
    y = h - 22 * mm
    c.setFont("Times-Bold", 18)
    c.drawString(18 * mm, y, "MailTrace case file")
    y -= 8 * mm
    c.setFont("Courier", 9)
    c.drawString(18 * mm, y, f"id {case['id']}   {f['label']}   score {f['score']}")
    y -= 6 * mm
    c.drawString(18 * mm, y, f"file {p['filename']}")
    y -= 6 * mm
    c.drawString(18 * mm, y, f"from {p.get('from_display','')} <{p.get('from_addr','')}>")
    y -= 5 * mm
    c.drawString(18 * mm, y, f"reply-to {p.get('reply_to') or '-'}")
    y -= 8 * mm
    c.setFont("Times-Bold", 11)
    c.drawString(18 * mm, y, "Reasons")
    y -= 6 * mm
    c.setFont("Times-Roman", 10)
    for r in f.get("reasons") or []:
        c.drawString(18 * mm, y, f"- {r[:110]}")
        y -= 5 * mm
    y -= 4 * mm
    c.setFont("Times-Bold", 11)
    c.drawString(18 * mm, y, "Origin hop")
    y -= 6 * mm
    c.setFont("Courier", 9)
    o = p.get("origin") or {}
    c.drawString(18 * mm, y, f"{o.get('ip')}  {o.get('city')}  {o.get('isp')}  {o.get('kind')}")
    y -= 8 * mm
    c.setFont("Times-Bold", 11)
    c.drawString(18 * mm, y, "Hops")
    y -= 5 * mm
    c.setFont("Courier", 8)
    for h in (p.get("hops") or [])[:8]:
        c.drawString(18 * mm, y, f"{h.get('ip') or '-':15} {h.get('city') or ''} {h.get('isp') or ''}"[:95])
        y -= 4 * mm
    y -= 3 * mm
    c.setFont("Times-Bold", 11)
    c.drawString(18 * mm, y, "Campaign links")
    y -= 5 * mm
    c.setFont("Times-Roman", 9)
    edges = (case.get("graph") or {}).get("edges") or []
    if not edges:
        c.drawString(18 * mm, y, "None yet. Analyse a second related .eml.")
        y -= 4 * mm
    for e in edges[:8]:
        c.drawString(18 * mm, y, f"{e.get('from')} -- {e.get('to')}  {e.get('caption') or ', '.join(e.get('shared') or [])}"[:100])
        y -= 4 * mm
    y -= 6 * mm
    c.setFont("Times-Bold", 11)
    c.drawString(18 * mm, y, "SHA-256 of this exact .eml")
    y -= 6 * mm
    c.setFont("Courier", 8)
    c.drawString(18 * mm, y, p.get("sha256", ""))
    y -= 10 * mm
    c.setFont("Times-Italic", 9)
    c.drawString(18 * mm, y, "Geo is hosting city / ISP. Not a person's GPS. No live mailbox.")
    c.showPage()
    c.save()
    return path
