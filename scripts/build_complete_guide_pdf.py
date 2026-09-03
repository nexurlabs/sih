#!/usr/bin/env python3
"""Build one teammate-facing PDF from the complete guide + screenshot proofs."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "shots" / "explainer"
OUT = ROOT / "docs" / "MailTrace_Complete_Guide.pdf"

PAPER = colors.HexColor("#F3EEE4")
INK = colors.HexColor("#1C1814")
MUTED = colors.HexColor("#6B6358")
RUST = colors.HexColor("#B33A2A")
RULE = colors.HexColor("#C9BFB0")
PALE = colors.HexColor("#EFE6D6")


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Kicker", fontName="Times-Bold", fontSize=9, textColor=RUST, spaceAfter=6, leading=12))
    s.add(ParagraphStyle("H1", fontName="Times-Bold", fontSize=22, leading=26, textColor=INK, spaceAfter=10, spaceBefore=4))
    s.add(ParagraphStyle("H2", fontName="Times-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=12, spaceAfter=6))
    s.add(ParagraphStyle("Body", fontName="Times-Roman", fontSize=10.5, leading=14.5, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6))
    s.add(ParagraphStyle("Note", fontName="Times-Italic", fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=8))
    s.add(ParagraphStyle("Cap", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10, spaceBefore=3))
    s.add(ParagraphStyle("Term", fontName="Times-Bold", fontSize=10.5, leading=14, textColor=INK, spaceBefore=4, spaceAfter=1))
    s.add(ParagraphStyle("Def", fontName="Times-Roman", fontSize=10, leading=14, textColor=INK, leftIndent=8, spaceAfter=6))
    s.add(ParagraphStyle("Cell", fontName="Times-Roman", fontSize=8.5, leading=11.5, textColor=INK))
    s.add(ParagraphStyle("CellB", fontName="Times-Bold", fontSize=8.5, leading=11.5, textColor=INK))
    s.add(ParagraphStyle("Cmd", fontName="Courier", fontSize=8, leading=11, textColor=INK, backColor=PALE, leftIndent=4, rightIndent=4, spaceAfter=8, spaceBefore=4))
    s.add(ParagraphStyle("CoverSub", fontName="Times-Italic", fontSize=12, leading=16, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8))
    return s


def shot(name: str, max_h=118 * mm) -> list:
    path = SHOTS / name
    if not path.is_file():
        return [Paragraph(f"[missing screenshot: {name}]", styles()["Note"])]
    img = Image(str(path))
    page_w = A4[0] - 36 * mm
    img._restrictSize(page_w, max_h)
    return [img]


def table(rows, col_widths=None):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALE),
                ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setStrokeColor(INK)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, A4[1] - 9 * mm, "MAILTRACE  ·  SIH26106  ·  COMPLETE GUIDE")
    canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 9 * mm, "NexurLabs / PEC")
    canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
    canvas.drawCentredString(A4[0] / 2, 7 * mm, f"page {doc.page}  ·  screenshot-backed walkthrough  ·  not a legal report")
    canvas.restoreState()


def build():
    S = styles()
    story = []
    P = lambda t, st="Body": Paragraph(t, S[st])

    story += [
        P("SIH26106  ·  EMAIL THREAT  ·  GEO  ·  FORENSICS", "Kicker"),
        P("MailTrace", "H1"),
        P("Complete teammate guide — what we built, every term, and the screenshots that prove it.", "CoverSub"),
        P("This PDF is the whole story in one file. You do not need GitHub to walk someone through it. The live lab is a local-first analyst tool: upload a saved <b>.eml</b>, get a score, reasons, hop map, campaign graph, hashed evidence, and a case PDF."),
        P("It is not Gmail. It does not read inboxes. It does not send phishing. Geo is hosting city / ISP of a mail server, not a person's GPS."),
        Spacer(1, 4 * mm),
        *shot("01_landing.png", 95 * mm),
        P("Figure 1 — Landing page. Sample chips + .eml upload.", "Cap"),
    ]

    story += [
        P("1. What it is, in one minute", "H2"),
        P("Give MailTrace a saved email. It answers five questions:"),
        P("1. Is it shady? Score 0–100 and a label: CLEAN, SPOOF, PHISH, or BEC.<br/>2. Why? Plain reasons such as SPF fail or Reply-To ≠ From.<br/>3. Where did it travel? The Received hop chain and the probable first public hop.<br/>4. Is it part of a campaign? A graph linking emails that share Reply-To / domain / hop.<br/>5. Proof? SHA-256 of the exact uploaded bytes + a downloadable PDF case file."),
        P("Think: post-mortem lab, not a spam filter.", "Note"),
        P("2. Why this exists", "H2"),
        P("SIH26106 asks for an AI-powered platform that detects fraudulent email and helps an investigator explain origin and campaign links. Real pain: a mail that looks like Exam Cell but came from a rogue host; a vendor asking to wire money to a new account (BEC); spam filters that only say spam/not-spam."),
        P("So we built an explainable laptop lab. No Gmail login required. Teammates can demo it from a saved file."),
        P("3. What it is not", "H2"),
        P("Not a trained 99% spam classifier. Not Gmail/Outlook ingest. Not a human tracker. Not full DKIM cryptographic verification (we read header stamps, and we can look up live SPF/DMARC TXT). Not court-grade chain of custody. Not “we found the attacker.” The score is a risk indicator, not a probability."),
    ]

    story.append(PageBreak())
    story += [
        P("4. Run it on your own PC (from GitHub)", "H2"),
        P("The code is on GitHub: <b>https://github.com/nexurlabs/sih</b> (public). Clone it, then follow the Windows steps below. Mac/Linux notes are at the end of this section. You do not need the IBM VM. You do not need Gmail."),
        P("Step A — install three things (once)", "H2"),
        P("1. <b>Python 3.11 or 3.12</b> from python.org → Downloads → Windows. On the installer, tick <b>Add python.exe to PATH</b>. Finish, then close PowerShell if it was open and open a new one.<br/>2. <b>Git</b> from git-scm.com (Next, Next, Next is fine). Or install GitHub Desktop if you hate terminals.<br/>3. Confirm Python works:"),
        Preformatted("python --version\n# expect: Python 3.11.x or 3.12.x", S["Cmd"]),
        P("If that says “not recognized”, PATH was not ticked. Reinstall Python and tick the box."),
        P("Step B — clone the repo", "H2"),
        P("In PowerShell:"),
        Preformatted("cd $HOME\\Desktop\ngit clone https://github.com/nexurlabs/sih.git\ncd sih", S["Cmd"]),
        P("GitHub Desktop: File → Clone repository → nexurlabs/sih → clone to Desktop, then open that folder in a terminal."),
        P("Step C — make a venv (do not skip)", "H2"),
        P("A venv is a private Python just for this project, so you do not wreck other stuff."),
        Preformatted("python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1", S["Cmd"]),
        P("If PowerShell screams about execution policy, run this once, then Activate again:"),
        Preformatted("Set-ExecutionPolicy -Scope CurrentUser RemoteSigned", S["Cmd"]),
        P("CMD instead of PowerShell: run <font face='Courier'>.venv\\Scripts\\activate.bat</font>. You should see <b>(.venv)</b> at the left of the prompt."),
        P("Step D — install, test, start", "H2"),
        Preformatted("pip install -r requirements.txt\npython scripts\\write_samples.py\npython scripts\\train_nlp.py\npytest -q\npython -m uvicorn app:app --host 127.0.0.1 --port 8777", S["Cmd"]),
        P("Leave that window open. Open Chrome/Edge and go to <b>http://127.0.0.1:8777</b> — that is your copy, on your laptop. Stop it later with Ctrl+C in the same window. After Activate you can also run <font face='Courier'>.\\run.ps1</font>."),
        P("If <font face='Courier'>python</font> opens the Microsoft Store instead of Python, use <font face='Courier'>py -3</font> in every command (py -3 -m venv .venv, py -3 -m uvicorn …).", "Note"),
        P("Step E — click the demo (this is how you use it)", "H2"),
        P("1. Click <b>04_spf_fail.eml</b> → stamp should be <b>64 / SPOOF</b>. Point at SPF/DKIM/DMARC fail and Frankfurt (hosting, not a person).<br/>2. Click <b>01_clean.eml</b> → <b>8 / CLEAN</b>. Same engine, honest low score.<br/>3. Click <b>07_cloud_hops.eml</b>, then <b>08_campaign_twin.eml</b> → those two dots get one line (campaign candidate). Extra samples just add more dots.<br/>4. Scroll: Local NLP box, Live DNS (SPF/DMARC TXT), origin map, evidence hash, Download case PDF.<br/>5. Optional: upload any saved .eml (Gmail → three dots → Show original → Download)."),
        P("If pytest is red, or the page will not open, you skipped Activate or the uvicorn window died. Start Step D again from pip.", "Note"),
        P("Optional: live DNS + GeoIP", "H2"),
        P("In the <b>same</b> PowerShell window, before uvicorn (Windows does not auto-read .env unless you use Git Bash + ./run.sh):"),
        Preformatted("$env:MAILTRACE_LIVE_DNS=\"1\"\n$env:MAILTRACE_LIVE_GEO=\"1\"\npython -m uvicorn app:app --host 127.0.0.1 --port 8777", S["Cmd"]),
        P("MaxMind <font face='Courier'>.mmdb</font> files are gitignored (they are big / licensed). Demo IPs still pin Frankfurt. For random real IPs, put <font face='Courier'>GeoLite2-City.mmdb</font> (and optionally ASN) in <font face='Courier'>data/</font> — ask a teammate for the files, do not commit them."),
        P("Optional: Qwen notes (not the score)", "H2"),
        P("The 0–100 stamp is header rules plus the <b>local wording check</b> (the NLP box). That model lives in the repo and runs on the laptop. Qwen is a separate sidebar that writes notes. No Groq key → no Qwen box, same score. If you want the notes:"),
        Preformatted("python scripts\\set_groq_key.py", S["Cmd"]),
        P("Mac / Linux (same idea)", "H2"),
        Preformatted("python3 -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\npython scripts/write_samples.py\npytest -q\npython -m uvicorn app:app --host 127.0.0.1 --port 8777", S["Cmd"]),
        P("Do not: connect Gmail, send phishing, claim you located a person, or push secrets / .env / .mmdb."),
    ]

    story += [
        P("5. How to use it (30 seconds, once it is open)", "H2"),
        P("Open the app → click <b>04_spf_fail.eml</b> → you should see <b>64 / SPOOF</b>. Then click <b>07_cloud_hops.eml</b> and <b>08_campaign_twin.eml</b> → the graph shows two nodes and one edge. Download the case PDF. On the private host you can also drop a real saved .eml."),
        *shot("02_case_spf_fail.png", 125 * mm),
        P("Figure 2 — Case 04. Stamp 64 SPOOF, reasons, hop list, Frankfurt origin map, wording check, live DNS, evidence.", "Cap"),
    ]

    story.append(PageBreak())
    story += [
        P("6. What the app looks like", "H2"),
        P("Same screens you get after you start the app and click a sample."),
        *shot("case_header.png", 55 * mm),
        P("Figure 3 — Case header: 64 SPOOF, SPF/DKIM/DMARC fail pills.", "Cap"),
        *shot("case_nlp.png", 42 * mm),
        P("Figure 4 — Local wording check. Reads the email text and can add a few points to the score.", "Cap"),
        *shot("case_live_dns.png", 42 * mm),
        P("Figure 5 — Live DNS. pec.edu.in has no published SPF/DMARC TXT (absent). That is a real finding, not a lookup bug.", "Cap"),
        *shot("case_auth_source.png", 32 * mm),
        P("Figure 6 — Auth source vs live DNS. Header-stated = what the .eml already said. Independent DKIM crypto = no.", "Cap"),
        *shot("case_assist.png", 80 * mm),
        P("Figure 7 — Qwen analyst assist. Advisory only. It cannot change the score or label. Mentions AWS Frankfurt as hosting.", "Cap"),
    ]

    story.append(PageBreak())
    story += [
        P("Campaign graph — 07 then 08", "H2"),
        P("Reset the lab, analyse 07_cloud_hops.eml, then 08_campaign_twin.eml. They share Reply-To + hop + domain, so the graph draws exactly two nodes and one edge. Shared indicators = campaign candidate. Not proof of the same human."),
        *shot("03_campaign_graph.png", 118 * mm),
        P("Figure 8 — Full case with campaign graph after 07 + 08.", "Cap"),
        *shot("graph_focus.png", 55 * mm),
        P("Figure 9 — Graph close-up. Shared domain / hop / Reply-To. Not proof of the same human.", "Cap"),
        *shot("case_report_08.png", 95 * mm),
        P("Figure 10 — Exported forensic PDF for a case. Hash, auth, hops, graph note, uncertainty.", "Cap"),
        *shot("04_mobile_landing.png", 70 * mm),
        P("Figure 11 — Phone-width landing. Same dossier, not a broken desktop squeeze.", "Cap"),
    ]

    story.append(PageBreak())
    story += [
        P("7. Every term, in plain language", "H2"),
    ]
    terms = [
        (".eml", "A saved email file. Full headers + body. Gmail: Show original → Download."),
        ("From / To / Subject", "Who claims to send, who receives, the title. Easy to fake."),
        ("Reply-To", "Where a reply actually goes. Scam trick: From looks official, Reply-To is a Gmail."),
        ("Return-Path", "Where bounces go. Should match From. Mismatch is a signal."),
        ("Message-ID", "A unique-ish id stamped by a mail system. Useful in evidence, not identity."),
        ("Received chain", "Each server that touched the mail adds a Received line. Read from the bottom up. The last public hop is our heuristic “origin.”"),
        ("Public hop", "A Received IP that is not 127.x / 10.x / 192.168.x. Those private ones are internal."),
        ("SPF", "Sender Policy Framework. The domain publishes which servers may send as it. Fail = this server is not on the list."),
        ("DKIM", "A signature in the headers. We report the header-stated result. We do not re-check the crypto."),
        ("DMARC", "Domain policy: what to do if SPF/DKIM fail. Fail = the domain’s own policy was violated."),
        ("Header-stated vs live DNS", "Header-stated = what the .eml already says. Live DNS = we query TXT for SPF and _dmarc. Live is publication, not DKIM crypto."),
        ("Alignment", "Do From, Reply-To, and Return-Path domains match? Mismatch is a spoof cue."),
        ("Lookalike domain", "paypa1 vs paypal, pec-edu.in vs pec.edu.in. Eyes miss it."),
        ("BEC", "Business Email Compromise. Urgent payment / new bank account. Often no malware, just pressure."),
        ("Phish", "Credential theft. Verify password, login to continue, account suspended."),
        ("Spoof", "Fake sender identity. The envelope lies."),
        ("Score 0–100", "Risk meter. Starts at 8, adds points per signal. 64 is not “64% sure.”"),
        ("Forensic score", "The rule-based part only (SPF, Reply-To, keywords, cloud hop…)."),
        ("NLP", "Local wording model (TF-IDF + logistic regression). Reads the email text and can add a few points to the score. Different tool from the optional Qwen notes."),
        ("Qwen / Groq", "Optional LLM notes. Redacted input. Never changes the stamp."),
        ("Label", "CLEAN &lt; 45. SPOOF from header/auth. BEC if payment language. PHISH if password/lookalike + high score."),
        ("Signal", "One finding with points and a source, e.g. spf_fail +22 from message-header."),
        ("Young domain", "Offline WHOIS cache says the domain is newly registered. Burner domains."),
        ("Cloud origin", "First public hop is AWS/GCP/Azure-class, not campus mail."),
        ("GeoIP / MaxMind", "IP → city / ISP / ASN from a local MMDB. Hosting context. Not GPS of a person."),
        ("Demo IP table", "Five IPs baked into the sample .emls so 04 always shows Frankfurt. Real uploads use MaxMind."),
        ("Campaign graph", "NetworkX. Dots = emails. Line = shared Reply-To / domain combo. Never IP-only. Never “same person.”"),
        ("SHA-256", "Fingerprint of the exact file you uploaded. One byte change → different hash."),
        ("Custody events", "Local log: received → hashed → stored. Prototype, not legal-grade."),
        ("Masked view", "Emails shown as j***@domain so you can share a case without the full address."),
        ("Deterministic", "Same .eml, same forensic score. No dice rolls."),
        ("Public demo vs private", "Public path is read-only samples. Private (auth) allows upload, PDF, evidence."),
    ]
    for name, defn in terms:
        story.append(P(name, "Term"))
        story.append(P(defn, "Def"))

    story.append(PageBreak())
    story += [
        P("8. The eight demo emails (pinned results)", "H2"),
        P("These files live in samples/. They are crafted so a judge can see each threat class. The engine is the same as for a real upload."),
    ]
    cell = lambda t: Paragraph(t, S["Cell"])
    cellb = lambda t: Paragraph(t, S["CellB"])
    rows = [[cellb("file"), cellb("score"), cellb("label"), cellb("what it teaches")]]
    fixtures = [
        ("01_clean.eml", "8", "CLEAN", "Normal mail, aligned auth"),
        ("02_display_spoof.eml", "100", "SPOOF", "Gmail wearing an official title"),
        ("03_lookalike.eml", "98", "PHISH", "paypa1-style lookalike + login lure"),
        ("04_spf_fail.eml", "64", "SPOOF", "Server not allowed to send as pec.edu.in"),
        ("05_bec_invoice.eml", "100", "BEC", "Urgent wire / new bank account"),
        ("06_cred_phish.eml", "100", "PHISH", "Verify password + urgency (+ NLP)"),
        ("07_cloud_hops.eml", "66", "SPOOF", "First hop is cloud, not campus"),
        ("08_campaign_twin.eml", "66", "SPOOF", "Twin of 07; graph links them"),
    ]
    for row in fixtures:
        rows.append([cell(x) for x in row])
    story.append(table(rows, [42 * mm, 18 * mm, 22 * mm, 88 * mm]))
    story.append(P("After 07 + 08: graph = 2 nodes, 1 edge. 01 + 04 do not link just because both mention pec.edu.in.", "Note"))

    story += [
        P("9. What happens to one email (04)", "H2"),
        P("From looks like Exam Cell &lt;notice@pec.edu.in&gt;. Received shows rogue.example [18.184.10.20]. Authentication-Results: SPF/DKIM/DMARC fail."),
        P("<b>Pipeline:</b> .eml bytes → parse_eml (headers, body, URLs, attachment metadata) → offline WHOIS cache → optional live SPF/DMARC TXT → fuse (base 8 + SPF 22 + DKIM 12 + DMARC 12 + cloud 10 = 64) → label SPOOF → NLP adds 0 on this file → Qwen note (advisory) → SQLite + hashed evidence → NetworkX graph → PDF on demand."),
        P("Why not 100? No password lure, no invoice language, no lookalike. Honest: bad auth, not a credential trap."),
        P("10. Stack (what we actually coded in)", "H2"),
    ]
    stack = [
        ["piece", "what", "why"],
        ["Language", "Python 3", "Email + tests + ML libs"],
        ["API", "FastAPI + Uvicorn", "Tiny /api/analyze, health, PDF"],
        ["Parser", "stdlib email + parse.py", "MIME, hops, HTML hrefs"],
        ["Score", "score.py rules", "Explainable; same file → same forensic score"],
        ["NLP", "sklearn TF-IDF + LogReg", "Bounded wording points, local corpus"],
        ["Graph", "NetworkX", "Campaign candidates"],
        ["Store", "SQLite + SHA-256 files", "Laptop, no extra server"],
        ["PDF", "ReportLab", "Case file download"],
        ["UI", "HTML + JS", "No React build"],
        ["Map", "Leaflet + hop list", "Tiles optional; list always works"],
        ["Geo", "MaxMind MMDB", "Real IPs get city/ISP"],
        ["Live DNS", "dnspython", "SPF/DMARC TXT when online"],
        ["Assist", "Groq Qwen", "Sidebar only"],
        ["Tests", "pytest (46+)", "Pins 04=64, 07+08 graph, auth conflict"],
    ]
    story.append(table([[cellb(a), cell(b), cell(c)] for a, b, c in stack], [28 * mm, 48 * mm, 94 * mm]))

    story += [
        P("11. Two-minute demo script for teammates", "H2"),
        P("1. “This is MailTrace. Offline email forensics. No Gmail.”<br/>2. Open 04 → 64 SPOOF. Point at SPF/DKIM/DMARC fail and Frankfurt hop (hosting, not a person).<br/>3. Open 01 → 8 CLEAN. Same engine, honest low score.<br/>4. Reset, then 07 then 08 → two nodes, one edge. Campaign candidate.<br/>5. Evidence / PDF → hashed original bytes.<br/>6. Close: “Rules decide. NLP adds a bit. Qwen only explains. Geo is a server.”"),
        P("12. Limits to say out loud", "H2"),
        P("Demo .emls are crafted. WHOIS is an offline cache. DKIM is not re-verified cryptographically. NLP is uncalibrated. pec.edu.in currently has no SPF TXT (live DNS will say absent — that’s a real finding). No mailbox gateway, no quarantine, no “we geolocated a human.”"),
        P("That’s the whole product. If they can click 04 and then 07+08 and repeat the terms above, they can present it without you in the room.", "Note"),
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="MailTrace Complete Guide — SIH26106",
        author="NexurLabs",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUT, OUT.stat().st_size)


if __name__ == "__main__":
    build()
