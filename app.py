from __future__ import annotations

import uuid
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from mailtrace.dns_auth import live_check, status as dns_status
from mailtrace.geo import status as geo_status
from mailtrace.graph_store import build as build_graph
from mailtrace.intel import lookup_domains
from mailtrace.llm_assist import build_assist, status as llm_status
from mailtrace.nlp_model import status as nlp_status
from mailtrace.parse import parse_eml
from mailtrace.pdf_report import write_pdf
from mailtrace.privacy import masked_case
from mailtrace.score import fuse
from mailtrace.store import all_cases, clear_cases, evidence_path, load_case, save_case

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
UI = ROOT / "ui"

app = FastAPI(title="MailTrace", version="0.3.0")
app.mount("/static", StaticFiles(directory=UI), name="static")


def _assemble(
    data: bytes,
    filename: str,
    *,
    persist: bool = True,
    include_llm: bool = True,
    case_id: str | None = None,
) -> dict:
    parsed = parse_eml(data, filename=filename)
    header_names = {
        "from", "to", "cc", "bcc", "subject", "date", "message-id",
        "received", "return-path", "reply-to", "authentication-results",
        "received-spf", "content-type", "mime-version",
    }
    found_headers = {
        match.group(1).lower()
        for match in re.finditer(r"(?m)^([A-Za-z0-9][A-Za-z0-9-]*):", parsed.get("raw_headers", ""))
    }
    if not found_headers.intersection(header_names):
        raise HTTPException(400, "invalid email: no recognizable RFC 5322 headers")
    parsed["intel"] = lookup_domains(
        parsed.get("from_domain"),
        parsed.get("reply_domain"),
        parsed.get("return_domain"),
    )
    parsed["live_auth"] = live_check(parsed)
    fusion = fuse(parsed, allow_qwen=include_llm)
    nlp = fusion.get("nlp") or {}
    assist = nlp.pop("assist", None) if isinstance(nlp, dict) else None
    if include_llm:
        fusion["llm_assist"] = assist if assist else build_assist(parsed, fusion)
    else:
        llm = llm_status()
        fusion["llm_assist"] = {
            "status": "disabled",
            "provider": llm.get("provider", "groq"),
            "model": llm.get("model", "qwen/qwen3.8-27b"),
            "validated": False,
            "note": "Public read-only demo: uploads, raw evidence, and Qwen calls are disabled.",
        }
    case = {"id": case_id or str(uuid.uuid4())[:8], "parsed": parsed, "fusion": fusion}
    if persist:
        save_case(case, raw_bytes=data)
        case["graph"] = build_graph(all_cases(), focus_id=case["id"])
    else:
        case["graph"] = build_graph([case], focus_id=case["id"])
    return case


def _sample_path(name: str) -> Path:
    path = (SAMPLES / name).resolve()
    if path.parent != SAMPLES.resolve() or not path.is_file():
        raise HTTPException(404, "unknown sample")
    return path


@app.get("/")
def index():
    return FileResponse(UI / "index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "product": "MailTrace",
        "ps": "SIH26106",
        "llm": llm_status(),
        "nlp": nlp_status(),
        "geo": geo_status(),
        "live_dns": dns_status(),
    }


@app.get("/api/samples")
def list_samples():
    files = sorted(SAMPLES.glob("*.eml"))
    return [{"name": f.name, "bytes": f.stat().st_size} for f in files]


@app.get("/api/demo/{name}")
def demo_sample(name: str):
    """Return a non-persistent, no-provider demo analysis for the public view."""
    selected = _sample_path(name).name
    demo_cases = [
        _assemble(
            path.read_bytes(),
            path.name,
            persist=False,
            include_llm=False,
            case_id=f"demo-{path.stem}",
        )
        for path in sorted(SAMPLES.glob("*.eml"))
    ]
    case = next(item for item in demo_cases if item["parsed"]["filename"] == selected)
    case["graph"] = build_graph(demo_cases, focus_id=case["id"])
    case["view"] = "public-demo"
    return case


@app.post("/api/reset")
def reset():
    clear_cases()
    return {"ok": True, "cleared": True}


@app.get("/api/cases")
def cases():
    return [{"id": c["id"], "filename": c["parsed"]["filename"], "score": c["fusion"]["score"]} for c in all_cases()]


@app.get("/api/graph")
def graph():
    return build_graph(all_cases())


@app.get("/api/case/{case_id}")
def get_case(case_id: str):
    case = load_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    case["graph"] = build_graph(all_cases(), focus_id=case_id)
    return case


@app.get("/api/case/{case_id}/masked")
def get_masked_case(case_id: str):
    case = load_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    masked = masked_case(case)
    masked["graph"] = build_graph(all_cases(), focus_id=case_id)
    masked["view"] = "masked"
    return masked


@app.get("/api/case/{case_id}/pdf")
def case_pdf(case_id: str):
    case = load_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    case["graph"] = build_graph(all_cases(), focus_id=case_id)
    path = write_pdf(case)
    return FileResponse(path, filename=f"mailtrace-{case_id}.pdf", media_type="application/pdf")


@app.get("/api/case/{case_id}/evidence")
def case_evidence(case_id: str):
    case = load_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    path = evidence_path(case)
    if not path:
        raise HTTPException(409, "raw evidence unavailable or hash mismatch")
    return Response(path.read_bytes(), media_type="message/rfc822")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    return _assemble(data, file.filename or "upload.eml")


@app.post("/api/analyze-sample/{name}")
def analyze_sample(name: str):
    path = _sample_path(name)
    return _assemble(path.read_bytes(), name)
