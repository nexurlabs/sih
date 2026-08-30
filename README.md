# MailTrace (SIH26106)

Private team repo. Local analyst lab: upload a saved `.eml` → risk score + reasons + hop origin + campaign links.

Not a spam filter. Not Gmail. Not a person’s GPS.

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

Demo for slides: click `04_spf_fail.eml`, then `07_cloud_hops.eml` and `08_campaign_twin.eml`.

## Do not

- Connect Gmail / Outlook
- Send phishing
- Claim you located a person
- Put mail on a public blockchain
- Make this repo public
