#!/usr/bin/env python3
"""Build a phone-readable, screenshot-backed MailTrace walkthrough."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "docs" / "shots" / "explainer"
OUT = ROOT / "docs" / "MailTrace_Full_Explainer.pdf"
BASE_URL = "http://127.0.0.1:8777"

PAPER = colors.HexColor("#F3EEE4")
PAPER_DARK = colors.HexColor("#E8DFD0")
INK = colors.HexColor("#2B2924")
MUTED = colors.HexColor("#625D55")
RUST = colors.HexColor("#B34832")
RUST_PALE = colors.HexColor("#F1DDD5")
GOLD = colors.HexColor("#B78A4A")
RULE = colors.HexColor("#C9BFAF")
WHITE = colors.white


def live_json(path: str):
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=8) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


health = live_json("/api/health") or {
    "llm": {"status": "ready", "provider": "groq", "model": "qwen/qwen3.8-27b"}
}
live_graph = live_json("/api/graph") or {
    "nodes": [
        {"id": "07", "label": "07 cloud hops", "score": 66},
        {"id": "08", "label": "08 campaign twin", "score": 66},
    ],
    "edges": [
        {
            "shared": ["dom:mail-secure.net", "ip:18.184.10.20", "rt:camp@mail-secure.net"],
            "caption": "domain: mail-secure.net + same hop: 18.184.10.20 + Reply-To: camp@mail-secure.net",
        }
    ],
}
fixture_results = json.loads((ASSET / "fixture_results.json").read_text())

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverKicker", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9, leading=12, tracking=2.5, textColor=RUST, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Times-Bold",
    fontSize=28, leading=31, textColor=INK, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSub", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=17, textColor=MUTED, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="H1MT", parent=styles["Heading1"], fontName="Times-Bold",
    fontSize=20, leading=24, textColor=INK, spaceBefore=2, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="H2MT", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=15, textColor=RUST, spaceBefore=8, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodyMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="SmallMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8, leading=10.5, textColor=MUTED, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="CaptionMT", parent=styles["BodyText"], fontName="Helvetica-Oblique",
    fontSize=7.5, leading=9.5, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CodeMT", parent=styles["Code"], fontName="Courier",
    fontSize=8, leading=10.5, textColor=INK, backColor=PAPER_DARK,
    borderColor=RULE, borderWidth=0.5, borderPadding=7, leftIndent=0, rightIndent=0,
    spaceBefore=4, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CalloutMT", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=9, leading=13, textColor=INK, backColor=RUST_PALE,
    borderColor=RUST, borderWidth=0.7, borderPadding=8, spaceBefore=5, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="TableHeadMT", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=7.8, leading=9.5, textColor=WHITE,
))
styles.add(ParagraphStyle(
    name="TableMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7.5, leading=9.4, textColor=INK,
))
styles.add(ParagraphStyle(
    name="TableSmallMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=6.9, leading=8.3, textColor=INK,
))


def P(text: str, style: str = "BodyMT") -> Paragraph:
    return Paragraph(text, styles[style])


def safe(text) -> str:
    return escape(str(text), {'"': '&quot;'})


def bullets(items: list[str], style: str = "BodyMT"):
    return [P("• " + safe(item), style) for item in items]


def make_table(rows, widths, small=False, header=True):
    body_style = "TableSmallMT" if small else "TableMT"
    data = []
    for r, row in enumerate(rows):
        cell_style = "TableHeadMT" if header and r == 0 else body_style
        data.append([P(safe(cell), cell_style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), RUST)]
        if len(rows) > 1:
            commands += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER_DARK])]
    table.setStyle(TableStyle(commands))
    return [table]


def image_flow(name: str, max_w: float, max_h: float, caption: str | None = None):
    path = ASSET / name
    with PILImage.open(path) as im:
        iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    image = Image(str(path), width=iw * scale, height=ih * scale)
    result: list = [image]
    if caption:
        result.append(P(caption, "CaptionMT"))
    return result


def code_block(text: str):
    return Preformatted(text, styles["CodeMT"])


def section(title: str, subtitle: str | None = None):
    out = [P(title, "H1MT"), HRFlowable(width="100%", thickness=0.7, color=RUST, spaceAfter=9)]
    if subtitle:
        out.append(P(subtitle, "CoverSub"))
    return out


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, A4[1] - 13 * mm, A4[0] - doc.rightMargin, A4[1] - 13 * mm)
    canvas.setFont("Courier", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, A4[1] - 10 * mm, "M A I L T R A C E")
    canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 10 * mm, "SIH26106 · local analyst lab")
    canvas.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
    canvas.drawString(doc.leftMargin, 8 * mm, "Source-grounded walkthrough · demo evidence only")
    canvas.drawRightString(A4[0] - doc.rightMargin, 8 * mm, f"{doc.page}")
    canvas.restoreState()


story = []

# 1 — Cover.
story += [Spacer(1, 12 * mm), P("SIH26106 · MAILTRACE", "CoverKicker")]
story += [P("How the prototype works", "CoverTitle")]
story += [P("A screenshot-backed explanation of the parser, score, origin view, campaign graph, PDF evidence, and optional Groq/Qwen analyst assist.", "CoverSub")]
story += [P("The one-line idea", "H2MT")]
story += [P("Drop a saved email. Get an explainable case file.", "CoverSub")]
story += image_flow("01_landing.png", 174 * mm, 116 * mm, "Figure 1 — the real localhost landing screen: eight crafted samples plus raw .eml upload.")
story += [P("Scope in one sentence", "H2MT")]
story += [P("MailTrace is a local-first analyst lab. It accepts a saved RFC 5322 email, preserves its fingerprint, extracts forensic signals, produces a deterministic risk indicator, stores evidence locally, correlates campaign candidates, and exports a report. It is not Gmail ingest, not a live authentication verifier, and not a human-location or attacker-attribution system.", "BodyMT")]
story += [PageBreak()]

# 2 — Mental model and data flow.
story += section("1. The 30-second mental model", "Think of MailTrace as a controlled evidence pipeline, not a black-box spam button.")
story += [code_block(
    "saved .eml\n"
    "    ↓ exact bytes + SHA-256 fingerprint\n"
    "Python email BytesParser\n"
    "    ↓ headers · body · URLs · attachments metadata · Received hops\n"
    "header evidence + alignment + offline domain/IP context\n"
    "    ↓\n"
    "deterministic score + CLEAN/SPOOF/PHISH/BEC label\n"
    "    ├─→ SQLite case + raw evidence\n"
    "    ├─→ focused campaign graph\n"
    "    └─→ forensic PDF\n"
    "\n"
    "optional redacted summary ──→ Groq Qwen analyst notes\n"
    "                                  advisory only"
)]
story += [P("The separation that matters", "H2MT")]
story += bullets([
    "The parser and deterministic rule fusion decide the displayed score, label, reasons, authentication state, and graph rules.",
    "Qwen sees a minimal redacted evidence summary only. It can add observations and recommended actions, but it cannot change the score or label.",
    "The UI and PDF repeat uncertainty boundaries so a demo claim does not quietly become a production claim.",
])
story += [P("Runtime components", "H2MT")]
story += make_table([
    ["Layer", "What is actually running"],
    ["Browser UI", "Vanilla HTML/CSS/JavaScript dossier served by FastAPI."],
    ["API", "FastAPI routes on 127.0.0.1:8777."],
    ["Parsing", "Python email.policy + BytesParser for MIME/RFC 5322 content."],
    ["Evidence", "SQLite case store plus SHA-256-named raw .eml files."],
    ["Correlation", "NetworkX graph converted to a small API response and custom SVG."],
    ["Origin view", "Received-header heuristic plus a deliberately small offline demo table."],
    ["Reports", "ReportLab PDF generated from the stored case."],
    ["Optional analyst", "Groq OpenAI-compatible endpoint using qwen/qwen3.8-27b."],
], [38 * mm, 136 * mm])
story += [PageBreak()]

# 3 — Upload and parser.
story += section("2. What happens when an email is uploaded")
story += [P("Step 1 — the API accepts bytes", "H2MT")]
story += [P("The UI sends the selected file to POST /api/analyze. Demo buttons use POST /api/analyze-sample/{name}. Empty uploads and unknown sample names are rejected. The server does not connect to Gmail or Outlook.", "BodyMT")]
story += [P("Step 2 — the original bytes get a fingerprint", "H2MT")]
story += [P("The exact upload bytes are hashed with SHA-256. That hash becomes the evidence storage key and is shown in the case so an analyst can tell which file produced the report.", "BodyMT")]
story += [P("Step 3 — structured fields are extracted", "H2MT")]
story += bullets([
    "From display name, address and domain; Reply-To; Return-Path; Subject; Date; Message-ID.",
    "Authentication-Results, Received-SPF and ARC authentication evidence.",
    "Plain-text body, limited locally to 4,000 characters; URLs deduplicated to 20.",
    "Received headers, candidate public IPs, a probable earliest public hop and cached infrastructure context.",
    "Attachment filename, MIME type, byte size and SHA-256 metadata, limited to 20. Attachments are never executed.",
])
story += image_flow("case_header.png", 174 * mm, 135 * mm, "Figure 2 — the live 04_spf_fail case: score, sender fields, alignment, reasons, Received chain and origin map.")
story += [PageBreak()]

# 4 — Authentication/origin.
story += section("3. Headers, authentication evidence, and origin")
story += [P("Authentication is evidence read from the file", "H2MT")]
story += [P("MailTrace scans the authentication headers already present in the .eml. Each of SPF, DKIM and DMARC becomes pass, fail, unknown, or conflict. The API marks the source as message-header, verification_mode as header-stated, and verified as false. A contradictory pass/fail observation becomes conflict and never silently resolves to pass.", "BodyMT")]
story += make_table([
    ["Visible field", "What the prototype means"],
    ["SPF / DKIM / DMARC", "Header-stated values, not a new DNS or cryptographic check."],
    ["From / Reply-To", "Domain comparison for alignment and mismatch signals."],
    ["From / Return-Path", "Domain comparison for delivery-identity alignment."],
    ["Received chain", "Parsed hop lines with candidate IP, status and cached context."],
    ["Origin", "Last public Received entry in parsed header order; confidence is heuristic."],
], [42 * mm, 132 * mm])
story += [P("Origin means infrastructure, not a person", "H2MT")]
story += [P("Private addresses such as 10.x, 127.x and 192.168.x are skipped when looking for a public hop. The selected hop is looked up in a small offline table used for the crafted samples. A Frankfurt/AWS result describes hosting context behind the observed hop; it does not locate a human, prove ownership, or attribute an attack.", "BodyMT")]
story += [P("Offline intelligence", "H2MT")]
story += [P("The demo domain cache supplies fields such as age, registrar and status from a checked-in JSON table. There is no live WHOIS, DNS, blacklist, threat-intelligence feed, or maintained global GeoIP database in this prototype.", "BodyMT")]
story += [PageBreak()]

# 5 — Score.
story += section("4. How the deterministic score is calculated")
story += [P("The score is intentionally inspectable", "H2MT")]
story += [P("Every case starts at 8. Matching signals add fixed points, the total is clamped to 0–100, and up to six strongest reasons are shown. The score is an explainable risk indicator, not a probability, accuracy percentage, or trained classifier.", "BodyMT")]
score_rows = [["Signal", "Points", "Source / meaning"]]
score_rows += [
    ["Visible Gmail address wearing an official title", "+28", "message-header"],
    ["Reply-To domain mismatch", "+18", "message-header"],
    ["Return-Path domain mismatch", "+10", "message-header"],
    ["SPF fail", "+22", "message-header"],
    ["DKIM fail", "+12", "message-header"],
    ["DMARC fail", "+12", "message-header"],
    ["Lookalike domain", "+20", "body / URL heuristic"],
    ["Young cached domain", "+14", "offline-cache"],
    ["Cloud-origin first public hop", "+10", "Received + offline-cache"],
    ["Password or login request", "+16", "body heuristic"],
    ["Invoice / payment redirect language", "+18", "body heuristic"],
    ["Urgency language", "+8", "body heuristic"],
]
story += make_table(score_rows, [69 * mm, 18 * mm, 87 * mm], small=True)
story += [P("Label order matters", "H2MT")]
story += bullets([
    "PHISH first: score ≥ 70 plus a password/login or lookalike reason.",
    "BEC next: score ≥ 50 plus payment, BEC or invoice language.",
    "SPOOF next: score ≥ 55 plus title, SPF or Reply-To evidence; otherwise score ≥ 45.",
    "Otherwise CLEAN. A clean case with no reasons receives an alignment/no-cue explanation.",
])
story += [P("Why this is defensible in a demo", "H2MT")]
story += [P("An analyst can add the visible points and see why the label happened. The method is transparent and reproducible, while the UI explicitly avoids pretending that a fixed rule sum is a calibrated probability.", "CalloutMT")]
story += [PageBreak()]

# 6 — Worked example.
story += section("5. Worked example: 04_spf_fail.eml")
story += [P("The displayed 64 is not magic", "H2MT")]
story += [code_block("base score                                      8\nSPF fail                                      +22\nDKIM fail                                     +12\nDMARC fail                                    +12\ncloud-origin hop: AWS, Frankfurt             +10\n                                             ────\ndeterministic total                            64")]
story += [P("The case is labeled SPOOF because the score is above the spoof threshold and the reasons contain SPF evidence. The From and Return-Path domains are aligned in this fixture, while Reply-To is absent; the complete authentication failure still drives the result.", "BodyMT")]
story += bullets([
    "The Received line supplies 18.184.10.20 as the probable public hop.",
    "The offline table renders that hop as Frankfurt / AWS / known.",
    "The UI shows the map as a visual origin aid, not as an attacker map.",
    "The Qwen panel adds observations and actions separately; it does not recalculate 64.",
])
story += image_flow("case_assist.png", 174 * mm, 145 * mm, "Figure 3 — the same live case lower down: signals, Qwen advisory panel, offline cache, PDF/evidence actions and provenance.")
story += [PageBreak()]

# 7 — Qwen and bots.
story += section("6. What the three SIH bots and Qwen do")
story += [P("The three Bot Mode profiles now share one Groq route", "H2MT")]
story += make_table([
    ["Profile", "Provider", "Model", "Tools"],
    ["sih-grok46", "groq", "qwen/qwen3.8-27b", "file + terminal"],
    ["sih-luna56", "groq", "qwen/qwen3.8-27b", "file + terminal"],
    ["sih-minimaxm3", "groq", "qwen/qwen3.8-27b", "file + terminal"],
], [39 * mm, 25 * mm, 52 * mm, 58 * mm])
story += [P("The provider is optional, not the detector", "H2MT")]
story += [P("The app sends Qwen a minimal redacted evidence summary. It includes bounded subject/body text, domains, alignment, header-stated authentication, masked IPs, safe URLs without query strings, attachment metadata without bytes, selected hop context, and the deterministic result for explanation. It does not send raw .eml bytes, attachment bytes, query strings, or unmasked email addresses.", "BodyMT")]
story += [P("Qwen is constrained to return JSON with threat types, observations, recommended actions, an analyst note, and a manual-review flag. Invalid or unavailable provider responses fall back to a truthful unavailable status while the deterministic case remains complete.", "BodyMT")]
story += [P("Hard boundary", "H2MT")]
story += [P("Qwen cannot override score, label, evidence, authentication conflict handling, origin rules, graph edges, or the safety disclaimers. validated is always false. It must not claim attacker identity, human location, live authentication, probability, or confidence.", "CalloutMT")]
story += [P("Why the profiles use a small tool set", "H2MT")]
story += [P("Groq's free-tier request budget is limited. The full Hermes tool catalog made the Bot Mode prompt too large and triggered HTTP 413. The three authorized profiles therefore use only file and terminal tools for a normal Qwen run, keeping the local analyst workflow under the provider limit.", "BodyMT")]
story += image_flow("case_assist.png", 174 * mm, 120 * mm, "Figure 4 — Qwen is visibly labeled “ADVISORY” beside the authoritative score and reasons.")
story += [PageBreak()]

# 8 — Graph.
story += section("7. How campaign correlation works")
story += [P("The graph is a candidate relationship view", "H2MT")]
story += [P("Each filename contributes one current node. The graph compares meaningful parsed indicators: Reply-To address, non-generic domains, and observed public hop IPs. A shared Reply-To is meaningful by itself; otherwise at least two non-IP indicators are required. IP-only relationships are rejected.", "BodyMT")]
story += image_flow("graph_focus.png", 174 * mm, 154 * mm, "Figure 5 — the real 07 → 08 campaign demo: two case nodes and one relationship caption.")
edge = (live_graph.get("edges") or [{}])[0]
node_count = len(live_graph.get("nodes") or [])
edge_count = len(live_graph.get("edges") or [])
shared = ", ".join(edge.get("shared") or ["dom:mail-secure.net", "ip:18.184.10.20", "rt:camp@mail-secure.net"])
caption = edge.get("caption") or "domain: mail-secure.net + same hop: 18.184.10.20 + Reply-To: camp@mail-secure.net"
story += [P(f"Live graph readback: {node_count} nodes / {edge_count} edge", "H2MT")]
story += [P(f"Shared API indicators: {safe(shared)}", "BodyMT")]
story += [P(f"Rendered caption: {safe(caption)}", "BodyMT")]
story += [P("The API itself labels the relation campaign-candidate and states that shared indicators do not prove common control, identity, or responsibility. This is correlation for analyst attention, not attribution.", "CalloutMT")]
story += [PageBreak()]

# 9 — Evidence and PDF.
story += section("8. Evidence storage, masking, and the PDF report")
story += [P("What is persisted locally", "H2MT")]
story += make_table([
    ["Artifact", "Purpose"],
    ["data/mailtrace.db", "Case ID, filename, SHA-256, parsed JSON payload and creation time."],
    ["data/evidence/<sha256>.eml", "Original raw bytes, checked again against the parsed SHA-256 before serving."],
    ["data/reports/", "Generated case PDFs."],
    ["/api/case/{id}/masked", "Masked case view for safer sharing."],
    ["/api/case/{id}/evidence", "Raw message/rfc822 evidence only when the stored hash still matches."],
    ["/api/case/{id}/pdf", "ReportLab PDF generated from the stored case."],
], [53 * mm, 121 * mm])
story += [P("What the report is honest about", "H2MT")]
story += bullets([
    "SHA-256 is an integrity fingerprint, not a blockchain.",
    "The local custody events are a prototype trace, not legal-grade chain of custody.",
    "Retention is caller-configured; there is no default retention period in this prototype.",
    "Authentication values come from message headers; no independent live DNS or DKIM verification is performed.",
])
story += image_flow("case_report_08.png", 112 * mm, 176 * mm, "Figure 6 — the actual one-page PDF generated for the 08 campaign case.")
story += [PageBreak()]

# 10 — Full demo runbook.
story += section("9. How to run and demonstrate it")
story += [P("Start the reproducible local path", "H2MT")]
story += [code_block(
    "cd /root/sih-mailtrace\n"
    "./run.sh\n"
    "\n"
    "# run.sh loads the ignored .env, regenerates samples,\n"
    "# runs the test suite, and starts Uvicorn on 127.0.0.1:8777"
)]
story += [P("Open this URL in the VM browser", "H2MT"), P("http://127.0.0.1:8777/", "CodeMT")]
story += [P("Recommended live demo order", "H2MT")]
story += bullets([
    "Click 04_spf_fail.eml. Point to 64, SPOOF, the three failed auth stamps, the reasons and Frankfurt/AWS hosting context.",
    "Scroll through the Qwen panel. Say “advisory” out loud; the rule score remains authoritative.",
    "Click Download case PDF and show the case fingerprint/provenance.",
    "For the graph, clear old local cases, then click 07_cloud_hops.eml followed by 08_campaign_twin.eml. The focused graph should be 2 nodes / 1 edge.",
    "For an upload demo, use a crafted .eml only. Do not upload real private mail while Qwen is enabled.",
])
story += [P("Clean graph command", "H2MT")]
story += [code_block("curl -X POST http://127.0.0.1:8777/api/reset")]
story += [P("Reset deletes the local demo cases and their stored evidence. Run it only when you want a clean campaign demonstration.", "SmallMT")]
story += [P("Useful API checks", "H2MT")]
story += make_table([
    ["Request", "Expected purpose"],
    ["GET /api/health", "Product, PS ID and safe Qwen runtime status."],
    ["GET /api/samples", "Eight demo filenames and byte sizes."],
    ["POST /api/analyze-sample/04_spf_fail.eml", "Live deterministic case plus optional advisory."],
    ["POST /api/analyze", "Raw multipart .eml upload."],
    ["GET /api/graph", "All current deduplicated graph nodes/edges."],
], [76 * mm, 98 * mm], small=True)
story += [PageBreak()]

# 11 — Mobile and boundaries.
story += section("10. Mobile view and the honest boundary")
story += image_flow("04_mobile_landing.png", 92 * mm, 150 * mm, "Figure 7 — the same landing flow at 390px: buttons stack without horizontal overflow.")
story += [P("Implemented now", "H2MT")]
story += bullets([
    "Local saved-email upload and eight deterministic demo fixtures.",
    "MIME/header/body parsing, authentication evidence, alignment, URLs, attachment metadata and Received-hop analysis.",
    "Explainable score, label, reasons, provenance, SHA-256 evidence and local case retrieval.",
    "Offline domain/IP context, map view, focused campaign graph and PDF export.",
    "Optional redacted Groq/Qwen analyst notes with offline/unavailable fallback.",
])
story += [P("Partial, offline, or intentionally absent", "H2MT")]
story += bullets([
    "No validated NLP/ML detector or calibrated probability. The deterministic score is not a trained model.",
    "No live DNS, WHOIS, threat-intelligence, blacklist or independent SPF/DKIM/DMARC cryptographic verification.",
    "No person geolocation, attacker identity, human attribution or legal-grade custody.",
    "No Gmail/Outlook ingestion, malware execution, attachment detonation or public multi-user account system.",
    "The graph is local shared-indicator correlation, not full campaign attribution.",
])
story += [P("Public hosting is a separate hardening project", "H2MT")]
story += [P("The current app is safe for the localhost SIH prototype boundary, but it is not ready to expose directly to the public internet: it has no auth layer, public reset/case routes, no rate limiting, no durable MailTrace service, and no MailTrace route in the existing Caddy config. A real hosted demo needs an access gate or allow-list, upload limits, protected reset, rate limits, loopback app binding behind TLS, persistent service management, backups, and a separate subdomain/VM.", "CalloutMT")]

# 12 — Verification and source map.
story += section("11. What was verified for this walkthrough")
story += [P("Live checks", "H2MT")]
story += make_table([
    ["Check", "Observed result"],
    ["UI landing", "HTTP 200; eight sample buttons and .eml file input rendered."],
    ["04 case", "64 / SPOOF; reasons, map, evidence, PDF and Qwen advisory visible."],
    ["07 → 08 graph", "2 nodes / 1 edge; caption derived from API shared indicators."],
    ["Raw upload", "01_clean.eml → 8 / CLEAN; SHA-256 evidence stored; advisory available."],
    ["Mobile", "390px viewport; scrollWidth equals clientWidth; no console errors."],
    ["API", "Health 200; eight samples; case/evidence/masked/PDF routes respond."],
    ["Regression", "38 tests passed; Python compilation, shell syntax and source diff checks passed."],
], [48 * mm, 126 * mm], small=True)
story += [P("Source map", "H2MT")]
story += make_table([
    ["File", "Role"],
    ["app.py", "FastAPI routes and orchestration."],
    ["mailtrace/parse.py", "MIME parsing, auth evidence, hops, origin, URLs and hashes."],
    ["mailtrace/score.py", "Fixed points, label order and uncertainty text."],
    ["mailtrace/graph_store.py", "Meaningful shared-indicator graph rules and captions."],
    ["mailtrace/store.py", "SQLite persistence and hash-checked evidence storage."],
    ["mailtrace/llm_assist.py", "Redaction, Groq request, strict JSON normalization and fallback."],
    ["mailtrace/pdf_report.py", "Case PDF generation."],
    ["ui/index.html", "Rendered dossier UI and API-derived graph caption."],
    ["tests/test_pipeline.py", "Deterministic, graph, PDF, privacy and Qwen regression coverage."],
], [58 * mm, 116 * mm], small=True)
story += [P("Final status", "H2MT")]
story += [P("The local SIH prototype is ready to demonstrate on a laptop/VM. The optional bots and Qwen route are live and advisory. The generated six-slide submission deck still needs the registered Team ID and Team Name inserted into its title slide before upload; hosting publicly is not required for the idea round.", "CalloutMT")]


doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm,
    topMargin=18 * mm, bottomMargin=17 * mm,
    title="MailTrace — How the SIH26106 Prototype Works",
    author="MailTrace team",
)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(OUT)
