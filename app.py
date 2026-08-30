from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mailtrace.graph_store import build as build_graph
from mailtrace.intel import lookup_domains
from mailtrace.parse import parse_eml
from mailtrace.pdf_report import write_pdf
from mailtrace.score import fuse
from mailtrace.store import all_cases, load_case, save_case

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
UI = ROOT / "ui"

app = FastAPI(title="MailTrace", version="0.2.0")
app.mount("/static", StaticFiles(directory=UI), name="static")


def _assemble(data: bytes, filename: str) -> dict:
    parsed = parse_eml(data, filename=filename)
    parsed["intel"] = lookup_domains(
        parsed.get("from_domain"),
        parsed.get("reply_domain"),
        parsed.get("return_domain"),
    )
    fusion = fuse(parsed)
    case = {"id": str(uuid.uuid4())[:8], "parsed": parsed, "fusion": fusion}
    save_case(case)
    case["graph"] = build_graph(all_cases())
    return case


@app.get("/")
def index():
    return FileResponse(UI / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "product": "MailTrace", "ps": "SIH26106"}


@app.get("/api/samples")
def list_samples():
    files = sorted(SAMPLES.glob("*.eml"))
    return [{"name": f.name, "bytes": f.stat().st_size} for f in files]


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
    case["graph"] = build_graph(all_cases())
    return case


@app.get("/api/case/{case_id}/pdf")
def case_pdf(case_id: str):
    case = load_case(case_id)
    if not case:
        raise HTTPException(404, "unknown case")
    path = write_pdf(case)
    return FileResponse(path, filename=f"mailtrace-{case_id}.pdf", media_type="application/pdf")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    return _assemble(data, file.filename or "upload.eml")


@app.post("/api/analyze-sample/{name}")
def analyze_sample(name: str):
    path = (SAMPLES / name).resolve()
    if path.parent != SAMPLES.resolve() or not path.is_file():
        raise HTTPException(404, "unknown sample")
    return _assemble(path.read_bytes(), name)
