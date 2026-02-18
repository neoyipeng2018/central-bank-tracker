"""FRED (Federal Reserve Economic Data) integration for economic context.

Fetches key macro indicators from the FRED API and caches them locally.
Requires a free API key from https://fred.stlouisfed.org/docs/api/api_key.html
Set via the ``FRED_API_KEY`` environment variable.
"""

import json
import logging
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from fomc_tracker import config as cfg

load_dotenv()

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CACHE_FILE = os.path.join(DATA_DIR, "fred_indicators.json")
CACHE_MAX_AGE_HOURS = cfg.FRED_CACHE_MAX_AGE_HOURS

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Series we track, with display metadata
FRED_SERIES = cfg.FRED_SERIES


def is_available() -> bool:
    """Check if the FRED API key is configured."""
    return bool(os.environ.get("FRED_API_KEY", "").strip())


def _get_api_key() -> str:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise RuntimeError("FRED_API_KEY environment variable not set")
    return key


def _fetch_series(series_id: str, limit: int | None = None) -> list[dict]:
    """Fetch recent observations for a FRED series."""
    if limit is None:
        limit = cfg.FRED_FETCH_LIMIT
    api_key = _get_api_key()
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    try:
        resp = requests.get(FRED_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])
        # Filter out missing values
        return [
            {"date": o["date"], "value": float(o["value"])}
            for o in observations
            if o.get("value", ".") != "."
        ]
    except Exception as e:
        logger.warning(f"  FRED fetch failed for {series_id}: {e}")
        return []


def _compute_value(observations: list[dict], transform: str) -> dict:
    """Compute the display value from raw observations based on transform type."""
    if not observations:
        return {"latest": None, "previous": None, "change": None, "observations": []}

    latest_val = observations[0]["value"]
    previous_val = observations[1]["value"] if len(observations) > 1 else None

    if transform == "pct_change_year" and len(observations) >= 13:
        # Year-over-year percent change
        year_ago = observations[12]["value"]
        computed = ((latest_val - year_ago) / year_ago) * 100 if year_ago else None
        prev_year_ago = observations[13]["value"] if len(observations) >= 14 else None
        prev_computed = (
            ((observations[1]["value"] - prev_year_ago) / prev_year_ago) * 100
            if prev_year_ago and previous_val is not None
            else None
        )
        change = computed - prev_computed if computed is not None and prev_computed is not None else None
        return {
            "latest": round(computed, 2) if computed is not None else None,
            "previous": round(prev_computed, 2) if prev_computed is not None else None,
            "change": round(change, 2) if change is not None else None,
            "observations": observations,
        }
    elif transform == "pct_change_quarter" and len(observations) >= 2:
        # QoQ annualised (FRED GDP is already annualised rate)
        change = latest_val - previous_val if previous_val is not None else None
        return {
            "latest": round(latest_val, 2),
            "previous": round(previous_val, 2) if previous_val is not None else None,
            "change": round(change, 2) if change is not None else None,
            "observations": observations,
        }
    elif transform == "change" and len(observations) >= 2:
        # Month-over-month change (e.g. payrolls in thousands)
        change_val = latest_val - previous_val if previous_val is not None else None
        return {
            "latest": round(change_val, 1) if change_val is not None else round(latest_val, 1),
            "previous": round(
                previous_val - observations[2]["value"], 1
            ) if len(observations) >= 3 else None,
            "change": None,
            "observations": observations,
        }
    else:
        # Level (direct value)
        change = latest_val - previous_val if previous_val is not None else None
        return {
            "latest": round(latest_val, 2),
            "previous": round(previous_val, 2) if previous_val is not None else None,
            "change": round(change, 2) if change is not None else None,
            "observations": observations,
        }


def fetch_all_indicators() -> dict:
    """Fetch all FRED series and return structured indicator data."""
    indicators = {}
    for series_id, meta in FRED_SERIES.items():
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

    # Check cache freshness
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cached_at < timedelta(hours=CACHE_MAX_AGE_HOURS):
                logger.info("Using cached FRED indicators")
                return cached.get("indicators", {})
        except Exception:
            pass  # cache corrupt, refetch

    # Fetch fresh data
    indicators = fetch_all_indicators()

    # Save cache
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(
                {"cached_at": datetime.now().isoformat(), "indicators": indicators},
                f,
                indent=2,
            )
    except Exception as e:
        logger.warning(f"Failed to cache FRED data: {e}")

    return indicators


def generate_context_summary(indicators: dict) -> str:
    """Generate a one-line human-readable summary of key economic conditions."""
    parts = []
    for sid in ["CPIAUCSL", "PCEPILFE", "UNRATE", "FEDFUNDS"]:
        ind = indicators.get(sid)
        if ind and ind.get("latest") is not None:
            parts.append(f"{ind['short_name']}: {ind['latest']}{ind['unit']}")
    return " | ".join(parts) if parts else "Economic data unavailable"
