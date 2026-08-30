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
