from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mailtrace.parse import parse_eml
from mailtrace.score import fuse


def test_clean_is_not_phish():
    p = Path(__file__).resolve().parents[1] / "samples" / "01_clean.eml"
    parsed = parse_eml(p.read_bytes(), p.name)
    out = fuse(parsed)
    assert parsed["auth"]["spf"] == "pass"
    assert out["label"] == "CLEAN"
    assert out["score"] < 45


def test_spoof_and_twin_graph_keys():
    root = Path(__file__).resolve().parents[1] / "samples"
    a = parse_eml((root / "02_display_spoof.eml").read_bytes(), "02_display_spoof.eml")
    b = fuse(a)
    assert a["gmail_wearing_title"]
    assert a["auth"]["spf"] == "fail"
    assert b["label"] in {"SPOOF", "PHISH"}
    assert b["score"] >= 55
    assert a["origin"]["city"] == "Frankfurt"
    assert a["origin"]["lat"] == 50.1109


def test_campaign_graph_and_pdf(tmp_path, monkeypatch):
    from mailtrace.graph_store import build
    from mailtrace.pdf_report import write_pdf
    from mailtrace import pdf_report

    monkeypatch.setattr(pdf_report, "OUT", tmp_path)
    root = Path(__file__).resolve().parents[1] / "samples"
    cases = []
    for name in ("07_cloud_hops.eml", "08_campaign_twin.eml"):
        p = parse_eml((root / name).read_bytes(), name)
        cases.append({"id": name[:2], "parsed": p, "fusion": fuse(p)})
    g = build(cases)
    assert len(g["nodes"]) == 2
    assert g["edges"]
    path = write_pdf(cases[0])
    assert path.exists() and path.stat().st_size > 400


def test_demo_corpus_labels():
    root = Path(__file__).resolve().parents[1] / "samples"
    expected = {
        "01_clean.eml": "CLEAN",
        "02_display_spoof.eml": "SPOOF",
        "03_lookalike.eml": "PHISH",
        "04_spf_fail.eml": "SPOOF",
        "05_bec_invoice.eml": "BEC",
        "06_cred_phish.eml": "PHISH",
        "07_cloud_hops.eml": "SPOOF",
        "08_campaign_twin.eml": "SPOOF",
    }
    assert len(list(root.glob("*.eml"))) == 8
    for name, label in expected.items():
        p = parse_eml((root / name).read_bytes(), name)
        out = fuse(p)
        assert out["label"] == label
        assert len(p["sha256"]) == 64


def test_attachment_metadata_is_hashed_without_execution():
    from email.message import EmailMessage
    import hashlib

    msg = EmailMessage()
    msg["From"] = "sender@example.org"
    msg["To"] = "analyst@example.org"
    msg["Subject"] = "Attachment test"
    msg.set_content("A harmless test message.")
    payload = b"benign attachment bytes"
    msg.add_attachment(payload, maintype="application", subtype="pdf", filename="invoice.pdf")

    parsed = parse_eml(msg.as_bytes(), "attachment-test.eml")
    assert parsed["attachments"] == [{
        "filename": "invoice.pdf",
        "content_type": "application/pdf",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }]
