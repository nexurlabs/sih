# Idea text — paste into PEC form / sih.gov.in

**Problem statement:** SIH26106  
**Title (suggested,  under ~100 chars):**  
MailTrace: email threat lab with origin hops, not a spam filter

**Description (paste):**

MailTrace is an analyst lab for SIH26106. An investigator uploads a saved .eml file. The system returns a risk score with human reasons, a map of the earliest reliable sending hop (city and ISP, not a person's GPS), SPF/DKIM/DMARC stamp results, a campaign graph linking related mails, and a PDF whose SHA-256 matches that exact file.

This is not Gmail login and not a 2003 spam-word classifier. Detection without origin fails the problem. Origin without reasons is theatre. MailTrace fuses both on a laptop (localhost). Demo corpus: eight crafted mails (clean, display-name spoof, lookalike domain, SPF fail, BEC invoice, credential phish, two-mail campaign).

No live mailbox ingest. No sending phishing. No claim that we located a human. Geo is hosting intelligence with confidence. Evidence is a local hash chain, not a public blockchain.

**Tech (one line):** FastAPI + MIME parser + SQLite + NetworkX + Leaflet + vis-network + reportlab PDF.

**Do not put in the form:** public URL, Gmail OAuth, teammate sklearn pickle as the product.
