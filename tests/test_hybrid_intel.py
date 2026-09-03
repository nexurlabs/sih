from email.message import EmailMessage
from pathlib import Path
import sys

sys_path = str(Path(__file__).resolve().parents[1])
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from mailtrace.dns_auth import live_check
from mailtrace.geo import lookup_ip
from mailtrace.parse import parse_eml
from mailtrace.score import fuse


def test_demo_ips_still_pin_frankfurt():
    row = lookup_ip("18.184.10.20")
    assert row["city"] == "Frankfurt"
    assert row["isp"] == "AWS"
    assert row["lat"] == 50.1109
    assert row["source"] == "offline-demo-table"


def test_private_ip_is_not_geolocated():
    row = lookup_ip("10.1.2.3")
    assert row["status"] == "unknown"
    assert row["source"] == "rfc1918"


def test_html_body_and_href_are_extracted():
    msg = EmailMessage()
    msg["From"] = "it@example.org"
    msg["To"] = "user@example.org"
    msg["Subject"] = "Reset"
    msg.set_content("plain fallback")
    msg.add_alternative(
        '<html><body>Please <a href="https://paypa1.example/login">verify your password</a></body></html>',
        subtype="html",
    )
    parsed = parse_eml(msg.as_bytes(), "html.eml")
    assert parsed["html_present"] is True
    assert "https://paypa1.example/login" in parsed["urls"]
    assert "verify your password" in parsed["body"].lower()


def test_high_risk_attachment_is_flagged_not_executed():
    msg = EmailMessage()
    msg["From"] = "sender@example.org"
    msg["Subject"] = "Invoice"
    msg.set_content("See attached.")
    msg.add_attachment(b"MZ-fake", maintype="application", subtype="octet-stream", filename="invoice.exe")
    parsed = parse_eml(msg.as_bytes(), "exe.eml")
    assert parsed["attachments"][0]["risk"] == "high"
    out = fuse(parsed)
    assert any(s["code"] == "dangerous_attachment" for s in out["signals"])


def test_live_dns_disabled_in_tests():
    parsed = {
        "from_domain": "pec.edu.in",
        "return_domain": "pec.edu.in",
        "origin": {"ip": "18.184.10.20"},
    }
    result = live_check(parsed)
    assert result["enabled"] is False
    assert result["spf_published"] == "unavailable"


def test_nlp_is_in_the_score_path_and_clean_stays_clean():
    root = Path(__file__).resolve().parents[1] / "samples"
    parsed = parse_eml((root / "01_clean.eml").read_bytes(), "01_clean.eml")
    out = fuse(parsed)
    assert out["method"] == "hybrid-forensic-nlp"
    assert out["model"]["status"] == "tfidf-logreg"
    assert out["nlp"]["status"] in {"available", "empty"}
    assert out["label"] == "CLEAN"
    assert out["score"] < 45
    assert out["score"] == min(100, out["forensic_score"] + int(out["nlp"].get("points") or 0))


def test_qwen_nlp_feeds_bounded_points(monkeypatch):
    from mailtrace import llm_assist
    from mailtrace.score import fuse

    def fake_classify(_parsed):
        return {
            "status": "available",
            "model": "qwen/qwen3.8-27b",
            "source": "qwen-nlp",
            "label": "credential_harvest",
            "points": 18,
            "validated": False,
            "note": "NLP layer is Groq qwen/qwen3.8-27b.",
        }

    monkeypatch.setattr(llm_assist, "classify_wording", fake_classify)
    root = Path(__file__).resolve().parents[1] / "samples"
    parsed = parse_eml((root / "01_clean.eml").read_bytes(), "01_clean.eml")
    out = fuse(parsed, allow_qwen=True)
    assert out["nlp"]["source"] == "qwen-nlp"
    assert out["nlp"]["points"] == 18
    assert out["score"] == min(100, out["forensic_score"] + 18)
    assert any(s.get("code") == "nlp_credential_harvest" for s in out["signals"])


def test_04_forensic_score_stays_64():
    root = Path(__file__).resolve().parents[1] / "samples"
    parsed = parse_eml((root / "04_spf_fail.eml").read_bytes(), "04_spf_fail.eml")
    out = fuse(parsed)
    assert out["forensic_score"] == 64
    assert out["label"] == "SPOOF"
    assert out["nlp"]["validated"] is False
