"""Historical stance storage with seed data for FOMC participants."""

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_DIR = os.path.join(DATA_DIR, "historical")
HISTORY_FILE = os.path.join(HISTORY_DIR, "stance_history.json")


def ensure_dirs():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _score_label(score: float) -> str:
    if score > 1.5:
        return "Hawkish"
    elif score < -1.5:
        return "Dovish"
    return "Neutral"


# Seed data: historical stances for context (synthetic but realistic)
SEED_DATA: dict[str, list[dict]] = {
    "Kevin M. Warsh": [
        {"date": "2025-09-15", "score": 2.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 2.50, "balance_sheet_label": "Hawkish"},
        {"date": "2025-10-15", "score": 2.50, "label": "Hawkish", "source": "seed",
         "policy_score": 2.50, "policy_label": "Hawkish", "balance_sheet_score": 2.50, "balance_sheet_label": "Hawkish"},
        {"date": "2025-11-15", "score": 2.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 2.25, "balance_sheet_label": "Hawkish"},
        {"date": "2025-12-15", "score": 3.00, "label": "Hawkish", "source": "seed",
         "policy_score": 3.00, "policy_label": "Hawkish", "balance_sheet_score": 2.50, "balance_sheet_label": "Hawkish"},
        {"date": "2026-01-15", "score": 2.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 2.50, "balance_sheet_label": "Hawkish"},
    ],
    "Jerome H. Powell": [
        {"date": "2025-09-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
    ],
    "Philip N. Jefferson": [
        {"date": "2025-09-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
    ],
    "Michael S. Barr": [
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
    "Michelle W. Bowman": [
        {"date": "2025-09-15", "score": 3.00, "label": "Hawkish", "source": "seed",
         "policy_score": 3.25, "policy_label": "Hawkish", "balance_sheet_score": 2.00, "balance_sheet_label": "Hawkish"},
        {"date": "2025-10-15", "score": 2.75, "label": "Hawkish", "source": "seed",
         "policy_score": 3.00, "policy_label": "Hawkish", "balance_sheet_score": 1.75, "balance_sheet_label": "Hawkish"},
        {"date": "2025-11-15", "score": 2.50, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 1.75, "balance_sheet_label": "Hawkish"},
        {"date": "2025-12-15", "score": 2.50, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 1.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 2.25, "label": "Hawkish", "source": "seed",
         "policy_score": 2.50, "policy_label": "Hawkish", "balance_sheet_score": 1.50, "balance_sheet_label": "Neutral"},
    ],
    "Christopher J. Waller": [
        {"date": "2025-09-15", "score": 2.50, "label": "Hawkish", "source": "seed",
         "policy_score": 2.75, "policy_label": "Hawkish", "balance_sheet_score": 1.75, "balance_sheet_label": "Hawkish"},
        {"date": "2025-10-15", "score": 2.00, "label": "Hawkish", "source": "seed",
         "policy_score": 2.25, "policy_label": "Hawkish", "balance_sheet_score": 1.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.00, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.50, "label": "Neutral", "source": "seed",
         "policy_score": 1.75, "policy_label": "Hawkish", "balance_sheet_score": 1.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.00, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
    ],
    "Lisa D. Cook": [
        {"date": "2025-09-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -1.75, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
    ],
    "Adriana D. Kugler": [
        {"date": "2025-09-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
    ],
    "John C. Williams": [
        {"date": "2025-09-15", "score": -0.25, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
    ],
    "Patrick T. Harker": [
        {"date": "2025-09-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.25, "balance_sheet_label": "Neutral"},
    ],
    "Thomas I. Barkin": [
        {"date": "2025-09-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 0.75, "label": "Neutral", "source": "seed",
         "policy_score": 0.75, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
    ],
    "Raphael W. Bostic": [
        {"date": "2025-09-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.50, "label": "Neutral", "source": "seed",
         "policy_score": -0.50, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.25, "balance_sheet_label": "Neutral"},
    ],
    "Mary C. Daly": [
        {"date": "2025-09-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -0.75, "label": "Neutral", "source": "seed",
         "policy_score": -0.75, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.25, "label": "Neutral", "source": "seed",
         "policy_score": -1.25, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.00, "label": "Neutral", "source": "seed",
         "policy_score": -1.00, "policy_label": "Neutral", "balance_sheet_score": -0.50, "balance_sheet_label": "Neutral"},
    ],
    "Susan M. Collins": [
        {"date": "2025-09-15", "score": 0.50, "label": "Neutral", "source": "seed",
         "policy_score": 0.50, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 0.00, "label": "Neutral", "source": "seed",
         "policy_score": 0.00, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 0.25, "label": "Neutral", "source": "seed",
         "policy_score": 0.25, "policy_label": "Neutral", "balance_sheet_score": 0.00, "balance_sheet_label": "Neutral"},
    ],
    "Beth M. Hammack": [
        {"date": "2025-09-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
    ],
    "Austan D. Goolsbee": [
        {"date": "2025-09-15", "score": -2.00, "label": "Dovish", "source": "seed",
         "policy_score": -2.25, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -2.00, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -2.00, "policy_label": "Dovish", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -2.00, "label": "Dovish", "source": "seed",
         "policy_score": -2.25, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -2.00, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
    ],
    "Alberto G. Musalem": [
        {"date": "2025-09-15", "score": 1.50, "label": "Neutral", "source": "seed",
         "policy_score": 1.50, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.00, "label": "Neutral", "source": "seed",
         "policy_score": 1.00, "policy_label": "Neutral", "balance_sheet_score": 0.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 1.25, "label": "Neutral", "source": "seed",
         "policy_score": 1.25, "policy_label": "Neutral", "balance_sheet_score": 0.75, "balance_sheet_label": "Neutral"},
    ],
    "Jeffrey R. Schmid": [
        {"date": "2025-09-15", "score": 2.00, "label": "Hawkish", "source": "seed",
         "policy_score": 2.00, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 1.75, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 1.75, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.50, "label": "Neutral", "source": "seed",
         "policy_score": 1.50, "policy_label": "Neutral", "balance_sheet_score": 1.00, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 1.75, "policy_label": "Hawkish", "balance_sheet_score": 1.25, "balance_sheet_label": "Neutral"},
    ],
    "Lorie K. Logan": [
        {"date": "2025-09-15", "score": 2.25, "label": "Hawkish", "source": "seed",
         "policy_score": 2.50, "policy_label": "Hawkish", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": 2.00, "label": "Hawkish", "source": "seed",
         "policy_score": 2.25, "policy_label": "Hawkish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.00, "policy_label": "Hawkish", "balance_sheet_score": -1.25, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": 1.75, "label": "Hawkish", "source": "seed",
         "policy_score": 2.25, "policy_label": "Hawkish", "balance_sheet_score": -1.50, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": 2.00, "label": "Hawkish", "source": "seed",
         "policy_score": 2.25, "policy_label": "Hawkish", "balance_sheet_score": -1.25, "balance_sheet_label": "Neutral"},
    ],
    "Neel Kashkari": [
        {"date": "2025-09-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -1.75, "policy_label": "Dovish", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-10-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
        {"date": "2025-11-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -0.75, "balance_sheet_label": "Neutral"},
        {"date": "2025-12-15", "score": -1.75, "label": "Dovish", "source": "seed",
         "policy_score": -1.75, "policy_label": "Dovish", "balance_sheet_score": -1.25, "balance_sheet_label": "Neutral"},
        {"date": "2026-01-15", "score": -1.50, "label": "Neutral", "source": "seed",
         "policy_score": -1.50, "policy_label": "Neutral", "balance_sheet_score": -1.00, "balance_sheet_label": "Neutral"},
    ],
}


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
            # Merge: add persisted entries that aren't already in seed
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
    """Add a new stance entry for a participant.

    evidence is an optional list of dicts, each with:
        title, url, source_type, keywords, quote
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    history = load_history()

    if name not in history:
        history[name] = []

    # Default policy/BS scores if not provided
    if policy_score is None:
        policy_score = score
    if policy_label is None:
        policy_label = _score_label(policy_score)
    if balance_sheet_score is None:
        balance_sheet_score = 0.0
    if balance_sheet_label is None:
        balance_sheet_label = _score_label(balance_sheet_score)

    # Update existing entry for same date, or append
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
