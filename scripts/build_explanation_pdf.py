from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
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
OUT = ROOT / "docs" / "MailTrace_Explanation.pdf"

PAPER = colors.HexColor("#F3EEE4")
INK = colors.HexColor("#1C1814")
MUTED = colors.HexColor("#6B6358")
RUST = colors.HexColor("#B33A2A")
LINE = colors.HexColor("#C9BFB0")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Times-Bold",
    fontSize=28, leading=32, textColor=INK, alignment=TA_CENTER,
    spaceAfter=8 * mm,
))
styles.add(ParagraphStyle(
    name="CoverSub", parent=styles["Normal"], fontName="Helvetica",
    fontSize=13, leading=18, textColor=MUTED, alignment=TA_CENTER,
    spaceAfter=6 * mm,
))
styles.add(ParagraphStyle(
    name="H1MT", parent=styles["Heading1"], fontName="Times-Bold",
    fontSize=18, leading=22, textColor=INK, spaceBefore=3 * mm,
    spaceAfter=4 * mm,
))
styles.add(ParagraphStyle(
    name="H2MT", parent=styles["Heading2"], fontName="Times-Bold",
    fontSize=12, leading=15, textColor=RUST, spaceBefore=3 * mm,
    spaceAfter=2 * mm,
))
styles.add(ParagraphStyle(
    name="BodyMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.4, leading=13.2, textColor=INK, spaceAfter=2.5 * mm,
))
styles.add(ParagraphStyle(
    name="SmallMT", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8, leading=10.5, textColor=MUTED, spaceAfter=1.5 * mm,
))
styles.add(ParagraphStyle(
    name="CodeMT", parent=styles["Code"], fontName="Courier",
    fontSize=7.8, leading=10.2, textColor=INK, backColor=colors.HexColor("#EAE2D5"),
    borderColor=LINE, borderWidth=0.5, borderPadding=5, leftIndent=2,
    rightIndent=2, spaceBefore=2 * mm, spaceAfter=3 * mm,
))
styles.add(ParagraphStyle(
    name="CalloutMT", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=10, leading=14, textColor=INK, backColor=colors.HexColor("#E9D8CF"),
    borderColor=RUST, borderWidth=0.8, borderPadding=7, spaceBefore=2 * mm,
    spaceAfter=3 * mm,
))


def para(text, style="BodyMT"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph("- " + escape(text), styles["BodyMT"])


def code(text):
    return Preformatted(text, styles["CodeMT"])


def table(data, widths):
    converted = []
    for row in data:
        converted.append([
            cell if isinstance(cell, Paragraph) else para(str(cell), "SmallMT")
            for cell in row
        ])
    t = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RUST),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F3EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont("Courier", 7.5)
    canvas.drawString(18 * mm, 10 * mm, "MailTrace | SIH26106 | local analyst lab")
    canvas.drawRightString(192 * mm, 10 * mm, f"page {doc.page}")
    canvas.restoreState()


story = []
story += [Spacer(1, 28 * mm), para("MailTrace", "CoverTitle")]
story += [para("Complete product explanation and testing guide", "CoverSub")]
story += [para("SIH26106 - Explainable email threat detection with origin and campaign forensics", "CoverSub")]
story += [Spacer(1, 12 * mm)]
story += [para("Upload a saved email. See the evidence behind its risk, probable hosting infrastructure and campaign relationships.", "CalloutMT")]
story += [Spacer(1, 8 * mm)]
story += [para("This document describes the current working prototype, the exact demo flow, the eight crafted samples, test commands, API routes and the boundaries that must be stated honestly.", "BodyMT")]
story += [Spacer(1, 20 * mm)]
story += [para("Current verified state: 5 automated tests passing; live API health 200; eight sample analyses; campaign graph 2 nodes / 1 edge; PDF export working.", "SmallMT")]
story += [PageBreak()]

story += [para("1. What MailTrace is", "H1MT")]
story += [para("MailTrace is a local-first email analyst lab. It is designed for an investigator or helpdesk analyst who has received a suspicious saved .eml file and needs more than a simple spam/not-spam answer.")]
story += [code(".eml file\n  -> exact-byte hash\n  -> MIME/header/body parsing\n  -> authentication evidence\n  -> sender alignment checks\n  -> Received-hop analysis\n  -> offline domain and IP context\n  -> explainable score and label\n  -> local case storage\n  -> campaign correlation\n  -> forensic PDF")]
story += [para("The core value is explainability. The analyst can see which fields caused the warning, what infrastructure appears in the headers, which other messages share indicators and what evidence fingerprint belongs to the uploaded file.")]
story += [para("It is not a Gmail replacement, a mail gateway, an antivirus sandbox or a tool that claims to locate a human attacker.", "CalloutMT")]

story += [para("2. End-to-end data flow", "H1MT")]
flow_rows = [
    ["Stage", "What happens", "Output"],
    ["Capture", "The exact uploaded .eml bytes are read locally.", "SHA-256, byte size, filename"],
    ["Extract", "Python email MIME parser reads headers, text/plain body, URLs and attachments.", "Structured parsed email"],
    ["Explain", "Authentication results, alignment, domain age, content cues and origin context are combined.", "Reasons, score, label"],
    ["Connect", "Stored cases are compared for shared domains, Reply-To values and origin IPs.", "Campaign graph"],
    ["Report", "The case is rendered as a one-page A4 PDF.", "Portable evidence summary"],
]
story += [table(flow_rows, [28 * mm, 96 * mm, 55 * mm])]

story += [para("3. What each code component does", "H1MT")]
component_rows = [
    ["File", "Responsibility"],
    ["app.py", "FastAPI routes, orchestration, uploads, sample analysis, case retrieval, graph and PDF endpoints."],
    ["mailtrace/parse.py", "Parses email fields, authentication evidence, URLs, Received hops, origin and hashes."],
    ["mailtrace/score.py", "Transparent weighted score and CLEAN/SPOOF/PHISH/BEC label."],
    ["mailtrace/intel.py", "Reads offline domain intelligence from data/whois_cache.json."],
    ["mailtrace/graph_store.py", "Builds the NetworkX undirected graph from shared indicators."],
    ["mailtrace/store.py", "Persists parsed case JSON, score and hash in SQLite."],
    ["mailtrace/pdf_report.py", "Creates the one-page forensic case PDF."],
    ["ui/index.html", "Upload/sample screen, case view, reasons, map, graph, hash footer and PDF button."],
    ["scripts/write_samples.py", "Regenerates the eight safe, local crafted .eml files."],
    ["tests/test_pipeline.py", "Parser, scoring, complete corpus, graph, PDF and attachment-hash tests."],
]
story += [table(component_rows, [48 * mm, 131 * mm])]
story += [PageBreak()]

story += [para("4. Email parsing and evidence", "H1MT")]
story += [para("MailTrace uses Python's standard email parser. It does not execute the message or treat the email body as a program.")]
for item in [
    "From display name, address and domain",
    "Reply-To and Return-Path values and their domains",
    "Subject and Message-ID",
    "Plain-text body, limited to the first 4,000 characters",
    "URLs found in the body or From field, deduplicated to 20",
    "Received headers and extracted IPv4 addresses",
    "Authentication-Results, Received-SPF and ARC authentication evidence",
    "Attachment filename, MIME type, size and SHA-256 metadata, limited to 20",
]:
    story += [bullet(item)]
story += [para("Attachments are metadata-only in this build: MailTrace hashes them but does not open, execute or detonate them. The main UI and current PDF focus on the header, hop, scoring and campaign evidence.", "CalloutMT")]

story += [para("5. Sender and authentication checks", "H1MT")]
story += [para("MailTrace compares the visible identity with the delivery identity. A message may display an official name while using a Gmail address, a different Reply-To domain or a different Return-Path domain.")]
for item in [
    "Gmail display-name heuristic: a Gmail address wearing a longer official-looking display title is flagged.",
    "Reply-To mismatch: the domain receiving the reply differs from the visible From domain.",
    "Return-Path mismatch: the bounce/delivery domain differs from the visible From domain.",
    "SPF, DKIM and DMARC are displayed as pass, fail, none or unknown when those results appear in the headers.",
]:
    story += [bullet(item)]
story += [para("Important: the demo reads authentication results already written in the .eml. It does not yet perform live DNS lookup or independent cryptographic DKIM verification. In production, trusted receiving infrastructure should perform those checks.", "CalloutMT")]

story += [para("6. Received hops and probable origin", "H1MT")]
story += [para("MailTrace reads each Received header, extracts public IPv4 addresses, ignores common local addresses and uses the last public hop in normal header order as the earliest reliable public hop.")]
story += [para("The demo uses a small offline IP table so the same sample always produces the same result:")]
ip_rows = [
    ["IP", "Demo context"],
    ["103.25.60.12", "Chandigarh / campus-like organisation"],
    ["18.184.10.20", "Frankfurt / AWS / cloud"],
    ["52.94.76.10", "Dublin / AWS / cloud"],
    ["8.8.8.8", "Unknown / public DNS"],
    ["185.199.108.153", "Unknown / Fastly CDN"],
]
story += [table(ip_rows, [48 * mm, 131 * mm])]
story += [para("Correct wording: 'The earliest reliable public hop appears to be hosted in Frankfurt by AWS.' Incorrect wording: 'The attacker is in Frankfurt.' IP geolocation describes network infrastructure, not a person's GPS location.", "CalloutMT")]
story += [PageBreak()]

story += [para("7. Offline domain intelligence", "H1MT")]
story += [para("The current domain cache is data/whois_cache.json. It contains reproducible demo facts such as approximate age, registrar label and a note. No live WHOIS request is made during the demonstration.")]
for item in [
    "pec.edu.in: established college domain",
    "gmail.com: consumer mailbox",
    "paypa1.com: lookalike and four days old in the demo cache",
    "pec-edu.in: lookalike of pec.edu.in and six days old",
    "mail-secure.net: young throwaway-style domain and twelve days old",
]:
    story += [bullet(item)]
story += [para("A cached domain younger than 30 days contributes a young-domain signal. A young domain is suspicious context, not proof of criminality.")]

story += [para("8. Explainable risk scoring", "H1MT")]
story += [para("The score starts at 8 and adds fixed points for observed signals. It is clamped to 0-100. It is a risk indicator, not a calibrated probability and not an accuracy percentage.")]
score_rows = [
    ["Signal", "Points"],
    ["Gmail address wearing official-looking title", "+28"],
    ["Reply-To domain mismatch", "+18"],
    ["Return-Path domain mismatch", "+10"],
    ["SPF failure", "+22"],
    ["DKIM failure", "+12"],
    ["DMARC failure", "+12"],
    ["Lookalike domain", "+20"],
    ["Young cached domain", "+14"],
    ["Cloud-origin hop", "+10"],
    ["Password/login language", "+16"],
    ["Invoice/payment redirect language", "+18"],
    ["Urgency language", "+8"],
]
story += [table(score_rows, [125 * mm, 54 * mm])]
story += [para("The UI prints up to six strongest reasons. A signal can contribute to the score even when the reason list has reached that display limit.")]

story += [para("9. Labels", "H1MT")]
for item in [
    "CLEAN: low score and no major spoof/phishing cue.",
    "SPOOF: sender alignment or authentication problem.",
    "PHISH: high score involving a lookalike domain or password/login lure.",
    "BEC: payment, invoice or account-change pattern. The BEC rule is checked before the broader spoof rule.",
]:
    story += [bullet(item)]
story += [PageBreak()]

story += [para("10. Campaign graph", "H1MT")]
story += [para("NetworkX creates one node per analyzed filename. Two cases are connected when they share a meaningful indicator:")]
for item in [
    "sender, Reply-To or Return-Path domain",
    "full Reply-To address",
    "probable origin IP",
]:
    story += [bullet(item)]
story += [code("07 cloud hops  ----  Reply-To + same hop + domain  ----  08 campaign twin")]
story += [para("The visible graph is currently a custom inline SVG because raw network canvases were too dense for slide and projector viewing. The graph caption deliberately says: shared indicators, not identity proof.")]

story += [para("11. Local storage", "H1MT")]
story += [para("Cases are saved in data/mailtrace.db. The database contains the case ID, filename, SHA-256, parsed JSON payload and creation time. It persists across server restarts.")]
story += [para("Restarting the server does not clear old cases. Use the reset endpoint before a clean campaign demonstration:")]
story += [code("curl -X POST http://127.0.0.1:8777/api/reset")]

story += [para("12. Forensic PDF", "H1MT")]
story += [para("The case PDF is a one-page A4 summary containing the case ID, score, label, sender, Reply-To, reasons, origin hop, up to eight Received hops, campaign links, exact-file SHA-256 and the hosting-not-GPS disclaimer.")]
story += [para("It is a portable case summary, not a replacement for preserving the original email file. The report is generated from the stored parsed case.")]

story += [para("13. The teammate ML files", "H1MT")]
story += [para("The teammate model_A.pkl and tfidf_vectorizer.pkl are not loaded by the current application. They are a traditional TF-IDF plus logistic-regression body classifier for ham/spam language. They cannot by themselves trace Received hops, inspect sender alignment, validate authentication or correlate campaigns.")]
story += [para("They can be added later as an optional body-language signal, but the forensic parser, authentication evidence, origin context, graph and report are the main SIH26106 product.", "CalloutMT")]
story += [PageBreak()]

story += [para("14. Eight demo samples and expected results", "H1MT")]
sample_rows = [
    ["Sample", "Expected", "What it demonstrates"],
    ["01_clean.eml", "CLEAN / 8", "Aligned college sender, all auth pass, Chandigarh campus-like hop."],
    ["02_display_spoof.eml", "SPOOF / 100", "Official-looking display name on Gmail, mismatched Reply-To and auth failures."],
    ["03_lookalike.eml", "PHISH / 98", "paypa1 lookalike, failed auth, young domain and Dublin cloud hop."],
    ["04_spf_fail.eml", "SPOOF / 64", "Claimed college sender but SPF, DKIM and DMARC fail; Frankfurt AWS hop."],
    ["05_bec_invoice.eml", "BEC / 100", "Urgent payment/account-change pattern with mismatched reply path."],
    ["06_cred_phish.eml", "PHISH / 100", "Mailbox suspension/login lure, lookalike domain and failed auth."],
    ["07_cloud_hops.eml", "SPOOF / 66", "Three Received hops and probable Frankfurt AWS origin."],
    ["08_campaign_twin.eml", "SPOOF / 66", "Second email sharing Reply-To, domain and origin IP with sample 07."],
]
story += [table(sample_rows, [40 * mm, 30 * mm, 109 * mm])]

story += [para("15. How to start it", "H1MT")]
story += [code("cd /root/sih-mailtrace\n\n# easiest path\nbash run.sh\n\n# or manually\npython3 scripts/write_samples.py\npython3 -m pytest -q\npython3 -m uvicorn app:app --host 127.0.0.1 --port 8777")]
story += [para("Open http://127.0.0.1:8777. The run script installs requirements, regenerates samples, runs tests and starts Uvicorn on localhost port 8777.")]

story += [para("16. Best click-by-click test", "H1MT")]
for i, item in enumerate([
    "Reset old cases with the curl command above.",
    "Open the local URL and click 04_spf_fail.eml.",
    "Verify SPOOF, score 64, SPF/DKIM/DMARC failures, Frankfurt/AWS origin, hop list and map.",
    "Click 07_cloud_hops.eml and inspect the three Received hops.",
    "Click 08_campaign_twin.eml and verify the two-node graph and one relationship caption.",
    "Click Download case PDF and verify the case ID, reasons, origin, campaign link and SHA-256.",
    "Finally reset again if the next person needs a clean demo.",
], 1):
    story += [para(f"{i}. {escape(item)}", "BodyMT")]
story += [PageBreak()]

story += [para("17. API test checklist", "H1MT")]
api_rows = [
    ["Action", "Command or route", "Expected"],
    ["Health", "GET /api/health", "200 and product MailTrace"],
    ["Samples", "GET /api/samples", "Eight .eml files"],
    ["Reset", "POST /api/reset", "cleared: true"],
    ["Sample analysis", "POST /api/analyze-sample/04_spf_fail.eml", "SPOOF / 64"],
    ["Raw upload", "POST /api/analyze with multipart file", "Case JSON and ID"],
    ["Stored cases", "GET /api/cases", "IDs, filenames and scores"],
    ["Graph", "GET /api/graph", "nodes and shared-indicator edges"],
    ["Case", "GET /api/case/{id}", "Full parsed case JSON"],
    ["PDF", "GET /api/case/{id}/pdf", "application/pdf"],
    ["Bad sample", "POST unknown sample", "404"],
    ["Empty upload", "POST empty file", "400"],
]
story += [table(api_rows, [38 * mm, 86 * mm, 55 * mm])]
story += [para("Useful direct commands:")]
story += [code("curl http://127.0.0.1:8777/api/health\ncurl http://127.0.0.1:8777/api/samples\ncurl -X POST http://127.0.0.1:8777/api/analyze-sample/04_spf_fail.eml\ncurl -F \"file=@samples/05_bec_invoice.eml\" http://127.0.0.1:8777/api/analyze\npython3 -m pytest -q")]

story += [para("18. Current verified result", "H1MT")]
for item in [
    "Automated suite: 5 passed.",
    "Live health: HTTP 200 with product MailTrace and problem statement SIH26106.",
    "All eight sample endpoints analyzed successfully.",
    "Campaign test: 2 nodes, 1 edge, caption Reply-To + same hop + domain.",
    "PDF endpoint: HTTP 200, application/pdf.",
    "Attachment test: metadata and SHA-256 verified without execution.",
]:
    story += [bullet(item)]

story += [para("19. Boundaries and future production work", "H1MT")]
for item in [
    "No Gmail or Outlook ingestion in the SIH demo.",
    "No live DNS-based SPF/DKIM/DMARC verification yet.",
    "No live WHOIS or global reputation service.",
    "Offline demo IP data is not a full GeoIP/ASN database.",
    "No malware detonation or antivirus engine.",
    "No exact attacker location or person attribution.",
    "No automatic quarantine, blocking or SOC alert integration.",
    "The score is rule fusion, not a calibrated probability.",
    "The local server binds to 127.0.0.1 and has no production authentication layer.",
]:
    story += [bullet(item)]
story += [PageBreak()]
story += [para("20. One-minute handoff for the team", "H1MT")]
story += [para("Use this short explanation when a teammate or judge asks what MailTrace actually does:")]
story += [para("1. We upload a saved .eml file instead of connecting to a live mailbox.", "BodyMT")]
story += [para("2. MailTrace preserves an exact SHA-256 fingerprint and parses the sender, Reply-To, Return-Path, authentication evidence, body, URLs, attachments and Received hops.", "BodyMT")]
story += [para("3. It explains the risk with visible reasons, estimates the hosting infrastructure behind the earliest reliable public hop and shows the hop path.", "BodyMT")]
story += [para("4. When multiple emails share a Reply-To, domain or origin IP, it creates a campaign lead. That is correlation, not proof of identity.", "BodyMT")]
story += [para("5. It stores the case locally and exports a portable forensic PDF containing the evidence summary and file fingerprint.", "BodyMT")]
story += [Spacer(1, 5 * mm)]
story += [para("Say this exactly:", "H2MT")]
story += [para("MailTrace turns a suspicious saved email into an explainable case file. It tells us what the message claims, what the headers reveal, where the infrastructure appears to be hosted, which other messages share indicators and what evidence should be preserved.", "CalloutMT")]
story += [para("Never say: 'we found the hacker' or 'the IP proves the attacker's location.'", "SmallMT")]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=16 * mm, bottomMargin=16 * mm, title="MailTrace complete explanation",
    author="MailTrace team",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
