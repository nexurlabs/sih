#!/usr/bin/env python3
"""Build the SIH 2026 six-slide MailTrace submission packet.

The PDF uses the official six-page SIH 2026 template as its background and
replaces the placeholder body text with concise diagrams and evidence.
"""
from __future__ import annotations

import io
import shutil
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SHOTS = DOCS / "shots"
TEMPLATE_PDF = Path("/tmp/sih2026_template.pdf")
OUT_PDF = DOCS / "MailTrace_SIH26106_SUBMISSION.pdf"
GRAPH_PNG = SHOTS / "campaign_proof.png"
CASE_HEADER = SHOTS / "case_header.png"
CASE_LOWER = SHOTS / "case_lower.png"
W, H = 960, 540

LOGO = SHOTS / "sih26_brain.png"

# Keep the official template's blue in the small structural accents, but make
# the content itself evidence-lab-like rather than a generic blue dashboard.
INK = HexColor("#18212B")
BLUE = HexColor("#126EAA")
RUST = HexColor("#A94531")
MUTED = HexColor("#5E6870")
RULE = HexColor("#CBD1D4")
PAPER = HexColor("#FBFAF6")
SAND = HexColor("#F1EEE7")
PALE_BLUE = HexColor("#EAF3F8")
PALE_RUST = HexColor("#F7E9E4")
GREEN = HexColor("#2C765B")

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_FILES = {
    "Serif": FONT_DIR / "DejaVuSerif.ttf",
    "SerifBold": FONT_DIR / "DejaVuSerif-Bold.ttf",
    "Sans": FONT_DIR / "DejaVuSans.ttf",
    "SansBold": FONT_DIR / "DejaVuSans-Bold.ttf",
    "Mono": FONT_DIR / "DejaVuSansMono.ttf",
    "MonoBold": FONT_DIR / "DejaVuSansMono-Bold.ttf",
}
for name, path in FONT_FILES.items():
    pdfmetrics.registerFont(TTFont(name, str(path)))


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def pil_font(path: Path, size: int):
    return ImageFont.truetype(str(path), size)


def make_graph_proof() -> None:
    """Draw the actual 07/08 relationship in a projector-readable form."""
    GRAPH_PNG.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (1800, 820), rgb("#FBFAF6"))
    d = ImageDraw.Draw(im)
    serif = pil_font(FONT_DIR / "DejaVuSerif-Bold.ttf", 44)
    sans_b = pil_font(FONT_DIR / "DejaVuSans-Bold.ttf", 25)
    sans = pil_font(FONT_DIR / "DejaVuSans.ttf", 23)
    mono = pil_font(FONT_DIR / "DejaVuSansMono.ttf", 22)
    mono_b = pil_font(FONT_DIR / "DejaVuSansMono-Bold.ttf", 26)
    muted = rgb("#5E6870")
    ink = rgb("#18212B")
    rust = rgb("#A94531")
    rule = rgb("#CBD1D4")
    sand = rgb("#F1EEE7")
    pale = rgb("#F7E9E4")

    d.text((70, 52), "CAMPAIGN CORRELATION", font=mono_b, fill=muted)
    d.text((70, 98), "Two emails. One explainable relationship.", font=serif, fill=ink)
    d.text((70, 158), "A shared indicator creates a campaign candidate — not identity proof.", font=sans, fill=muted)

    left = (70, 270, 715, 570)
    right = (1085, 270, 1730, 570)
    d.rectangle(left, fill=sand, outline=ink, width=4)
    d.rectangle(right, fill=pale, outline=rust, width=4)
    d.rectangle((left[0], left[1], left[2], left[1] + 12), fill=ink)
    d.rectangle((right[0], right[1], right[2], right[1] + 12), fill=rust)

    d.text((left[0] + 36, left[1] + 40), "07", font=mono_b, fill=muted)
    d.text((left[0] + 36, left[1] + 82), "cloud hops", font=sans_b, fill=ink)
    d.text((left[0] + 36, left[1] + 145), "sender domain", font=mono, fill=muted)
    d.text((left[0] + 270, left[1] + 145), "mail-secure.net", font=mono, fill=ink)
    d.text((left[0] + 36, left[1] + 190), "origin hop", font=mono, fill=muted)
    d.text((left[0] + 270, left[1] + 190), "18.184.10.20 / AWS", font=mono, fill=ink)
    d.text((left[0] + 36, left[1] + 235), "Reply-To", font=mono, fill=muted)
    d.text((left[0] + 270, left[1] + 235), "camp@mail-secure.net", font=mono, fill=ink)

    d.text((right[0] + 36, right[1] + 40), "08", font=mono_b, fill=rust)
    d.text((right[0] + 36, right[1] + 82), "campaign twin", font=sans_b, fill=ink)
    d.text((right[0] + 36, right[1] + 145), "sender domain", font=mono, fill=muted)
    d.text((right[0] + 270, right[1] + 145), "mail-secure.net", font=mono, fill=ink)
    d.text((right[0] + 36, right[1] + 190), "origin hop", font=mono, fill=muted)
    d.text((right[0] + 270, right[1] + 190), "18.184.10.20 / AWS", font=mono, fill=ink)
    d.text((right[0] + 36, right[1] + 235), "Reply-To", font=mono, fill=muted)
    d.text((right[0] + 270, right[1] + 235), "camp@mail-secure.net", font=mono, fill=ink)

    cy = 420
    d.line((715, cy, 1085, cy), fill=rust, width=9)
    d.polygon([(1085, cy), (1055, cy - 18), (1055, cy + 18)], fill=rust)
    pill = (760, 350, 1040, 490)
    d.rounded_rectangle(pill, radius=8, fill=rgb("#FBFAF6"), outline=rule, width=3)
    d.text((900, 377), "SHARED", font=mono_b, fill=rust, anchor="mm")
    d.text((900, 421), "Reply-To", font=sans_b, fill=ink, anchor="mm")
    d.text((900, 455), "+ origin IP + domain", font=sans, fill=muted, anchor="mm")

    d.line((70, 660, 1730, 660), fill=rule, width=3)
    d.text((70, 700), "3 SHARED INDICATORS", font=mono_b, fill=rust)
    d.text((465, 700), "campaign candidate", font=sans_b, fill=ink)
    d.text((1450, 700), "prototype output", font=mono, fill=muted)
    im.save(GRAPH_PNG, optimize=True)


def make_logo() -> None:
    source = Path("/tmp/image2.png")
    if not source.exists():
        return
    im = Image.open(source).convert("RGBA")
    # The 2026 template asset contains the brain mark plus wordmark; keep the
    # brain mark for a clean header and title-page visual.
    im.crop((0, 0, 5400, im.height)).save(LOGO, optimize=True)


def make_case_crops() -> None:
    source = Path("/tmp/mt_spoof.png")
    if not source.exists():
        return
    im = Image.open(source).convert("RGB")
    # These are crops from the live localhost case screen, not a mock.
    im.crop((170, 60, 1270, 330)).save(CASE_HEADER, optimize=True)
    im.crop((170, 300, 1270, 700)).save(CASE_LOWER, optimize=True)


def set_fill(c: canvas.Canvas, color) -> None:
    c.setFillColor(color)


def text(c: canvas.Canvas, x, y, value, font="Sans", size=12, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def right_text(c: canvas.Canvas, x, y, value, font="Sans", size=12, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawRightString(x, y, value)


def wrap_lines(value: str, font: str, size: float, max_width: float) -> list[str]:
    words = value.split()
    lines: list[str] = []
    line = ""
    for word in words:
        test = word if not line else line + " " + word
        if pdfmetrics.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def wrapped(c, x, y, value, max_width, font="Sans", size=11, leading=None, color=INK):
    leading = leading or size * 1.3
    c.setFont(font, size)
    c.setFillColor(color)
    for line in wrap_lines(value, font, size, max_width):
        c.drawString(x, y, line)
        y -= leading
    return y


def bullet_list(c, x, y, items, width, size=11, leading=17, color=INK, bullet_color=RUST):
    for item in items:
        c.setFillColor(bullet_color)
        c.circle(x + 3, y + 3, 2.6, fill=1, stroke=0)
        y = wrapped(c, x + 14, y, item, width - 14, "Sans", size, leading, color)
        y -= 5
    return y


def mask_body(c: canvas.Canvas, page: int) -> None:
    """Draw a clean 2026-template shell before each page's content."""
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    titles = {
        1: "TITLE PAGE",
        2: "IDEA TITLE",
        3: "TECHNICAL APPROACH",
        4: "FEASIBILITY AND VIABILITY",
        5: "IMPACT AND BENEFITS",
        6: "RESEARCH AND REFERENCES",
    }
    text(c, 38, 501, "SMART INDIA HACKATHON 2026", "SerifBold", 18, BLUE)
    if LOGO.exists():
        c.drawImage(ImageReader(str(LOGO)), 830, 463, 86, 48, preserveAspectRatio=True, mask="auto")
    text(c, W / 2 - pdfmetrics.stringWidth(titles[page], "SerifBold", 15) / 2, 462, titles[page], "SerifBold", 15, INK)
    c.setFillColor(BLUE)
    c.rect(0, 0, W, 27, fill=1, stroke=0)
    text(c, W / 2 - 70, 9, "@SIH Idea submission - Template", "Sans", 7.2, white)
    right_text(c, W - 25, 9, str(page), "Sans", 7.2, white)
    c.setFillColor(PAPER)
    c.rect(18, 42, W - 36, 401, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.rect(18, 42, W - 36, 401, fill=0, stroke=1)
    if page != 1:
        c.setStrokeColor(BLUE)
        c.setLineWidth(1)
        c.rect(30, 468, 112, 24, fill=0, stroke=1)
        text(c, 38, 477, "TEAM NAME", "MonoBold", 8, BLUE)


def label(c, x, y, value, color=BLUE):
    text(c, x, y, value.upper(), "MonoBold", 9, color)


def rule(c, x1, y, x2, color=RULE, width=1):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def panel(c, x, y, w, h, fill=SAND, stroke=RULE):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    c.rect(x, y, w, h, fill=1, stroke=1)


def metadata_row(c, x, y, key, value, accent=False):
    text(c, x, y, key.upper(), "MonoBold", 8, MUTED)
    text(c, x + 145, y, value, "SansBold" if accent else "Sans", 9.5, RUST if accent else INK)
    rule(c, x, y - 10, x + 448)


def page1(c):
    mask_body(c, 1)
    label(c, 38, 414, "SIH26106  /  SOFTWARE  /  BLOCKCHAIN & CYBERSECURITY", BLUE)
    text(c, 38, 365, "MailTrace", "SerifBold", 34, INK)
    text(c, 38, 334, "Email threat detection + origin forensics", "SansBold", 15, INK)
    c.setFillColor(RUST)
    c.rect(38, 315, 86, 4, fill=1, stroke=0)
    wrapped(c, 38, 288, "Upload a saved email. See the evidence behind its risk, its likely infrastructure, and its relationship to other cases.", 435, "Sans", 11.5, 16, MUTED)
    y = 235
    metadata_row(c, 38, y, "Problem statement ID", "SIH26106")
    y -= 29
    metadata_row(c, 38, y, "Problem statement title", "AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform")
    y -= 29
    metadata_row(c, 38, y, "Theme", "Blockchain & Cybersecurity")
    y -= 29
    metadata_row(c, 38, y, "PS category", "Software")
    y -= 29
    metadata_row(c, 38, y, "Team ID", "[ENTER PORTAL TEAM ID]", True)
    y -= 29
    metadata_row(c, 38, y, "Team name", "[ENTER REGISTERED TEAM NAME]", True)


def flow_box(c, x, y, w, h, number, title, details, fill=PALE_BLUE, accent=BLUE):
    panel(c, x, y, w, h, fill, RULE)
    c.setFillColor(accent)
    c.rect(x, y + h - 7, w, 7, fill=1, stroke=0)
    text(c, x + 12, y + h - 29, number, "MonoBold", 10, accent)
    text(c, x + 12, y + h - 51, title, "SansBold", 11, INK)
    wrapped(c, x + 12, y + h - 72, details, w - 24, "Sans", 8.8, 12, MUTED)


def graph_card(c, x, y, w, h):
    """A compact, vector graph so slide-scale labels stay readable."""
    panel(c, x, y, w, h, PAPER, RULE)
    label(c, x + 16, y + h - 20, "campaign correlation", BLUE)
    text(c, x + 16, y + h - 38, "shared indicators -> campaign candidate", "Sans", 8.5, MUTED)
    box_y = y + 34
    box_h = h - 82
    box_w = (w - 60) / 2
    lx = x + 15
    rx = x + w - 15 - box_w
    panel(c, lx, box_y, box_w, box_h, SAND, INK)
    panel(c, rx, box_y, box_w, box_h, PALE_RUST, RUST)
    text(c, lx + 10, box_y + box_h - 18, "07  /  CLOUD HOPS", "MonoBold", 8.2, BLUE)
    text(c, lx + 10, box_y + box_h - 35, "mail-secure.net", "SansBold", 9.5, INK)
    text(c, lx + 10, box_y + 17, "Reply-To + 18.184.10.20 / AWS", "Mono", 6.8, MUTED)
    text(c, rx + 10, box_y + box_h - 18, "08  /  CAMPAIGN TWIN", "MonoBold", 8.2, RUST)
    text(c, rx + 10, box_y + box_h - 35, "mail-secure.net", "SansBold", 9.5, INK)
    text(c, rx + 10, box_y + 17, "Reply-To + 18.184.10.20 / AWS", "Mono", 6.8, MUTED)
    cy = box_y + box_h / 2
    c.setStrokeColor(RUST)
    c.setLineWidth(2.5)
    c.line(lx + box_w, cy, rx, cy)
    c.setFillColor(RUST)
    c.circle((lx + box_w + rx) / 2, cy, 3, fill=1, stroke=0)
    panel(c, (lx + box_w + rx) / 2 - 56, cy - 14, 112, 28, PAPER, RUST)
    text(c, (lx + box_w + rx) / 2 - 45, cy + 2, "Reply-To + hop", "MonoBold", 6.8, RUST)
    text(c, (lx + box_w + rx) / 2 - 38, cy - 9, "+ domain", "Mono", 6.8, MUTED)


def page2(c):
    mask_body(c, 2)
    text(c, 36, 414, "From one suspicious message to a connected case file.", "SerifBold", 18, INK)
    text(c, 36, 390, "MailTrace combines detection, origin context and campaign correlation in one analyst workflow.", "Sans", 10.5, MUTED)
    label(c, 36, 356, "proposed solution")
    xs = [36, 150, 264, 378]
    titles = ["CAPTURE", "EXTRACT", "EXPLAIN", "CONNECT"]
    details = [
        ".eml bytes stay local; hash the exact evidence.",
        "From, Reply-To, Received, URLs and MIME parts.",
        "Auth results, risk score and reasons an analyst can cite.",
        "Shared Reply-To, domain or hop IP becomes a campaign lead.",
    ]
    for i, (x, t, d) in enumerate(zip(xs, titles, details), 1):
        flow_box(c, x, 267, 96, 78, str(i).zfill(2), t, d, PALE_BLUE if i != 3 else PALE_RUST, BLUE if i != 3 else RUST)
        if i < 4:
            c.setStrokeColor(MUTED)
            c.setLineWidth(1.5)
            c.line(x + 96, 306, x + 110, 306)
            c.setFillColor(MUTED)
            c.circle(x + 110, 306, 2.3, fill=1, stroke=0)
    label(c, 36, 231, "prototype output")
    graph_card(c, 36, 73, 889, 145)
    text(c, 36, 54, "Detection = reasons  |  Origin = hosting intelligence  |  Correlation = a lead, not an identity claim", "Mono", 8.2, MUTED)


def module_box(c, x, y, w, h, title, details, accent=BLUE):
    panel(c, x, y, w, h, SAND, RULE)
    c.setFillColor(accent)
    c.rect(x, y, 6, h, fill=1, stroke=0)
    text(c, x + 16, y + h - 25, title, "MonoBold", 9, accent)
    wrapped(c, x + 16, y + h - 47, details, w - 28, "Sans", 8.4, 11.5, INK)


def page3(c):
    mask_body(c, 3)
    text(c, 36, 414, "Evidence pipeline: small, explainable modules.", "SerifBold", 18, INK)
    text(c, 36, 390, "The working prototype is deterministic first; NLP is one supporting signal, not the whole product.", "Sans", 10.5, MUTED)
    modules = [
        ("01  .EML", "raw bytes + SHA-256", BLUE),
        ("02  MIME", "headers, body, URLs, attachments", BLUE),
        ("03  AUTH", "SPF / DKIM / DMARC + alignment", RUST),
        ("04  ORIGIN", "Received chain + hosting intel", BLUE),
        ("05  OUTPUT", "score, map, graph, PDF", RUST),
    ]
    x = 36
    for i, (t, d, a) in enumerate(modules):
        module_box(c, x, 280, 164, 82, t, d, a)
        if i < len(modules) - 1:
            c.setStrokeColor(MUTED)
            c.setLineWidth(1.2)
            c.line(x + 164, 321, x + 177, 321)
        x += 183
    label(c, 36, 238, "implemented prototype")
    bullet_list(c, 36, 214, [
        "FastAPI + Python email parser + SQLite case store",
        "NetworkX campaign graph + Leaflet hop map + ReportLab forensic PDF",
        "Offline demo intelligence keeps the laptop demo reproducible and safe",
    ], 470, 9.6, 13)
    label(c, 535, 238, "real localhost proof", GREEN)
    if CASE_HEADER.exists():
        c.drawImage(ImageReader(str(CASE_HEADER)), 535, 153, 390, 72, preserveAspectRatio=True, mask="auto")
    if CASE_LOWER.exists():
        c.drawImage(ImageReader(str(CASE_LOWER)), 535, 73, 390, 72, preserveAspectRatio=True, mask="auto")
    c.setStrokeColor(RULE)
    c.rect(535, 73, 390, 152, fill=0, stroke=1)
    text(c, 535, 58, "Captured from the local case screen: score, reasons, hop map and evidence footer.", "Mono", 7.8, MUTED)


def two_column_heading(c, x, y, title, accent=BLUE):
    c.setFillColor(accent)
    c.rect(x, y - 5, 6, 26, fill=1, stroke=0)
    text(c, x + 16, y + 5, title, "SansBold", 13, INK)


def row(c, x, y, w, left, right, fill, right_color=INK):
    c.setFillColor(fill)
    c.rect(x, y - 4, w, 34, fill=1, stroke=0)
    text(c, x + 12, y + 9, left, "MonoBold", 8.5, MUTED)
    wrapped(c, x + 145, y + 9, right, w - 157, "Sans", 9, 12, right_color)


def page4(c):
    mask_body(c, 4)
    text(c, 36, 414, "Feasible now; harden the edges as adoption grows.", "SerifBold", 18, INK)
    text(c, 36, 390, "The first version runs on a laptop and avoids fragile live dependencies. The production path is modular.", "Sans", 10.5, MUTED)
    two_column_heading(c, 36, 350, "NOW  /  IDEA-ROUND PROTOTYPE", BLUE)
    two_column_heading(c, 500, 350, "NEXT  /  PRODUCTION HARDENING", RUST)
    left_items = [
        "saved .eml upload; no mailbox credentials",
        "8 crafted cases for clean, spoof, phish, BEC and campaign paths",
        "offline demo geo and domain cache for reproducible runs",
        "local SQLite case store, graph and PDF evidence",
    ]
    right_items = [
        "live DNS and cryptographic auth verification",
        "maintained GeoIP / ASN data and organisation deployment",
        "access control, PII masking and retention policies",
        "larger labelled corpus, calibration and analyst feedback",
    ]
    y = 317
    for item in left_items:
        y = bullet_list(c, 40, y, [item], 405, 9.2, 12, INK, BLUE)
    y = 317
    for item in right_items:
        y = bullet_list(c, 504, y, [item], 405, 9.2, 12, INK, RUST)
    label(c, 36, 186, "risks and mitigations", RUST)
    x, w = 36, 889
    c.setFillColor(INK)
    c.rect(x, 146, w, 24, fill=1, stroke=0)
    text(c, x + 12, 154, "RISK", "MonoBold", 8, white)
    text(c, x + 286, 154, "MITIGATION IN MAILTRACE", "MonoBold", 8, white)
    risks = [
        ("Headers can be missing or forged", "show confidence, preserve raw evidence, never call a lead proof"),
        ("IP geolocation is not a human location", "report hosting city / ISP only; explicitly reject GPS attribution"),
        ("Email data is sensitive", "local-first workflow; no Gmail ingest; future masking, access and retention controls"),
    ]
    y = 116
    for i, (a, b) in enumerate(risks):
        row(c, x, y, w, a, b, PALE_BLUE if i % 2 == 0 else white)
        y -= 36


def page5(c):
    mask_body(c, 5)
    text(c, 36, 414, "Impact: turn a vague warning into an actionable case.", "SerifBold", 18, INK)
    text(c, 36, 390, "MailTrace is for people who must explain what happened, preserve evidence and decide what to do next.", "Sans", 10.5, MUTED)
    label(c, 36, 354, "the analyst difference")
    panel(c, 36, 245, 250, 86, PALE_BLUE, RULE)
    text(c, 55, 304, "FILTER", "MonoBold", 10, BLUE)
    text(c, 55, 274, "spam / not spam", "SerifBold", 22, INK)
    wrapped(c, 55, 256, "A label without context leaves the next question unanswered.", 210, "Sans", 8.8, 12, MUTED)
    c.setStrokeColor(RUST)
    c.setLineWidth(3)
    c.line(300, 288, 350, 288)
    c.setFillColor(RUST)
    c.circle(350, 288, 4, fill=1, stroke=0)
    panel(c, 372, 223, 552, 108, PALE_RUST, RUST)
    text(c, 393, 304, "MAILTRACE CASE FILE", "MonoBold", 10, RUST)
    text(c, 393, 278, "SPF fail  ·  Reply-To mismatch  ·  earliest hop", "SansBold", 12, INK)
    text(c, 393, 256, "Frankfurt / AWS  ·  related case 08  ·  SHA-256", "Sans", 10, MUTED)
    text(c, 393, 237, "reasons + origin context + campaign lead", "Sans", 10, INK)

    label(c, 36, 187, "target users and value", BLUE)
    rows = [
        ("IT / helpdesk", "triage a suspicious message with reasons they can cite"),
        ("SOC / incident response", "preserve original evidence and connect related messages"),
        ("universities / SMEs", "run locally without handing an inbox to a third party"),
    ]
    y = 158
    for i, (a, b) in enumerate(rows):
        row(c, 36, y, 888, a, b, SAND if i % 2 == 0 else white)
        y -= 35
    label(c, 36, 48, "pilot measures  /  no invented numbers", RUST)
    text(c, 226, 48, "time-to-triage  ·  evidence completeness  ·  linked-campaign discovery  ·  analyst agreement", "Mono", 8.5, MUTED)


def page6(c):
    mask_body(c, 6)
    text(c, 36, 414, "Research basis and implementation references.", "SerifBold", 18, INK)
    text(c, 36, 390, "The prototype maps directly to the problem statement while keeping attribution and privacy claims bounded.", "Sans", 10.5, MUTED)
    two_column_heading(c, 36, 350, "PROBLEM + STANDARDS", BLUE)
    refs_left = [
        ("SIH26106", "Official PS: NLP/ML detection, header forensics, IP geo, domain intelligence, graph correlation and forensic reporting."),
        ("RFC 5322", "Internet Message Format: structured headers, message IDs and Received fields."),
        ("RFC 7208 / 6376 / 7489", "SPF, DKIM and DMARC concepts used for authentication evidence and alignment."),
    ]
    y = 317
    for title, desc in refs_left:
        text(c, 40, y, title, "MonoBold", 9, RUST)
        y = wrapped(c, 170, y, desc, 330, "Sans", 8.8, 12, INK) - 17
    two_column_heading(c, 500, 350, "BUILD REFERENCES", RUST)
    refs_right = [
        ("Python email", "standard-library MIME parsing; attachments are named and hashed, never executed."),
        ("NetworkX + Leaflet", "relationship graph and hop map for analyst inspection."),
        ("ReportLab + SHA-256", "portable case PDF and integrity fingerprint of the exact uploaded bytes."),
        ("SpamAssassin corpus", "optional TF-IDF baseline only; it is not presented as origin forensics."),
    ]
    y = 317
    for title, desc in refs_right:
        text(c, 504, y, title, "MonoBold", 9, RUST)
        y = wrapped(c, 635, y, desc, 285, "Sans", 8.8, 12, INK) - 15
    panel(c, 36, 105, 888, 88, PALE_BLUE, RULE)
    label(c, 55, 171, "scope and safety", BLUE)
    bullet_list(c, 55, 148, [
        "Local crafted .eml files only for the demo; no Gmail/Outlook production ingest and no real phishing messages.",
        "Geo output is hosting infrastructure with confidence, never the exact location of a person.",
        "The evidence hash is an integrity fingerprint, not a public blockchain or cryptocurrency ledger.",
    ], 840, 9.2, 12, INK, BLUE)
    text(c, 36, 74, "Source links: sih.gov.in/sih2026PS  ·  rfc-editor.org  ·  docs.python.org  ·  networkx.org  ·  leafletjs.com", "Mono", 8.2, MUTED)


def build_pdf() -> None:
    out = OUT_PDF
    c = canvas.Canvas(str(out), pagesize=(W, H))
    pages = [page1, page2, page3, page4, page5, page6]
    for fn in pages:
        fn(c)
        c.showPage()
    c.save()
    print("wrote", out)


if __name__ == "__main__":
    make_logo()
    make_graph_proof()
    make_case_crops()
    build_pdf()
