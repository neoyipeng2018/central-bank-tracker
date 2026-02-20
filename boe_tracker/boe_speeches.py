"""Scrape Bank of England speech pages for full text."""

import logging
import re

import feedparser
import requests
from bs4 import BeautifulSoup

from boe_tracker import config as cfg
from boe_tracker.participants import PARTICIPANTS

logger = logging.getLogger(__name__)

BOE_SPEECHES_RSS = cfg.BOE_SPEECHES_RSS
BOE_BASE_URL = "https://www.bankofengland.co.uk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_speech_text(url: str) -> str:
    """Scrape the full text of a BOE speech page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch speech {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "lxml")

    # BOE speeches are typically in .page-content or article
    article = (
        soup.select_one(".page-content")
        or soup.select_one("article")
        or soup.select_one("#maincontent")
    )
    if article:
        text = article.get_text(" ", strip=True)
    else:
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    text = re.sub(r"\s+", " ", text).strip()
    return text[:3000]


def fetch_speeches_for_participant(
    participant_name: str, max_results: int = 5
) -> list[dict]:
    """Fetch recent speeches from BOE RSS that match a participant."""
    last_name = participant_name.split()[-1].lower()
    name_parts = participant_name.split()
    first_last = (
        f"{name_parts[0]} {name_parts[-1]}".lower()
        if len(name_parts) >= 2
        else ""
    )
    results = []

    try:
        feed = feedparser.parse(BOE_SPEECHES_RSS)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            author = entry.get("author", "")

            combined = (title + " " + summary + " " + author).lower()
            if last_name not in combined and first_last not in combined:
                continue

            link = entry.get("link", "")
            if link and not link.startswith("http"):
                link = BOE_BASE_URL + link

            pub_date = entry.get("published", "")

            # Scrape full text
            speech_text = scrape_speech_text(link) if link else ""
            body = speech_text if speech_text else summary

            results.append({
                "source": "boe_speeches",
                "title": title,
                "body": body,
                "url": link,
                "date": pub_date,
            })

            if len(results) >= max_results:
                break
    except Exception as e:
        logger.warning(f"BOE speeches RSS failed: {e}")

    return results
