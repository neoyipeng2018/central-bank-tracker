"""Fetch recent news for MPC participants from pluggable data sources.

Built-in sources: DuckDuckGo news, BOE speeches RSS, BOE news RSS,
MPC minutes, Treasury Committee hearings.
Add your own with ``register_source()`` or the ``@data_source`` decorator.

Each data source is a callable:
    (participant: Participant, **kwargs) -> list[dict]

Each dict must have these keys:
    source  (str) - identifier for your dataset
    title   (str) - headline or title
    body    (str) - article/speech text
    url     (str) - link to original (can be "")
    date    (str) - publication date (can be "")
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Callable

import feedparser
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from boe_tracker import config as cfg
from boe_tracker.participants import Participant
from boe_tracker.boe_speeches import fetch_speeches_for_participant
from boe_tracker.mpc_minutes import fetch_mpc_minutes
from boe_tracker.treasury_committee import fetch_hearings_for_participant

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "boe")
NEWS_DIR = os.path.join(DATA_DIR, "news")

RATE_LIMIT_SECONDS = cfg.RATE_LIMIT_SECONDS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# -- Data source registry ---------------------------------------------------

DataSourceFn = Callable[..., list[dict]]

_SOURCES: list[tuple[str, DataSourceFn, bool]] = []


def register_source(
    name: str, fn: DataSourceFn, *, enabled: bool = True
) -> None:
    """Register a data source function."""
    _SOURCES.append((name, fn, enabled))
    logger.debug(f"Registered data source: {name} (enabled={enabled})")


def data_source(name: str, *, enabled: bool = True):
    """Decorator to register a function as a data source."""
    def decorator(fn: DataSourceFn) -> DataSourceFn:
        register_source(name, fn, enabled=enabled)
        return fn
    return decorator


def list_sources() -> list[tuple[str, bool]]:
    """Return registered source names and their enabled status."""
    return [(name, enabled) for name, _, enabled in _SOURCES]


def enable_source(name: str) -> None:
    """Enable a previously registered source by name."""
    for i, (n, fn, _) in enumerate(_SOURCES):
        if n == name:
            _SOURCES[i] = (n, fn, True)
            return
    raise KeyError(f"No source named '{name}'")


def disable_source(name: str) -> None:
    """Disable a registered source by name."""
    for i, (n, fn, _) in enumerate(_SOURCES):
        if n == name:
            _SOURCES[i] = (n, fn, False)
            return
    raise KeyError(f"No source named '{name}'")


def ensure_dirs():
    os.makedirs(NEWS_DIR, exist_ok=True)


# -- Built-in sources -------------------------------------------------------

def _search_ddg(participant: Participant, max_results: int = 10, **kwargs) -> list[dict]:
    """Search DuckDuckGo for recent news about an MPC participant."""
    short_name = participant.name.split()[-1]
    query = f'{participant.name} OR {short_name} "Bank of England" monetary policy 2026'

    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results, timelimit="m"))
        return [
            {
                "source": "duckduckgo",
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "url": r.get("url", ""),
                "date": r.get("date", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"  DuckDuckGo search failed for {participant.name}: {e}")
        return []


def _fetch_boe_speeches(participant: Participant, max_results: int = 5, **kwargs) -> list[dict]:
    """Fetch speeches from the BOE website for a participant."""
    try:
        return fetch_speeches_for_participant(participant.name, max_results=max_results)
    except Exception as e:
        logger.warning(f"  BOE speeches fetch failed for {participant.name}: {e}")
        return []


def _fetch_boe_news_rss(participant: Participant, **kwargs) -> list[dict]:
    """Fetch relevant items from the BOE news RSS feed."""
    short_name = participant.name.split()[-1].lower()
    results = []

    try:
        feed = feedparser.parse(cfg.BOE_NEWS_RSS)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = (title + " " + summary).lower()
            if short_name in combined or participant.name.lower() in combined:
                pub_date = entry.get("published", "")
                link = entry.get("link", "")
                if link and not link.startswith("http"):
                    link = "https://www.bankofengland.co.uk" + link
                results.append({
                    "source": "boe_news_rss",
                    "title": title,
                    "body": summary,
                    "url": link,
                    "date": pub_date,
                })
    except Exception as e:
        logger.warning(f"  BOE news RSS failed: {e}")

    return results


def _fetch_mpc_minutes(participant: Participant, max_results: int = 3, **kwargs) -> list[dict]:
    """Fetch MPC minutes (committee-level documents, not filtered by participant)."""
    try:
        return fetch_mpc_minutes(max_results=max_results)
    except Exception as e:
        logger.warning(f"  MPC minutes fetch failed: {e}")
        return []


def _fetch_treasury_committee(participant: Participant, max_results: int = 3, **kwargs) -> list[dict]:
    """Fetch Treasury Committee hearing excerpts for a participant."""
    try:
        return fetch_hearings_for_participant(participant.name, max_results=max_results)
    except Exception as e:
        logger.warning(f"  Treasury Committee fetch failed for {participant.name}: {e}")
        return []


def fetch_news_for_participant(
    participant: Participant, max_results: int = 10
) -> list[dict]:
    """Fetch news from all enabled data sources for a single participant."""
    ensure_dirs()
    all_results = []

    for name, fn, enabled in _SOURCES:
        if not enabled:
            logger.debug(f"  Skipping disabled source: {name}")
            continue
        try:
            results = fn(participant, max_results=max_results)
            logger.info(f"  {name}: {len(results)} results for {participant.name}")
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"  Source '{name}' failed for {participant.name}: {e}")

    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for r in all_results:
        url = r.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduped.append(r)
    all_results = deduped

    # Save to file
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = participant.name.replace(" ", "_").replace(".", "")
    filename = f"{date_str}_{safe_name}.json"
    filepath = os.path.join(NEWS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(
            {
                "participant": participant.name,
                "fetch_date": date_str,
                "result_count": len(all_results),
                "results": all_results,
            },
            f,
            indent=2,
        )

    logger.info(f"  Saved {len(all_results)} results to {filename}")
    return all_results


# -- Register built-in sources -----------------------------------------------

register_source("duckduckgo", _search_ddg)
register_source("boe_speeches", _fetch_boe_speeches)
register_source("boe_news_rss", _fetch_boe_news_rss)
register_source("mpc_minutes", _fetch_mpc_minutes)
register_source("treasury_committee", _fetch_treasury_committee)


def load_cached_news(participant: Participant) -> list[dict] | None:
    """Load today's cached news for a participant, if available."""
    ensure_dirs()
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = participant.name.replace(" ", "_").replace(".", "")
    filename = f"{date_str}_{safe_name}.json"
    filepath = os.path.join(NEWS_DIR, filename)

    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
        return data.get("results", [])
    return None
