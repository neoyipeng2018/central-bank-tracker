"""Scrape Federal Reserve speech pages for full text."""

import logging
import os
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SPEECHES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "speeches")

FED_SPEECH_INDEX = "https://www.federalreserve.gov/newsevents/speeches.htm"
FED_BASE_URL = "https://www.federalreserve.gov"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def ensure_dirs():
    os.makedirs(SPEECHES_DIR, exist_ok=True)


def fetch_recent_speech_urls(limit: int = 30) -> list[dict]:
    """Fetch recent speech URLs from the Fed speeches index page."""
    try:
        resp = requests.get(FED_SPEECH_INDEX, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch speech index: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    speeches = []

    rows = soup.select(".row.eventlist .col-xs-12.col-md-9")
    for row in rows[:limit]:
        link_tag = row.find("a")
        if not link_tag:
            continue
        title = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        if href.startswith("/"):
            href = FED_BASE_URL + href

        # Try to find speaker and date
        desc = row.get_text(" ", strip=True)
        speeches.append({"title": title, "url": href, "description": desc})

    logger.info(f"Found {len(speeches)} recent speeches on Fed website")
    return speeches


def scrape_speech_text(url: str) -> str:
    """Scrape the full text of a Fed speech page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch speech {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "lxml")

    # Fed speeches usually in div#article or similar
    article = soup.select_one("#article") or soup.select_one(".col-xs-12.col-sm-8.col-md-8")
    if article:
        text = article.get_text(" ", strip=True)
    else:
        # Fallback: get all paragraphs
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_speeches_for_participant(name: str, limit: int = 5) -> list[dict]:
    """Find recent speeches by a specific FOMC participant."""
    all_speeches = fetch_recent_speech_urls(limit=50)
    last_name = name.split()[-1].lower()

    matching = []
    for speech in all_speeches:
        desc_lower = speech["description"].lower()
        if last_name in desc_lower or name.lower() in desc_lower:
            matching.append(speech)

    return matching[:limit]
