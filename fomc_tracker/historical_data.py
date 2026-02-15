"""Historical stance storage with seed data for FOMC participants."""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_DIR = os.path.join(DATA_DIR, "historical")
HISTORY_FILE = os.path.join(HISTORY_DIR, "stance_history.json")


def ensure_dirs():
    os.makedirs(HISTORY_DIR, exist_ok=True)


# Seed data: historical stances for context (synthetic but realistic)
SEED_DATA: dict[str, list[dict]] = {
    "Kevin M. Warsh": [
        {"date": "2025-09-15", "score": 0.55, "label": "Hawkish", "source": "seed"},
        {"date": "2025-10-15", "score": 0.50, "label": "Hawkish", "source": "seed"},
        {"date": "2025-11-15", "score": 0.55, "label": "Hawkish", "source": "seed"},
        {"date": "2025-12-15", "score": 0.60, "label": "Hawkish", "source": "seed"},
        {"date": "2026-01-15", "score": 0.55, "label": "Hawkish", "source": "seed"},
    ],
    "Jerome H. Powell": [
        {"date": "2025-09-15", "score": 0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.10, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.05, "label": "Neutral", "source": "seed"},
    ],
    "Philip N. Jefferson": [
        {"date": "2025-09-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.15, "label": "Neutral", "source": "seed"},
    ],
    "Michael S. Barr": [
        {"date": "2025-09-15", "score": -0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.30, "label": "Dovish", "source": "seed"},
        {"date": "2026-01-15", "score": -0.25, "label": "Neutral", "source": "seed"},
    ],
    "Michelle W. Bowman": [
        {"date": "2025-09-15", "score": 0.60, "label": "Hawkish", "source": "seed"},
        {"date": "2025-10-15", "score": 0.55, "label": "Hawkish", "source": "seed"},
        {"date": "2025-11-15", "score": 0.50, "label": "Hawkish", "source": "seed"},
        {"date": "2025-12-15", "score": 0.50, "label": "Hawkish", "source": "seed"},
        {"date": "2026-01-15", "score": 0.45, "label": "Hawkish", "source": "seed"},
    ],
    "Christopher J. Waller": [
        {"date": "2025-09-15", "score": 0.50, "label": "Hawkish", "source": "seed"},
        {"date": "2025-10-15", "score": 0.40, "label": "Hawkish", "source": "seed"},
        {"date": "2025-11-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
        {"date": "2025-12-15", "score": 0.30, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
    ],
    "Lisa D. Cook": [
        {"date": "2025-09-15", "score": -0.30, "label": "Dovish", "source": "seed"},
        {"date": "2025-10-15", "score": -0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.30, "label": "Dovish", "source": "seed"},
        {"date": "2025-12-15", "score": -0.35, "label": "Dovish", "source": "seed"},
        {"date": "2026-01-15", "score": -0.30, "label": "Dovish", "source": "seed"},
    ],
    "Adriana D. Kugler": [
        {"date": "2025-09-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.15, "label": "Neutral", "source": "seed"},
    ],
    "John C. Williams": [
        {"date": "2025-09-15", "score": -0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.10, "label": "Neutral", "source": "seed"},
    ],
    "Patrick T. Harker": [
        {"date": "2025-09-15", "score": 0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": 0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": 0.05, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.10, "label": "Neutral", "source": "seed"},
    ],
    "Thomas I. Barkin": [
        {"date": "2025-09-15", "score": 0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": 0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": 0.10, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.15, "label": "Neutral", "source": "seed"},
    ],
    "Raphael W. Bostic": [
        {"date": "2025-09-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.15, "label": "Neutral", "source": "seed"},
    ],
    "Mary C. Daly": [
        {"date": "2025-09-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": -0.15, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": -0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.25, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": -0.20, "label": "Neutral", "source": "seed"},
    ],
    "Susan M. Collins": [
        {"date": "2025-09-15", "score": 0.10, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": 0.05, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": 0.00, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.05, "label": "Neutral", "source": "seed"},
    ],
    "Beth M. Hammack": [
        {"date": "2025-09-15", "score": 0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": 0.20, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": 0.25, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.20, "label": "Neutral", "source": "seed"},
    ],
    "Austan D. Goolsbee": [
        {"date": "2025-09-15", "score": -0.40, "label": "Dovish", "source": "seed"},
        {"date": "2025-10-15", "score": -0.35, "label": "Dovish", "source": "seed"},
        {"date": "2025-11-15", "score": -0.35, "label": "Dovish", "source": "seed"},
        {"date": "2025-12-15", "score": -0.40, "label": "Dovish", "source": "seed"},
        {"date": "2026-01-15", "score": -0.35, "label": "Dovish", "source": "seed"},
    ],
    "Alberto G. Musalem": [
        {"date": "2025-09-15", "score": 0.30, "label": "Neutral", "source": "seed"},
        {"date": "2025-10-15", "score": 0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-11-15", "score": 0.25, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": 0.20, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.25, "label": "Neutral", "source": "seed"},
    ],
    "Jeffrey R. Schmid": [
        {"date": "2025-09-15", "score": 0.40, "label": "Hawkish", "source": "seed"},
        {"date": "2025-10-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
        {"date": "2025-11-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
        {"date": "2025-12-15", "score": 0.30, "label": "Neutral", "source": "seed"},
        {"date": "2026-01-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
    ],
    "Lorie K. Logan": [
        {"date": "2025-09-15", "score": 0.45, "label": "Hawkish", "source": "seed"},
        {"date": "2025-10-15", "score": 0.40, "label": "Hawkish", "source": "seed"},
        {"date": "2025-11-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
        {"date": "2025-12-15", "score": 0.35, "label": "Hawkish", "source": "seed"},
        {"date": "2026-01-15", "score": 0.40, "label": "Hawkish", "source": "seed"},
    ],
    "Neel Kashkari": [
        {"date": "2025-09-15", "score": -0.35, "label": "Dovish", "source": "seed"},
        {"date": "2025-10-15", "score": -0.30, "label": "Dovish", "source": "seed"},
        {"date": "2025-11-15", "score": -0.30, "label": "Neutral", "source": "seed"},
        {"date": "2025-12-15", "score": -0.35, "label": "Dovish", "source": "seed"},
        {"date": "2026-01-15", "score": -0.30, "label": "Dovish", "source": "seed"},
    ],
}


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
            # Merge: add persisted entries that aren't already in seed
            existing_dates = {e["date"] for e in history[name]}
            for entry in entries:
                if entry["date"] not in existing_dates:
                    history[name].append(entry)

    # Sort all by date
    for name in history:
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
) -> dict[str, list[dict]]:
    """Add a new stance entry for a participant.

    evidence is an optional list of dicts, each with:
        title, url, source_type, keywords, quote
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    history = load_history()

    if name not in history:
        history[name] = []

    # Update existing entry for same date, or append
    existing_dates = {e["date"]: i for i, e in enumerate(history[name])}
    entry = {"date": date, "score": round(score, 3), "label": label, "source": source}
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
    return entries[-1] if entries else None
