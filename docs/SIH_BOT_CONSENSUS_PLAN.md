# SIH26106 / MailTrace — `sih` Bot Consensus Plan

Source: the Hermes Bot Mode group `sih`, with `sih-grok46`, `sih-luna56`, and `sih-minimaxm3`. Planning-only review; no repository edits, commits, deployments, credentials, or external contacts were made.

## A. Recommendation and boundary

Keep MailTrace as a localhost analyst lab for the immediate SIH milestone. It accepts a saved `.eml`, computes a SHA-256 fingerprint of the uploaded bytes, extracts header/MIME/body evidence, produces a deterministic explainable risk indicator, shows probable hosting infrastructure from offline demo data, correlates local cases through shared indicators, and exports a case PDF.

Do not present the current prototype as a Gmail/mail gateway, real-time or pre-interaction protection, trained/validated AI/ML, live WHOIS/DNS/MX/GeoIP/TI, a calibrated probability, a person’s GPS location, an attacker-identity system, malware detonation, a public blockchain, or a complete legal chain-of-custody archive.

## B. Requirements-to-proof summary

- Detection: partial. `mailtrace/score.py` uses deterministic keyword/header rules and currently labels the eight synthetic fixtures CLEAN/SPOOF/PHISH/BEC. Gap: no evaluated ML/NLP, robust HTML/obfuscation analysis, URL reputation, or calibrated probability.
- Header forensics: partial. `mailtrace/parse.py` extracts From, Return-Path, Received, Message-ID, Reply-To, and header-stated SPF/DKIM/DMARC. Gap: Return-Path, Message-ID, raw auth evidence, alignment/verification mode, URLs, and attachment metadata need dossier/PDF parity. Never call header-stated results live verification.
- Origin intelligence: offline approximation. Known demo IPs and a hand-built domain cache provide hosting context. Gap: no live intelligence, IPv6, robust relay validation, or numeric origin confidence.
- Correlation: partial. NetworkX links shared domains/IPs/Reply-To. Gap: common/shared demo IPs can create false campaigns; UI captions are hardcoded; no external TI or identity classification.
- Dashboard/reports: local upload dossier, map, graph, case API, and PDF exist. Gap: no mailbox/gateway, pre-interaction alerting, quarantine, case search/filter, campaign management, or complete report evidence.
- Privacy/evidence: synthetic local fixtures and upload hashing exist. Gap: the original `.eml` bytes are not archived in SQLite, and there is no custody event ledger, analyst identity, masking, access logging, retention, or controlled deletion.

## C. Critical path

### P0 — submission and demo safety

1. Obtain the real portal Team ID and registered Team Name.
2. Re-check the exact SIH26106 title on the selected official portal row immediately before submission.
3. Restore the supplied six-slide template’s literal headings: IDEA TITLE; TECHNICAL APPROACH; FEASIBILITY AND VIABILITY; IMPACT AND BENEFITS; RESEARCH AND REFERENCES.
4. Remove `[ENTER PORTAL TEAM ID]` and `[ENTER REGISTERED TEAM NAME]`.
5. Replace `with confidence`, `preserves the exact bytes`, and any current-prototype NLP/AI claim with honest uncertainty/fingerprint wording.
6. Use screenshots from `ui/index.html`, not the legacy `ui/case.html`.
7. Export one reviewed, canonical six-page PDF from the editable PPTX. Verify six pages, six slides, no placeholders, no instruction page, correct headings/title/team fields, no clipping. Only after verification remove duplicate submission artifacts so there is one upload candidate.

### P1 — demo hardening

1. Show Return-Path, Message-ID, URLs, attachment metadata, raw/header authentication source, `verification_mode=header evidence`, and uncertainty/provenance in both dossier and PDF.
2. Fix auth parsing so pass+fail conflicts become `CONFLICT`/`UNKNOWN`, never `pass`.
3. Lock graph changes A+B together: rotate unrelated demo fixtures only to existing cache entries or deterministic reserved/unknown values, while keeping 07/08’s shared campaign indicators; and forbid IP-only edges. Update related tests in the same change.
4. Make graph captions API-derived and show shared keys/strength; do not globally use `pec.edu.in` as a denylist or call an edge proof of common control.
5. Fix frontend `response.ok` handling for empty uploads and add a map/CDN fallback.
6. Add the five pinned graph assertions: reset→07/08 = exactly 2 nodes/1 API-derived edge; reset→04 plus 02/05/06 = 0 edges; reset→01/04 = 0 edges; 04 shows SPF/DKIM/DMARC fail, Return-Path equals From, no Reply-To, probable hop `18.184.10.20` / Frankfurt / AWS from the offline table; captions vary with actual shared keys.

### P2 — only after P0/P1 pass

One optional item at most: controlled raw-evidence/custody trace, an evaluated local NLP baseline, or case search/filter. Live intelligence adapters may exist behind one OFF-by-default boundary, but must return unknown/unavailable on missing or failed lookups.

## D. Evidence and wording rules

- Risk score: “Deterministic explainable risk indicator. Not a probability, accuracy percentage, or identity proof.”
- Authentication: “SPF/DKIM/DMARC results were read from the `.eml` headers. No live DNS or independent cryptographic verification was performed by this prototype.”
- Origin: “Probable earliest observed public hop and cached hosting/network context. Not a person’s GPS location.”
- Campaign graph: “Shared indicators create a campaign candidate. They do not prove common control, identity, or criminal responsibility.”
- Hash: “SHA-256 of the exact uploaded bytes. Integrity fingerprint, not a public blockchain or complete custody ledger.”
- Attachments: metadata and hash only; no opening, execution, or detonation.

The complete custody design—raw evidence storage, hash/filename/parser provenance, actor-attributed events, local permissions, retention/deletion, masking, and redacted reports—should be a later prototype custody trace, not claimed as legal-grade compliance now. Do not invent a universal 30-day policy.

## E. Test and three-minute demo

Freeze the eight-fixture baseline. Add enriched score-contract, evidence-field, auth-conflict, graph-isolation, API-caption, PDF-parity, empty-upload, and map-fallback tests. Re-run the full suite after every code change.

Demo sequence:

1. Start only on loopback and reset state.
2. `04_spf_fail.eml`: show SPOOF/64, header-stated SPF/DKIM/DMARC failure, Return-Path=From, no Reply-To, Received hop `18.184.10.20`, cached Frankfurt/AWS context, and non-attribution wording.
3. `05_bec_invoice.eml`: show BEC/100 as a capped rule score and the payment/account-change evidence.
4. Reset again; analyze `07_cloud_hops.eml` then `08_campaign_twin.eml`: show exactly two nodes, one relationship, actual shared indicators, and “campaign candidate/shared indicators,” not identity proof.
5. Open the PDF and point to case ID, SHA-256, evidence source, hops, disclaimers, and the focused relationship.
6. Keep fallback screenshots/PDF ready if external fonts, Leaflet, vis-network, or OSM resources fail.

## F. Unresolved inputs for Rishabh

- Exact registered portal Team ID.
- Exact registered Team Name.
- Current official SIH26106 title string.
- Evidence that the 31-Aug-2026 leader form was submitted.
- Approval of graph lock A+B before touching `scripts/write_samples.py`, `graph_store.py`, or auth parsing.
- Whether duplicate artifacts are removed after canonical verification.
- Whether the demo environment can reach CDN/map resources.
- Whether institute policy permits future external LLM/live intelligence.
- Retention, analyst identity, raw-evidence custody, and masking policy.

## G. Explicit do-not-build list for this milestone

No Gmail/Outlook OAuth or mailbox ingestion; no public hosting; no live phishing or attack infrastructure; no public blockchain email storage; no default live WHOIS/DNS/MX/blacklist; no VPN/TOR/botnet claims without verified data; no tiny-corpus trained-from-scratch classifier; no teammate `.pkl` presented as the SIH model; no attachment execution; no exact human geolocation or sender attribution; no invented percentages; no cosmetic custody table described as compliance; no dense unreadable full-corpus graph.

## Smallest credible SIH-ready slice

A template-compliant six-slide PDF with real team metadata and official wording, backed by a reliable localhost demo using real `ui/index.html` captures, visible header/origin evidence, honest uncertainty/fingerprint language, and a clean reset-isolated 07/08 campaign-candidate graph.
