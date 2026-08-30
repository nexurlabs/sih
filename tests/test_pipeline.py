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
