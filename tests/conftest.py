import os
from pathlib import Path

os.environ.setdefault("MAILTRACE_LIVE_DNS", "0")
os.environ.setdefault("MAILTRACE_LIVE_GEO", "0")
os.environ.setdefault("MAILTRACE_LLM_ENABLED", "0")

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT))
