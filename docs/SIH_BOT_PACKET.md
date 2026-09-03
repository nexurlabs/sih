# SIH26106 / MailTrace — Bot Planning Packet

**Purpose:** source-grounded planning only. Do not edit the repository, deploy services, contact third parties, log into accounts, or broaden the product beyond the official SIH26106 scope. Read this packet and all listed PDFs before producing a plan.

**Prepared for:** the SIH Bot Mode group (`sih`).
**Working project:** `/root/sih-mailtrace`
**Official source links:**
- https://www.sih.gov.in/sih2026PS
- https://sih2026.vuce.in/ps/SIH26106

---

## 1. What we are building

MailTrace is a local-first, explainable email-threat investigation prototype for SIH problem SIH26106. It turns a saved raw email (`.eml`) into a case dossier:

```text
raw .eml
  -> exact-byte SHA-256
  -> MIME/header/body parsing
  -> authentication/alignment evidence
  -> Received-hop/origin context
  -> deterministic explainable risk score
  -> SQLite case
  -> shared-indicator campaign graph
  -> map + dossier UI + PDF report
```

The intended claim is:

> MailTrace turns a suspicious saved email into an explainable case file: it preserves the file fingerprint, extracts forensic evidence, scores the risk, shows probable hosting infrastructure, connects related cases, and exports a report.

Do not describe the current prototype as a live Gmail protection layer, a mail gateway, a trained AI model, legal-grade chain of custody, or proof of attacker identity.

Ownership/workflow: Rishabh and Lyra build the project. Teammates are expected to present/pass it later, not to own the implementation.

---

## 2. Official SIH26106 scope to validate

The current SIH portal/mirror asks for an end-to-end platform covering:

### Detection
- NLP/ML analysis of subject and body.
- Urgency, social-engineering, impersonation, phishing, BEC/payment-diversion cues.
- Suspicious links and attachments.
- Classes such as legitimate, suspicious, spoofed, phishing, and fraud-related.

### Email/header/protocol forensics
- From, Return-Path, Received, Message-ID, Reply-To.
- SPF, DKIM, and DMARC validation/evidence.
- Forged or inconsistent headers.
- Suspicious relay paths.
- Sender/infrastructure authorization.

### Origin and infrastructure intelligence
- Earliest reliable sending node.
- Originating IP.
- Country/region/city/ISP/hosting-provider context.
- Cloud/VPN/TOR/proxy/open-relay/botnet context where supportable.
- WHOIS, DNS, MX, registrar, and domain-age intelligence.

### Campaign and identity correlation
- Previous incidents, domains, IPs, aliases, reply chains, and threat intelligence.
- Blacklists/reputation sources.
- Graph-based campaign correlation.
- Confidence/uncertainty.
- Distinguish spoofed domains, compromised accounts, anonymized infrastructure, and possible direct malicious sources without overclaiming.

### Dashboard, alerting, and reports
- Near-real-time or pre-interaction alerting.
- Analyst dashboard.
- Risk score and origin confidence.
- Map and relationship graph.
- Searchable cases and campaign grouping.
- Structured forensic reports.

### Privacy/evidence/compliance
- Personal-data controls.
- Logging.
- Evidence preservation and chain of custody.
- Retention periods.
- Masking/redaction.
- Institutional/legal/incident-response suitability.

Separate every conclusion into:
1. **Confirmed official requirement** — directly supported by the PS/source.
2. **Technical inference** — necessary or strongly suggested, but not stated exactly.
3. **Proposed implementation choice** — our design decision, not an SIH mandate.
4. **Unresolved question/risk** — needs evidence, user approval, or a later experiment.

The official title wording should be copied from the currently selected portal entry at submission time; older local artifacts may contain slightly different wording.

---

## 3. Existing PDFs and editable submission artifacts

Read every applicable PDF with the file reader/PDF extractor. These are local files; do not upload them anywhere.

- `/root/sih-mailtrace/docs/sih26106_what_to_build.pdf`
  - 22-page teammate explainer grounded in the earlier official-scope audit.
  - Principal scope reference, but revalidate against the live official source links above.
  - Does not claim current implementation status.

- `/root/sih-mailtrace/docs/MailTrace_Complete_Guide.pdf`
  - Product/testing guide for the local prototype.

- `/root/sih-mailtrace/docs/MailTrace_SIH26106_Audit.pdf`
  - Fresh audit artifact containing the rechecked official scope and implementation findings.

- `/root/sih-mailtrace/docs/MailTrace_SIH26106_idea.pdf`
  - Current six-page submission PDF; not upload-ready yet.
  - Still contains `[ENTER PORTAL TEAM ID]` and `[ENTER REGISTERED TEAM NAME]`.

- `/root/sih-mailtrace/docs/MailTrace_SIH26106.pptx`
  - Editable six-page submission deck corresponding to the current PDF.

Other useful source files:
- `/root/sih-mailtrace/README.md`
- `/root/sih-mailtrace/docs/IDEA.md`
- `/root/sih-mailtrace/docs/SUBMIT.md`
- `/root/sih-mailtrace/scripts/build_official_ppt.py`
- `/root/sih-mailtrace/scripts/write_samples.py`

Do not treat screenshots or the old static mock `/root/sih-mailtrace/ui/case.html` as live runtime proof. The actual runtime dossier is `/root/sih-mailtrace/ui/index.html`.

---

## 4. Current implementation inventory

### Backend
- `app.py` — FastAPI orchestration/API.
- `mailtrace/parse.py` — Python email parsing and evidence extraction.
- `mailtrace/score.py` — deterministic rule-based score and labels.
- `mailtrace/intel.py` — offline domain/IP context lookup.
- `mailtrace/graph_store.py` — NetworkX graph construction.
- `mailtrace/store.py` — SQLite case persistence.
- `mailtrace/pdf_report.py` — readable multi-page ReportLab PDF with parsed evidence, provenance and uncertainty.

### Frontend
- `ui/index.html` — actual running dossier UI.
- Uses inline HTML/CSS/JavaScript, Leaflet map, and a custom inline SVG graph renderer.
- `vis-network` may be loaded but is not the visible graph renderer.

### Fixtures/data
- `/root/sih-mailtrace/samples/01_clean.eml`
- `/root/sih-mailtrace/samples/02_display_spoof.eml`
- `/root/sih-mailtrace/samples/03_lookalike.eml`
- `/root/sih-mailtrace/samples/04_spf_fail.eml`
- `/root/sih-mailtrace/samples/05_bec_invoice.eml`
- `/root/sih-mailtrace/samples/06_cred_phish.eml`
- `/root/sih-mailtrace/samples/07_cloud_hops.eml`
- `/root/sih-mailtrace/samples/08_campaign_twin.eml`
- `/root/sih-mailtrace/data/whois_cache.json` — small offline intelligence cache.

The corpus is synthetic/safe demo data. No real mailbox ingestion, public host, or real phishing operation is part of the current demo.

---

## 5. Verified current behavior

The real app path, including the offline intelligence cache, analyzed all eight fixtures successfully:

- `01_clean.eml` -> **CLEAN / 8**
- `02_display_spoof.eml` -> **SPOOF / 100**
- `03_lookalike.eml` -> **PHISH / 98**
- `04_spf_fail.eml` -> **SPOOF / 64**
- `05_bec_invoice.eml` -> **BEC / 100**
- `06_cred_phish.eml` -> **PHISH / 100**
- `07_cloud_hops.eml` -> **SPOOF / 66**
- `08_campaign_twin.eml` -> **SPOOF / 66**

Full corpus graph:
- 8 case nodes.
- 17 edges.

Clean campaign demonstration after reset:
- Analyze 07, then 08.
- 2 nodes and 1 edge.
- Shared indicators: `mail-secure.net`, `18.184.10.20`, and `camp@mail-secure.net`.
- Relationship caption: `Reply-To + same hop + domain`.

Verification already performed:
- fixture generation passed;
- current Python tests: **5 passed**;
- Python compilation passed;
- shell syntax passed;
- API health returned 200;
- raw/multipart upload passed;
- case retrieval passed;
- graph endpoint passed;
- PDF endpoint returned `200 application/pdf`;
- PDF read-back contained SHA-256, reasons, origin, and GPS disclaimer;
- unknown sample returned 404;
- empty upload returned API 400;
- browser console was clean during normal sample flow.

The database was reset to zero cases after verification. The repo had no implementation changes during the re-audit; only the audit PDFs are untracked.

---

## 6. Existing scoring model

Base score is 8, then fixed rule weights are added and capped at 100:

- official-looking title on Gmail address: +28
- Reply-To mismatch: +18
- Return-Path mismatch: +10
- SPF fail: +22
- DKIM fail: +12
- DMARC fail: +12
- lookalike domain: +20
- young cached domain: +14
- cloud-origin hop: +10
- password/login language: +16
- payment/invoice language: +18
- urgency language: +8

This is an explainable **risk indicator**, not a probability, accuracy percentage, attribution confidence, or proof of fraud. The UI currently shows only the first six reasons even when more signals contributed.

---

## 7. Known gaps and correctness findings

### Submission packet — urgent
- Team ID and registered team name placeholders remain.
- Current deck uses custom headings instead of the literal official template headings on slides 2–6.
- Required template headings are: IDEA TITLE, TECHNICAL APPROACH, FEASIBILITY AND VIABILITY, IMPACT AND BENEFITS, RESEARCH AND REFERENCES.
- Correct editable PPTX first, then export one canonical six-page PDF.

### Graph correctness — urgent
- Backend captions are meaningful, but the UI hardcodes every visible edge as `Reply-To + same hop + domain`.
- Full-corpus graph links clean `01_clean` to `04_spf_fail` merely because both mention `pec.edu.in`; common institutional domains create noisy edges.
- Need common-domain exclusion/lower weighting, meaningful-indicator thresholding, edge strength/confidence, and current-case-specific rendering/report filtering.

### Evidence visibility
Parser extracts Return-Path, Message-ID, URLs, and attachments, but the live UI/PDF mostly show From, Reply-To, reasons, Received hops, map, graph, and SHA-256. Add visible:
- Return-Path and Message-ID;
- full authentication evidence;
- URLs/IOCs;
- attachment names/types/sizes/hashes;
- raw-header or evidence view;
- current case’s graph relationships only.

### Evidence preservation/compliance
- SQLite stores parsed JSON and a SHA-256, not the original `.eml` bytes.
- No immutable evidence object, custody events, analyst identity, retention policy, deletion policy, masking/redaction, access control, or action audit log.
- A file hash is an integrity fingerprint, not a blockchain chain-of-custody record.

### Upload/frontend
- API correctly returns 400 for empty uploads, but frontend does not check `response.ok`; it can throw `Cannot read properties of undefined (reading 'origin')`.
- Drop area says “Drop a saved email”, but no true drag/drop handler exists.
- Phone-width render clips the fixed two-column layout and wraps the case title badly. Desktop/laptop demo render is clean.

### Parsing/intelligence
- NLP is Groq Qwen 3.8 27B with bounded points; sklearn fallback; not a calibrated detector.
- HTML-only body is not semantically analyzed.
- IPv6 support is absent.
- Auth extraction is substring/first-match oriented.
- No robust header-order anomaly analysis.
- No URL obfuscation/reputation analysis.
- Offline cache is not live DNS/WHOIS/MX/GeoIP/TI.
- No VPN/TOR/proxy/open-relay/botnet detection.
- No exact sender attribution.
- “Origin confidence” is currently not calculated despite appearing in some explanatory wording.

### Reporting/retention
- PDF is now a readable multi-page report and includes the parsed evidence/provenance fields covered by the parity tests.
- It can include unrelated graph edges from the full graph after multiple analyses.
- `data/reports/` accumulates generated PDFs; cleanup/retention is not implemented.

---

## 8. Correct claims and language

Use:
- “probable earliest observed public hop”;
- “hosting/infrastructure context”;
- “campaign candidate”;
- “shared indicator”;
- “explainable risk score”;
- “confidence/uncertainty to be added or explicitly bounded”.

Do not use without new evidence:
- “we found the attacker”;
- “exact physical location”;
- “100% phishing”;
- “AI model accuracy”;
- “blockchain-secured chain of custody”;
- “real-time Gmail protection”;
- “the sender is located in Frankfurt” when the evidence is only a cloud/datacenter hop.

---

## 9. Planning question for the three bots

Produce one coordinated SIH plan, not code. Each bot should first read this packet and all relevant PDFs, then independently inspect the live repository as needed.

The final group plan must include:

1. One-sentence product definition and strict SIH scope boundary.
2. Confirmed official requirements vs inferences vs proposed choices vs unresolved questions.
3. Target architecture with component/data/evidence boundaries.
4. Minimum credible SIH demo path and judging story.
5. P0/P1/P2 implementation roadmap.
6. Exact acceptance criteria and tests for every P0/P1 item.
7. Evidence/provenance/privacy/security model.
8. ML/NLP strategy that is honest about data and validation.
9. Intelligence strategy: offline demo first, live adapters later, with failure/uncertainty handling.
10. Graph-correlation design that avoids common-domain false links.
11. Dossier/PDF/report design.
12. Submission deck compliance fixes.
13. Risks, anti-claims, and demo failure fallbacks.
14. Recommended division of work between Rishabh/Lyra and teammates.
15. A short final “build next” checklist.

The three roles:
- **Grok 4.6, medium:** adversarial reviewer. Challenge overclaims, scope drift, security/privacy weaknesses, graph false positives, and judging risks.
- **GPT-5.6 Luna, max:** lead architect. Synthesize the official requirements into an implementable staged plan with acceptance criteria.
- **MiniMax M3:** product/demo/implementation planner. Focus on visible workflow, evidence UX, report quality, feasible milestones, and what can be demonstrated reliably.

They may disagree. Preserve disagreement, then state the recommended resolution. Do not let a model silently convert a proposal into an official requirement.

**Final response format:**
- `CONSENSUS`
- `DISAGREEMENTS / DECISIONS`
- `PHASE 0 — submission and demo safety`
- `PHASE 1 — forensic evidence hardening`
- `PHASE 2 — intelligence and correlation`
- `PHASE 3 — ML/NLP and near-real-time path`
- `SECURITY / PRIVACY / CHAIN OF CUSTODY`
- `ACCEPTANCE TESTS`
- `RISKS AND DO-NOT-CLAIM LIST`
- `NEXT 10 ACTIONS`

Again: planning only. Do not edit code or files other than any temporary notes explicitly requested by the coordinator.
