"""NLP layer: Groq Qwen 3.8 27B when enabled, else local TF-IDF logistic."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS = DATA / "nlp_corpus.json"
MODEL = DATA / "nlp_model.joblib"

# Maps model class -> bounded forensic points. Keep 01_clean at +0.
POINTS = {
    "clean": 0,
    "credential_harvest": 10,
    "payment_fraud": 10,
    "impersonation_urgency": 6,
}

_bundle: dict[str, Any] | None = None


def status() -> dict[str, Any]:
    from mailtrace.llm_assist import status as llm_status

    llm = llm_status()
    if llm.get("enabled") and llm.get("configured"):
        return {
            "status": "ready" if llm.get("status") == "ready" else llm.get("status"),
            "model": llm.get("model") or "qwen/qwen3.8-27b",
            "provider": "groq",
            "fallback": "tfidf-logreg",
            "validated": False,
            "note": "NLP layer is Groq Qwen 3.8 27B. Sklearn TF-IDF is fallback if Groq is off or fails.",
        }
    sklearn_state = "available" if MODEL.is_file() or CORPUS.is_file() else "untrained"
    return {
        "status": sklearn_state,
        "model": "tfidf-logreg",
        "provider": "local",
        "validated": False,
        "corpus": str(CORPUS) if CORPUS.is_file() else None,
        "artifact": str(MODEL) if MODEL.is_file() else None,
        "note": "Groq Qwen is off; using local sklearn wording model.",
    }


def _load():
    global _bundle
    if _bundle is not None:
        return _bundle
    if MODEL.is_file():
        import joblib

        _bundle = joblib.load(MODEL)
        return _bundle
    train()
    return _bundle


def train() -> dict[str, Any]:
    """Train from the bundled corpus. Deterministic. Not the 8 demo .eml files."""
    global _bundle
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import joblib

    rows = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = [str(item["text"]) for item in rows]
    labels = [str(item["label"]) for item in rows]
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=4000, lowercase=True)),
            (
                "clf",
                LogisticRegression(max_iter=400, C=2.0, class_weight="balanced", random_state=0),
            ),
        ]
    )
    pipe.fit(texts, labels)
    _bundle = {"pipeline": pipe, "labels": sorted(set(labels)), "trained_on": "bundled-nlp-corpus"}
    DATA.mkdir(parents=True, exist_ok=True)
    joblib.dump(_bundle, MODEL)
    return {"n": len(texts), "labels": _bundle["labels"]}


def analyze(subject: str, body: str, parsed: dict[str, Any] | None = None, *, allow_qwen: bool = True) -> dict[str, Any]:
    text = f"{subject or ''}\n{body or ''}".strip()
    payload = parsed or {"subject": subject, "body": body}
    if allow_qwen:
        from mailtrace.llm_assist import classify_wording

        qwen = classify_wording(payload)
        if qwen and qwen.get("status") == "available":
            return qwen
    base = {
        "status": "available",
        "model": "tfidf-logreg",
        "provider": "local",
        "validated": False,
        "label": "clean",
        "confidence": 0.0,
        "points": 0,
        "source": "local-nlp",
        "note": "Groq Qwen unavailable; local sklearn wording model used.",
    }
    if not text:
        base["status"] = "empty"
        return base
    try:
        bundle = _load()
        pipe = bundle["pipeline"]
        proba = pipe.predict_proba([text])[0]
        classes = list(pipe.classes_)
        idx = int(proba.argmax())
        label = str(classes[idx])
        confidence = float(proba[idx])
        points = POINTS.get(label, 0)
        if label != "clean" and confidence < 0.45:
            label = "clean"
            points = 0
        base.update({"label": label, "confidence": round(confidence, 4), "points": points})
        return base
    except Exception:
        return {
            **base,
            "status": "unavailable",
            "note": "NLP model unavailable; forensic rules retained.",
        }
