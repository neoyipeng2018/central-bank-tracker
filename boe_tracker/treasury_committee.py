"""Treasury Committee hearing scraper for MPC member testimony."""

import logging
import re
import time

import requests
from bs4 import BeautifulSoup

from boe_tracker import config as cfg
from boe_tracker.participants import PARTICIPANTS

logger = logging.getLogger(__name__)

TREASURY_COMMITTEE_URL = cfg.TREASURY_COMMITTEE_URL

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# MPC members' last names for matching
_MPC_LAST_NAMES = {p.name.split()[-1].lower() for p in PARTICIPANTS}


def fetch_hearing_urls(limit: int = 10) -> list[dict]:
    """Scrape the Treasury Committee oral evidence page for BOE-related hearings."""
    try:
        resp = requests.get(TREASURY_COMMITTEE_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch Treasury Committee page: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    # Look for evidence session links
    for link in soup.find_all("a", href=True):
        title = link.get_text(strip=True)
        href = link.get("href", "")

        if not title:
            continue

        title_lower = title.lower()
        # Filter for BOE-related hearings
        boe_keywords = [
            "bank of england", "monetary policy", "inflation report",
            "financial stability", "governor",
        ]
        if not any(kw in title_lower for kw in boe_keywords):
            # Also check if any MPC member name appears
            if not any(name in title_lower for name in _MPC_LAST_NAMES):
                continue

        if href.startswith("/"):
            href = "https://committees.parliament.uk" + href

        results.append({
            "title": title,
            "url": href,
        })

        if len(results) >= limit:
            break

    logger.info(f"Found {len(results)} Treasury Committee BOE hearings")
    return results


def scrape_hearing_text(url: str) -> str:
    """Scrape oral evidence transcript text from a hearing page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch hearing page {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "lxml")

    # Parliamentary evidence transcripts are typically in the main content area
    content = (
        soup.select_one(".evidence-text")
        or soup.select_one(".content-area")
        or soup.select_one("article")
        or soup.select_one("#mainContent")
    )

    if content:
        text = content.get_text(" ", strip=True)
    else:
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    text = re.sub(r"\s+", " ", text).strip()
    return text[:5000]


def extract_member_statements(text: str, member_name: str) -> str:
    """Extract statements by a specific MPC member from hearing transcript.

    Looks for Q&A patterns where the member is answering.
    """
    last_name = member_name.split()[-1]
    # Common patterns in parliamentary transcripts:
    # "Mr Bailey:" or "Andrew Bailey:" or "Governor:"
    patterns = [
        rf"{last_name}:\s*",
        rf"(?:Mr|Ms|Mrs|Dr|Sir|Dame)\s+{last_name}:\s*",
        rf"{member_name}:\s*",
    ]

    statements = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start = match.end()
            # Find the next speaker (pattern: "Name:" or "Q\d+")
            next_speaker = re.search(
                r"(?:Mr|Ms|Mrs|Dr|Sir|Dame)\s+\w+:|Q\d+\s", text[start:]
            )
            end = start + next_speaker.start() if next_speaker else min(start + 500, len(text))
            statement = text[start:end].strip()
            if len(statement) > 20:
                statements.append(statement)

    return " ".join(statements[:3])[:3000]


def fetch_treasury_hearings(max_results: int = 3) -> list[dict]:
    """Fetch recent Treasury Committee hearings related to BOE/MPC.

    Returns list of dicts with source, title, body, url, date.
    """
    results = []
    hearings = fetch_hearing_urls(limit=max_results * 2)

    for hearing in hearings:
        url = hearing["url"]
        title = hearing["title"]

        time.sleep(cfg.RATE_LIMIT_SECONDS)
        text = scrape_hearing_text(url)

        if not text:
            continue

        results.append({
            "source": "treasury_committee",
            "title": title,
            "body": text,
            "url": url,
            "date": "",
        })

        if len(results) >= max_results:
            break

    return results


def fetch_hearings_for_participant(
    participant_name: str, max_results: int = 3
) -> list[dict]:
    """Fetch Treasury Committee hearing excerpts for a specific MPC member."""
    results = []
    hearings = fetch_hearing_urls(limit=10)

    for hearing in hearings:
        url = hearing["url"]
        title = hearing["title"]

        time.sleep(cfg.RATE_LIMIT_SECONDS)
        text = scrape_hearing_text(url)

        if not text:
            continue

        # Extract member-specific statements
        member_text = extract_member_statements(text, participant_name)
        if not member_text:
            # Check if the member is mentioned at all
            last_name = participant_name.split()[-1].lower()
            if last_name not in text.lower():
                continue
            member_text = text[:3000]

        results.append({
            "source": "treasury_committee",
            "title": f"{title} - {participant_name}",
            "body": member_text,
            "url": url,
            "date": "",
        })

        if len(results) >= max_results:
            break

    return results
