"""BOE Interactive Analytical Database (IADB) integration for economic context.

Fetches key UK macro indicators from the BOE IADB.
No API key required -- data is available as CSV exports.
"""

import json
import logging
import os
from datetime import datetime, timedelta

import requests

from boe_tracker import config as cfg

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "boe")
CACHE_FILE = os.path.join(DATA_DIR, "boe_indicators.json")
CACHE_MAX_AGE_HOURS = cfg.BOE_STATS_CACHE_MAX_AGE_HOURS

# BOE IADB CSV endpoint
BOE_IADB_URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"

BOE_STATS_SERIES = cfg.BOE_STATS_SERIES

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def is_available() -> bool:
    """BOE IADB is always available (no API key needed)."""
    return True


def _fetch_series(series_id: str, limit: int = 24) -> list[dict]:
    """Fetch recent observations for a BOE IADB series."""
    params = {
        "SeriesCodes": series_id,
        "CSVF": "TN",
        "UsingCodes": "Y",
        "VPD": "Y",
        "VFD": "N",
    }

    try:
        resp = requests.get(BOE_IADB_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Parse CSV response
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return []

        observations = []
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(",")
            if len(parts) >= 2:
                date_str = parts[0].strip().strip('"')
                value_str = parts[1].strip().strip('"')
                try:
                    value = float(value_str)
                    observations.append({"date": date_str, "value": value})
                except (ValueError, IndexError):
                    continue

        # Sort by date descending and limit
        observations.sort(key=lambda o: o["date"], reverse=True)
        return observations[:limit]

    except Exception as e:
        logger.warning(f"  BOE IADB fetch failed for {series_id}: {e}")
        return []


def _compute_value(observations: list[dict], transform: str) -> dict:
    """Compute the display value from raw observations based on transform type."""
    if not observations:
        return {"latest": None, "previous": None, "change": None, "observations": []}

    latest_val = observations[0]["value"]
    previous_val = observations[1]["value"] if len(observations) > 1 else None

    change = latest_val - previous_val if previous_val is not None else None

    return {
        "latest": round(latest_val, 2),
        "previous": round(previous_val, 2) if previous_val is not None else None,
        "change": round(change, 2) if change is not None else None,
        "observations": observations,
    }


def fetch_all_indicators() -> dict:
    """Fetch all BOE IADB series and return structured indicator data."""
    indicators = {}
    for series_id, meta in BOE_STATS_SERIES.items():
        obs = _fetch_series(series_id)
        computed = _compute_value(obs, meta["transform"])
        indicators[series_id] = {
            **meta,
            **computed,
            "series_id": series_id,
            "last_date": obs[0]["date"] if obs else None,
        }
    return indicators


def fetch_and_cache() -> dict:
    """Fetch indicators with caching (reuse if less than CACHE_MAX_AGE_HOURS old)."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cached_at < timedelta(hours=CACHE_MAX_AGE_HOURS):
                logger.info("Using cached BOE indicators")
                return cached.get("indicators", {})
        except Exception:
            pass

    indicators = fetch_all_indicators()

    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(
                {"cached_at": datetime.now().isoformat(), "indicators": indicators},
                f,
                indent=2,
            )
    except Exception as e:
        logger.warning(f"Failed to cache BOE data: {e}")

    return indicators


def generate_context_summary(indicators: dict) -> str:
    """Generate a one-line human-readable summary of key UK economic conditions."""
    parts = []
    for sid in ["IUDBEDR", "D7BT", "MGSX"]:
        ind = indicators.get(sid)
        if ind and ind.get("latest") is not None:
            parts.append(f"{ind['short_name']}: {ind['latest']}{ind['unit']}")
    return " | ".join(parts) if parts else "Economic data unavailable"
