"""Settings, file paths and business constants in one place.

Keys are read from `Portfolio Projects/.env` (two folders above this repo) when it exists, otherwise
from normal environment variables. Keys are never printed or logged.

The bank, "Gulf Horizon Bank", is fictional. Its service targets below are invented and configurable.
Only the 15-calendar-day ombudsman rule comes from a real source (Sanadak, see docs/model_risk.md).
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
EVALS_DIR = REPO_ROOT / "evals"

# Shared .env first (Portfolio Projects/.env), then a local repo .env. Real environment variables win.
load_dotenv(REPO_ROOT.parent.parent / ".env", override=False)
load_dotenv(REPO_ROOT / ".env", override=False)

BANK_NAME = "Gulf Horizon Bank"

# ---- Complaint clock (fictional bank targets, except the Sanadak rule) ----
ACK_BUSINESS_DAYS = 2  # written acknowledgement due within 2 business days
ESCALATION_BUSINESS_DAYS = 5  # still open after 5 business days -> Complaints Manager
OMBUDSMAN_CALENDAR_DAYS = 15  # Sanadak: the customer may refer after 15 calendar days without a written reply
WEEKEND = {5, 6}  # Saturday and Sunday (Python: Monday = 0). UAE weekend since 2022: a stated assumption.
# Assumed public holidays for the demo year. Islamic holidays move with the moon sighting:
# replace this list with the official announcement before relying on it.
HOLIDAYS_2026 = {
    date(2026, 1, 1),  # New Year's Day
    date(2026, 3, 20), date(2026, 3, 21), date(2026, 3, 22),  # Eid al-Fitr (assumed dates)
    date(2026, 5, 26),  # Arafat Day (assumed)
    date(2026, 5, 27), date(2026, 5, 28), date(2026, 5, 29),  # Eid al-Adha (assumed)
    date(2026, 6, 16),  # Hijri New Year (assumed)
    date(2026, 8, 25),  # Prophet's Birthday (assumed)
    date(2026, 12, 1),  # Commemoration Day
    date(2026, 12, 2), date(2026, 12, 3),  # National Day
}
DISPUTE_WINDOW_DAYS = 120  # fictional: card disputes accepted up to 120 days after the transaction

# ---- Routing ----
# Below this confidence a classical model's guess goes to the human triage desk (customer_care).
# Set before any test run (not tuned on the test set).
CLASSIC_MIN_CONFIDENCE = 0.30
PROMPT_VERSION = "triage-v1"  # change when prompts.py changes; it is written to the audit log


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def model_id(role: str) -> str:
    """role 'main', 'cheap', 'judge' or 'embed' -> the model ID from MODEL_MAIN / ... / MODEL_EMBED."""
    if role == "embed":
        return env("MODEL_EMBED", "baai/bge-m3")
    return env(f"MODEL_{role.upper()}")


def runtime_dir() -> Path:
    """Folder for mutable demo state (case queue, audit log, cached models). Not committed."""
    path = Path(env("TRIAGE_RUNTIME_DIR") or (REPO_ROOT / "runtime"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def reviewer() -> dict:
    """Who uses the agent console. Set in configuration, never chosen on screen (least privilege)."""
    return {"id": env("REVIEWER_ID", "demo-reviewer"), "role": "complaints-officer"}
