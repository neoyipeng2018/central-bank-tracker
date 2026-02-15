"""Fetch recent news for FOMC participants from pluggable data sources.

Built-in sources: DuckDuckGo news, Fed RSS feeds, BIS speeches.
Add your own with ``register_source()`` or the ``@data_source`` decorator.

Each data source is a callable:
    (participant: Participant, **kwargs) -> list[dict]

Each dict must have these keys:
    source  (str) - identifier for your dataset, e.g. "my_api"
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
from datetime import datetime, timedelta
from typing import Callable

import feedparser
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from fomc_tracker.participants import Participant

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NEWS_DIR = os.path.join(DATA_DIR, "news")

# Fed RSS feeds for speeches and press releases
FED_RSS_FEEDS = [
    "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "https://www.federalreserve.gov/feeds/press_speech.xml",
    "https://www.federalreserve.gov/feeds/press_testimony.xml",
]

# BIS central bankers' speeches RSS (includes Fed officials)
BIS_SPEECHES_RSS = "https://www.bis.org/doclist/cbspeeches.rss?paging_length=50"

BIS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

RATE_LIMIT_SECONDS = 1.5

# ── Data source registry ───────────────────────────────────────────────────────

# Type alias for a data source callable.
DataSourceFn = Callable[..., list[dict]]

# Registry: list of (name, callable, enabled).
_SOURCES: list[tuple[str, DataSourceFn, bool]] = []


def register_source(
    name: str, fn: DataSourceFn, *, enabled: bool = True
) -> None:
    """Register a data source function.

    Args:
        name: Human-readable name (used in logs).
        fn: Callable with signature (participant: Participant, **kwargs) -> list[dict].
             Each returned dict must contain: source, title, body, url, date.
        enabled: Set False to register but skip during fetches.

    Example::

        def my_fetcher(participant, **kwargs):
            # hit your API, read a CSV, whatever
            return [{"source": "my_api", "title": "...", "body": "...",
                     "url": "", "date": "2026-02-16"}]

        register_source("my_api", my_fetcher)
    """
    _SOURCES.append((name, fn, enabled))
    logger.debug(f"Registered data source: {name} (enabled={enabled})")


def data_source(name: str, *, enabled: bool = True):
    """Decorator to register a function as a data source.

    Example::

        @data_source("reuters_api")
        def fetch_reuters(participant, **kwargs):
            ...
            return [{"source": "reuters_api", ...}]
    """
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
    """Disable a registered source by name (keeps it in the registry)."""
    for i, (n, fn, _) in enumerate(_SOURCES):
        if n == name:
            _SOURCES[i] = (n, fn, False)
            return
    raise KeyError(f"No source named '{name}'")


def ensure_dirs():
    os.makedirs(NEWS_DIR, exist_ok=True)


def _search_ddg(participant: Participant, max_results: int = 10, **kwargs) -> list[dict]:
    """Search DuckDuckGo for recent news about a participant."""
    # Use short name for better search results
    short_name = participant.name.split()[-1]  # Last name
    query = f"{participant.name} OR {short_name} Federal Reserve monetary policy 2026"

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


def _fetch_fed_rss(participant: Participant, **kwargs) -> list[dict]:
    """Fetch relevant items from Fed RSS feeds."""
    short_name = participant.name.split()[-1].lower()
    results = []

    for feed_url in FED_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                # Check if this entry mentions the participant
                combined = (title + " " + summary).lower()
                if short_name in combined or participant.name.lower() in combined:
                    pub_date = entry.get("published", "")
                    results.append(
                        {
                            "source": "fed_rss",
                            "title": title,
                            "body": summary,
                            "url": entry.get("link", ""),
                            "date": pub_date,
                        }
                    )
        except Exception as e:
            logger.warning(f"  RSS fetch failed ({feed_url}): {e}")

    return results


def _scrape_bis_speech_text(url: str) -> str:
    """Scrape the full text of a BIS speech page."""
    try:
        resp = requests.get(url, headers=BIS_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.debug(f"  Failed to scrape BIS speech {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "lxml")

    # BIS speech text is typically in #cmsContent or the main article area
    article = soup.select_one("#cmsContent") or soup.select_one("#center")
    if article:
        text = article.get_text(" ", strip=True)
    else:
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Truncate to avoid huge payloads (keep first ~3000 chars for classification)
    return text[:3000]


def _fetch_bis_speeches(participant: Participant, **kwargs) -> list[dict]:
    """Fetch matching speeches from BIS central bankers' speeches RSS feed.

    The BIS feed uses <cb:person> with <cb:surname> and <dc:creator> fields,
    making it reliable for speaker matching.
    """
    last_name = participant.name.split()[-1].lower()
    # Also build first-last variant for dc:creator matching (e.g. "Jerome Powell")
    name_parts = participant.name.split()
    first_last = f"{name_parts[0]} {name_parts[-1]}".lower() if len(name_parts) >= 2 else ""
    results = []

    try:
        feed = feedparser.parse(BIS_SPEECHES_RSS)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            creator = entry.get("dc_creator", "") or entry.get("author", "")

            # Match by surname in title/creator or full first-last name
            combined = (title + " " + creator + " " + summary).lower()
            if last_name not in combined:
                continue
            # Avoid false positives on common surnames by also checking first name
            if first_last and first_last not in combined:
                # If first-last doesn't match, require surname appears in title prefix
                # (BIS titles start with "Speaker Name: Title")
                title_prefix = title[:60].lower()
                if last_name not in title_prefix:
                    continue

            link = entry.get("link", "")
            pub_date = entry.get("dc_date", "") or entry.get("published", "")

            # Scrape full speech text for richer classification signal
            speech_text = _scrape_bis_speech_text(link) if link else ""

            body = speech_text if speech_text else summary
            results.append(
                {
                    "source": "bis_speeches",
                    "title": title,
                    "body": body,
                    "url": link,
                    "date": pub_date,
                }
            )
    except Exception as e:
        logger.warning(f"  BIS speeches RSS failed: {e}")

    return results


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


# ── Register built-in sources ──────────────────────────────────────────────────

register_source("duckduckgo", _search_ddg)
register_source("fed_rss", _fetch_fed_rss)
register_source("bis_speeches", _fetch_bis_speeches)


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
