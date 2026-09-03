# Idea text — paste into PEC form / sih.gov.in

**Problem statement:** SIH26106  
**Title (suggested, under ~100 chars):**  
MailTrace: Explainable email threat detection with origin and campaign forensics

**Description (paste):**

MailTrace is a local-first analyst platform for SIH26106. An investigator uploads a saved `.eml` file. The system preserves and hashes the exact uploaded bytes, extracts message headers and MIME content, surfaces SPF/DKIM/DMARC and sender-alignment evidence, reconstructs the Received chain, and reports the probable earliest observed hop with stated uncertainty and cached hosting context. It then gives an explainable deterministic risk indicator for spoofing, phishing and BEC, links related emails through shared indicators, and exports a forensic case PDF.

The key difference from a spam/ham filter is the evidence trail: the analyst can see why a message is suspicious, where it likely travelled through, and whether another message shares the same Reply-To, domain or origin hop. The prototype runs on a laptop with local crafted `.eml` cases; it does not require Gmail access, send phishing, or claim the exact location of a human. Live DNS verification, larger GeoIP/ASN data, privacy controls and model calibration are the production hardening path.

**Tech (one line):** FastAPI + Python MIME parser + SQLite + NetworkX + custom SVG graph + Leaflet fallback + ReportLab PDF; NLP is Groq `qwen/qwen3.8-27b` (bounded wording points, sklearn fallback). Not a calibrated detector.
