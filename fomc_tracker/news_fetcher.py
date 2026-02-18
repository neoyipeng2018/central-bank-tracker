"""Fetch recent news for FOMC participants from pluggable data sources.

Built-in sources: DuckDuckGo news, Fed RSS feeds, BIS speeches,
Fed speeches, FOMC minutes/statements, and regional Fed blogs.
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

from fomc_tracker import config as cfg
from fomc_tracker.participants import Participant
from fomc_tracker.fed_speeches import find_speeches_for_participant, scrape_speech_text

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NEWS_DIR = os.path.join(DATA_DIR, "news")

# Fed RSS feeds for speeches and press releases
FED_RSS_FEEDS = cfg.FED_RSS_FEEDS

# BIS central bankers' speeches RSS (includes Fed officials)
BIS_SPEECHES_RSS = cfg.BIS_SPEECHES_RSS

BIS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

RATE_LIMIT_SECONDS = cfg.RATE_LIMIT_SECONDS

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


# ── Fed Speeches source ───────────────────────────────────────────────────────

def _fetch_fed_speeches(participant: Participant, max_results: int = 5, **kwargs) -> list[dict]:
    """Fetch speeches from the Federal Reserve website for a participant."""
    results = []
    try:
        matches = find_speeches_for_participant(participant.name, limit=max_results)
        for speech in matches:
            url = speech.get("url", "")
            # Scrape full text for richer classification signal
            if url:
                time.sleep(RATE_LIMIT_SECONDS)
                text = scrape_speech_text(url)
                body = text[:3000] if text else speech.get("description", "")
            else:
                body = speech.get("description", "")

            results.append(
                {
                    "source": "fed_speeches",
                    "title": speech.get("title", ""),
                    "body": body,
                    "url": url,
                    "date": "",
                }
            )
    except Exception as e:
        logger.warning(f"  Fed speeches fetch failed for {participant.name}: {e}")

    return results


# ── FOMC Minutes & Statements source ─────────────────────────────────────────

FOMC_KEYWORDS = ["statement", "minutes", "implementation note", "press conference"]


def _fetch_fomc_minutes(participant: Participant, max_results: int = 3, **kwargs) -> list[dict]:
    """Fetch FOMC statements, minutes, and press conference transcripts.

    These are committee-level documents (not filtered by participant name).
    """
    results = []
    feed_url = "https://www.federalreserve.gov/feeds/press_monetary.xml"

    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.get("title", "")
            title_lower = title.lower()

            # Only include statements, minutes, implementation notes, press conferences
            if not any(kw in title_lower for kw in FOMC_KEYWORDS):
                continue

            link = entry.get("link", "")
            pub_date = entry.get("published", "")
            summary = entry.get("summary", "")

            # Scrape full text for richer signal
            body = summary
            if link:
                try:
                    time.sleep(RATE_LIMIT_SECONDS)
                    resp = requests.get(link, headers=BIS_HEADERS, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")
                    article = (
                        soup.select_one("#article")
                        or soup.select_one(".col-xs-12.col-sm-8.col-md-8")
                    )
                    if article:
                        text = article.get_text(" ", strip=True)
                    else:
                        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
                    text = re.sub(r"\s+", " ", text).strip()
                    if text:
                        body = text[:3000]
                except Exception as e:
                    logger.debug(f"  Failed to scrape FOMC document {link}: {e}")

            results.append(
                {
                    "source": "fomc_minutes",
                    "title": title,
                    "body": body,
                    "url": link,
                    "date": pub_date,
                }
            )
            if len(results) >= max_results:
                break
    except Exception as e:
        logger.warning(f"  FOMC minutes/statements fetch failed: {e}")

    return results


# ── Regional Fed Blogs source ─────────────────────────────────────────────────

REGIONAL_FED_BLOGS = cfg.REGIONAL_FED_BLOGS


def _fetch_regional_fed_blogs(
    participant: Participant, max_results: int = 5, **kwargs
) -> list[dict]:
    """Fetch blog posts from regional Fed bank blogs matching a participant.

    Matches by the participant's institution, then filters by author name
    or last-name mention in title/summary.  Returns empty for Board of
    Governors members (they don't publish on regional blogs).
    """
    # Board of Governors members don't publish on regional blogs
    if participant.is_governor or participant.institution == "Incoming":
        return []

    feeds = REGIONAL_FED_BLOGS.get(participant.institution, [])
    if not feeds:
        return []

    last_name = participant.name.split()[-1].lower()
    name_parts = participant.name.split()
    first_last = f"{name_parts[0]} {name_parts[-1]}".lower() if len(name_parts) >= 2 else ""
    results = []

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                author = entry.get("author", "") or entry.get("dc_creator", "")

                # Check if this entry is by or mentions the participant
                combined = (title + " " + summary + " " + author).lower()
                if last_name not in combined and first_last not in combined:
                    continue

                # Strip HTML from summary
                if "<" in summary:
                    soup = BeautifulSoup(summary, "lxml")
                    summary = soup.get_text(" ", strip=True)

                pub_date = entry.get("published", "") or entry.get("dc_date", "")

                results.append(
                    {
                        "source": "regional_fed_blog",
                        "title": title,
                        "body": summary[:3000],
                        "url": entry.get("link", ""),
                        "date": pub_date,
                    }
                )
                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning(f"  Regional Fed blog fetch failed ({feed_url}): {e}")

        if len(results) >= max_results:
            break

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

    # Deduplicate by URL (multiple sources may return the same page)
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


# ── Register built-in sources ──────────────────────────────────────────────────

register_source("duckduckgo", _search_ddg)
register_source("fed_rss", _fetch_fed_rss)
register_source("bis_speeches", _fetch_bis_speeches)
register_source("fed_speeches", _fetch_fed_speeches)
register_source("fomc_minutes", _fetch_fomc_minutes)
register_source("regional_fed_blogs", _fetch_regional_fed_blogs)


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
