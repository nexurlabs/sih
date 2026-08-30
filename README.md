# MailTrace (SIH26106)

Private team repo. Local analyst lab.

Upload a saved `.eml` → score + reasons + hop map + campaign graph + SHA-256 PDF.

Not a spam filter. Not Gmail. Geo is **hosting city / ISP**, not a person's GPS.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/write_samples.py
pytest -q
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

**Demo:** `04_spf_fail.eml`, then `07_cloud_hops.eml` + `08_campaign_twin.eml` (graph). Download PDF on the case.

## SIH submission deck

The editable six-slide deck is built from the provided SIH 2026 template:

```bash
python scripts/build_official_ppt.py
soffice --headless --convert-to pdf --outdir docs docs/MailTrace_SIH26106.pptx
```

Upload `docs/MailTrace_SIH26106_idea.pdf`, not the PPTX. Fill the real portal Team ID and registered Team Name on slide 1 before uploading.

## Stack

- FastAPI + Python email parser
- SQLite case store
- NetworkX campaign graph
- Leaflet map (offline lat/lon table for demo hops)
- vis-network
- reportlab PDF
- Cached WHOIS json only (no live scrape)

## Do not

- Connect Gmail / Outlook
- Send phishing
- Claim you located a person
- Put mail on a public chain
- Make this repo public
