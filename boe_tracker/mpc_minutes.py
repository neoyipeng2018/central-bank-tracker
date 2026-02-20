"""MPC minutes PDF parsing for vote records and member statements."""

import logging
import os
import re
import time

import requests
from bs4 import BeautifulSoup

from boe_tracker import config as cfg

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "boe")
MINUTES_DIR = os.path.join(DATA_DIR, "minutes")

MPC_MINUTES_URL = cfg.MPC_MINUTES_URL

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def ensure_dirs():
    os.makedirs(MINUTES_DIR, exist_ok=True)


def fetch_recent_minutes_urls(limit: int = 5) -> list[dict]:
    """Scrape the MPC minutes index page for recent PDF links."""
    try:
        resp = requests.get(MPC_MINUTES_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch MPC minutes index: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    # BOE lists minutes as links on the summary-and-minutes page
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        if not title:
            continue

        # Match monetary policy summary links
        if "monetary-policy-summary-and-minutes" in href or "mpc-minutes" in href.lower():
            if href.startswith("/"):
                href = "https://www.bankofengland.co.uk" + href

            results.append({
                "title": title,
                "url": href,
            })
            if len(results) >= limit:
                break

    logger.info(f"Found {len(results)} recent MPC minutes links")
    return results


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed; skipping PDF extraction")
        return ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"Failed to extract text from PDF {pdf_path}: {e}")
        return ""


def download_pdf(url: str, filename: str) -> str | None:
    """Download a PDF to the minutes cache directory."""
    ensure_dirs()
    filepath = os.path.join(MINUTES_DIR, filename)

    if os.path.exists(filepath):
        return filepath

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath
    except Exception as e:
        logger.warning(f"Failed to download MPC minutes PDF {url}: {e}")
        return None


def scrape_minutes_html(url: str) -> str:
    """Scrape MPC minutes from the HTML page (when no PDF is available)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch MPC minutes page {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.text, "lxml")

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
    return text[:5000]


def parse_vote_record(text: str) -> dict | None:
    """Extract voting record from minutes text.

    Looks for patterns like:
    "7 members voted to maintain Bank Rate at 4.75%"
    "2 members preferred to reduce Bank Rate by 0.25 percentage points"
    """
    votes = {}

    # Match vote counts
    maintain_match = re.search(
        r"(\d+)\s+members?\s+voted\s+to\s+(?:maintain|keep|hold)\s+Bank\s+Rate",
        text, re.IGNORECASE,
    )
    cut_match = re.search(
        r"(\d+)\s+members?\s+(?:voted|preferred)\s+to\s+(?:reduce|cut|lower)\s+Bank\s+Rate",
        text, re.IGNORECASE,
    )
    hike_match = re.search(
        r"(\d+)\s+members?\s+(?:voted|preferred)\s+to\s+(?:increase|raise)\s+Bank\s+Rate",
        text, re.IGNORECASE,
    )

    if maintain_match:
        votes["hold"] = int(maintain_match.group(1))
    if cut_match:
        votes["cut"] = int(cut_match.group(1))
    if hike_match:
        votes["hike"] = int(hike_match.group(1))

    if not votes:
        return None

    return votes


def fetch_mpc_minutes(max_results: int = 3) -> list[dict]:
    """Fetch and parse recent MPC minutes.

    Returns list of dicts with source, title, body, url, date, and optionally votes.
    """
    results = []
    urls = fetch_recent_minutes_urls(limit=max_results)

    for item in urls:
        url = item["url"]
        title = item["title"]

        time.sleep(cfg.RATE_LIMIT_SECONDS)

        # Try HTML scraping (BOE publishes minutes as web pages)
        text = scrape_minutes_html(url)

        # Try to find and download PDF if link points to one
        if url.endswith(".pdf"):
            safe_name = re.sub(r"[^\w]", "_", title)[:50]
            pdf_path = download_pdf(url, f"{safe_name}.pdf")
            if pdf_path:
                pdf_text = extract_text_from_pdf(pdf_path)
                if pdf_text:
                    text = pdf_text[:5000]

        if not text:
            continue

        entry = {
            "source": "mpc_minutes",
            "title": title,
            "body": text,
            "url": url,
            "date": "",
        }

        # Try to extract vote record
        votes = parse_vote_record(text)
        if votes:
            entry["votes"] = votes

        results.append(entry)

    return results
