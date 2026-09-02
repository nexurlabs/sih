#!/usr/bin/env python3
"""Install a Groq key locally without printing it.

The key is read from an interactive hidden prompt (or GROQ_API_KEY already in
the process environment), then written with mode 0600 to the three SIH Hermes
profiles and the ignored MailTrace .env file.
"""
from __future__ import annotations

import getpass
import os
import tempfile
from pathlib import Path

PROFILES = ("sih-grok46", "sih-luna56", "sih-minimaxm3")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HERMES_ROOT = Path(os.getenv("HERMES_ROOT", Path.home() / ".hermes")).expanduser()


def update_env(path: Path, updates: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        old = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        old = ""
    lines = old.splitlines()
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else ""
        if key in updates:
            result.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            result.append(line)
    for key, value in updates.items():
        if key not in seen:
            result.append(f"{key}={value}")
    content = "\n".join(result).rstrip("\n") + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".env_", dir=str(path.parent), text=True)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def main() -> None:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        key = getpass.getpass("Groq API key (hidden): ").strip()
    if not key:
        raise SystemExit("No key entered; nothing changed.")

    for profile in PROFILES:
        update_env(HERMES_ROOT / "profiles" / profile / ".env", {"GROQ_API_KEY": key})
    update_env(
        PROJECT_ROOT / ".env",
        {
            "GROQ_API_KEY": key,
            "MAILTRACE_LLM_ENABLED": "1",
            "MAILTRACE_LLM_MODEL": "qwen/qwen3.8-27b",
            "MAILTRACE_LLM_TIMEOUT": "25",
        },
    )
    del key
    print("Groq key stored locally in 3 SIH profile env files and MailTrace .env.")
    print("The value was not displayed. Restart the bots and MailTrace after setup.")


if __name__ == "__main__":
    main()
