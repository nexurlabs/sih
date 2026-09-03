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
MAILTRACE_PORT="${MAILTRACE_PORT:-8777}"
uvicorn app:app --host 127.0.0.1 --port "$MAILTRACE_PORT"
```

Open http://127.0.0.1:8777

**Optional Qwen analyst assist (Groq):** the core score stays deterministic. Create a Groq free-tier key at https://console.groq.com/keys, then run the local installer. It prompts invisibly, writes the key only to git-ignored files, and never prints it:

```bash
python3 scripts/set_groq_key.py
./run.sh
```

The installer configures `qwen/qwen3.8-27b` for MailTrace and all three SIH Bot Mode profiles. The app sends Groq a redacted evidence summary only: no raw `.eml`, attachment bytes, query strings, or unmasked email addresses. Qwen output appears as **analyst assist**, does not change the deterministic score/label, and is marked non-validated. Without the key or with the feature disabled, the app remains fully usable offline.

**Demo:** `04_spf_fail.eml`, then `07_cloud_hops.eml` + `08_campaign_twin.eml` (graph). Download PDF on the case.

## Run on Windows (teammates / noobs)

Repo is **private**. Get invited first. If GitHub says not found, you were not invited.

1. Install Python 3.11+ from python.org and tick **Add python.exe to PATH**.
2. Install Git (or GitHub Desktop).
3. Clone, then in **PowerShell**:

```powershell
cd $HOME\Desktop
git clone https://github.com/nexurlabs/sih.git
cd sih
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\write_samples.py
pytest -q
python -m uvicorn app:app --host 127.0.0.1 --port 8777
```

If Activate is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

If `python` opens the Microsoft Store, use `py -3` instead of `python`.

Leave that window open. Browser: http://127.0.0.1:8777

**Clicks:** `04_spf_fail.eml` → 64 SPOOF. Then `07` + `08` → two nodes, one edge.

Optional live DNS/Geo (this PowerShell window):

```powershell
$env:MAILTRACE_LIVE_DNS="1"
$env:MAILTRACE_LIVE_GEO="1"
```

Or after Activate: `.\run.ps1` (reads `.env` if present). Full walkthrough: `docs/MailTrace_Complete_Guide.pdf`

## SIH submission deck

The editable six-slide deck is built from the provided SIH 2026 template:

```bash
export MAILTRACE_TEAM_ID='REAL PORTAL TEAM ID'
export MAILTRACE_TEAM_NAME='REGISTERED TEAM NAME'
export MAILTRACE_PORTAL_TITLE='VERIFIED SIH26106 PORTAL TITLE'
python scripts/build_official_ppt.py --export-pdf
```

The command writes the editable twin and the one canonical PDF at
`docs/MailTrace_SIH26106_idea.pdf`. The generator refuses empty or placeholder
metadata. Upload the PDF, not the PPTX, only after the title/team values are
verified against the portal and the six-page export is visually reviewed.

## Stack

- FastAPI + Python email parser
- SQLite case store
- NetworkX campaign graph
- Leaflet map (offline lat/lon table for demo hops)
- custom SVG relationship graph renderer
- reportlab PDF
- GeoIP via MaxMind MMDB + optional ip-api, demo IP pins preserved
- Live SPF/DMARC TXT via dnspython when MAILTRACE_LIVE_DNS=1
- Local TF-IDF/LogReg NLP as a bounded score component
- Cached WHOIS json (no live scrape)

## Do not

- Connect Gmail / Outlook
- Send phishing
- Claim you located a person
- Put mail on a public chain
- Make this repo public
