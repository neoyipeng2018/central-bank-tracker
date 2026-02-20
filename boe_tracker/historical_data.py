"""Historical stance storage with seed data for MPC participants."""

import json
import os
from datetime import datetime

from boe_tracker import config as cfg

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "boe")
HISTORY_DIR = os.path.join(DATA_DIR, "historical")
HISTORY_FILE = os.path.join(HISTORY_DIR, "stance_history.json")


def ensure_dirs():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _score_label(score: float) -> str:
    return cfg.score_label(score)


# Seed data: historical stances for context (based on known MPC voting patterns)
SEED_DATA: dict[str, list[dict]] = {
    "Andrew Bailey": [
        {"date": "2025-09-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 0.00, "label": "Neutral", "source": "seed",
         "policy_score": 0.00, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
    ],
    "Sarah Breeden": [
        {"date": "2025-09-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
    ],
    "Clare Lombardelli": [
        {"date": "2025-09-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
    ],
    "Dave Ramsden": [
        {"date": "2025-09-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
    ],
    "Huw Pill": [
        {"date": "2025-09-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
    ],
    "Megan Greene": [
        {"date": "2025-09-15", "score": 1.50, "label": "Neutral", "source": "seed",
         "policy_score": 1.50, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
    ],
    "Catherine L Mann": [
        {"date": "2025-09-15", "score": 2.25, "label": "Hawkish", "source": "seed",
         "policy_score": 2.50, "policy_label": "Hawkish", "balance_sheet_score": 1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 2.00, "label": "Hawkish", "source": "seed",
         "policy_score": 2.25, "policy_label": "Hawkish", "balance_sheet_score": 1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.00, "policy_label": "Hawkish", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -2.00, "policy_label": "Dovish", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.75, "policy_label": "Dovish", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
    ],
    "Swati Dhingra": [
        {"date": "2025-09-15", "score": -2.75, "label": "Dovish", "source": "seed",
         "policy_score": -3.00, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -2.50, "label": "Dovish", "source": "seed",
         "policy_score": -2.75, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -2.50, "label": "Dovish", "source": "seed",
         "policy_score": -2.75, "policy_label": "Dovish", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -2.75, "label": "Dovish", "source": "seed",
         "policy_score": -3.00, "policy_label": "Dovish", "balance_sheet_score": -1.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -2.50, "label": "Dovish", "source": "seed",
         "policy_score": -2.75, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
    ],
    "Alan Taylor": [
        {"date": "2025-09-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
    ],
}


def _load_extra_seed_data() -> None:
    """Merge extra seed data from ``local/boe_seed_data.py`` if present."""
    try:
        from local.boe_seed_data import EXTRA_SEED_DATA  # type: ignore[import-not-found]
        for name, entries in EXTRA_SEED_DATA.items():
            if name not in SEED_DATA:
                SEED_DATA[name] = []
            existing_dates = {e["date"] for e in SEED_DATA[name]}
            for entry in entries:
                if entry["date"] not in existing_dates:
                    SEED_DATA[name].append(entry)
    except ImportError:
        pass


_load_extra_seed_data()


def _backfill_entry(entry: dict) -> dict:
    """Ensure an entry has dual-dimension fields (backward compat for old data)."""
    if "policy_score" not in entry:
        entry["policy_score"] = entry.get("score", 0.0)
        entry["policy_label"] = _score_label(entry["policy_score"])
    if "balance_sheet_score" not in entry:
        entry["balance_sheet_score"] = 0.0
        entry["balance_sheet_label"] = "Neutral"
    return entry


def load_history() -> dict[str, list[dict]]:
    """Load stance history from disk, merging with seed data."""
    ensure_dirs()
    history = {}

    # Start with seed data
    for name, entries in SEED_DATA.items():
        history[name] = list(entries)

    # Overlay persisted data
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            persisted = json.load(f)
        for name, entries in persisted.items():
            if name not in history:
                history[name] = []
            existing_dates = {e["date"] for e in history[name]}
            for entry in entries:
                if entry["date"] not in existing_dates:
                    history[name].append(entry)

    # Sort all by date and backfill missing fields
    for name in history:
        history[name] = [_backfill_entry(e) for e in history[name]]
        history[name].sort(key=lambda e: e["date"])

    return history


def save_history(history: dict[str, list[dict]]):
    """Save full stance history to disk."""
    ensure_dirs()
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def add_stance(
    name: str,
    score: float,
    label: str,
    date: str | None = None,
    source: str = "live",
    evidence: list[dict] | None = None,
    policy_score: float | None = None,
    policy_label: str | None = None,
    balance_sheet_score: float | None = None,
    balance_sheet_label: str | None = None,
) -> dict[str, list[dict]]:
    """Add a new stance entry for a participant."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    history = load_history()

    if name not in history:
        history[name] = []

    if policy_score is None:
        policy_score = score
    if policy_label is None:
        policy_label = _score_label(policy_score)
    if balance_sheet_score is None:
        balance_sheet_score = 0.0
    if balance_sheet_label is None:
        balance_sheet_label = _score_label(balance_sheet_score)

    existing_dates = {e["date"]: i for i, e in enumerate(history[name])}
    entry = {
        "date": date,
        "score": round(score, 3),
        "label": label,
        "source": source,
        "policy_score": round(policy_score, 3),
        "policy_label": policy_label,
        "balance_sheet_score": round(balance_sheet_score, 3),
        "balance_sheet_label": balance_sheet_label,
    }
    if evidence:
        entry["evidence"] = evidence

    if date in existing_dates:
        history[name][existing_dates[date]] = entry
    else:
        history[name].append(entry)
        history[name].sort(key=lambda e: e["date"])

    save_history(history)
    return history


def get_latest_stance(name: str) -> dict | None:
    """Get the most recent stance for a participant."""
    history = load_history()
    entries = history.get(name, [])
    if not entries:
        return None
    return _backfill_entry(entries[-1])
