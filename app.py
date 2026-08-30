from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mailtrace.graph_store import CampaignGraph
from mailtrace.parse import parse_eml
from mailtrace.score import fuse

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
UI = ROOT / "ui"

app = FastAPI(title="MailTrace", version="0.1.0")
graph = CampaignGraph()
app.mount("/static", StaticFiles(directory=UI), name="static")


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


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")
    parsed = parse_eml(data, filename=file.filename or "upload.eml")
    fusion = fuse(parsed)
    case = {"id": str(uuid.uuid4())[:8], "parsed": parsed, "fusion": fusion}
    links = graph.add(case)
    return {"id": case["id"], "parsed": parsed, "fusion": fusion, "graph": links}


@app.post("/api/analyze-sample/{name}")
def analyze_sample(name: str):
    path = (SAMPLES / name).resolve()
    if path.parent != SAMPLES.resolve() or not path.is_file():
        raise HTTPException(404, "unknown sample")
    data = path.read_bytes()
    parsed = parse_eml(data, filename=name)
    fusion = fuse(parsed)
    case = {"id": str(uuid.uuid4())[:8], "parsed": parsed, "fusion": fusion}
    links = graph.add(case)
    return {"id": case["id"], "parsed": parsed, "fusion": fusion, "graph": links}
