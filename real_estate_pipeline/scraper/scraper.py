"""
Real estate listing scraper — starter skeleton.

Workflow this follows (build it up in this order, don't skip steps):
  1. Fetch ONE page, print raw HTML length to confirm you got a real response.
  2. Parse that one page, extract fields for ONE listing, print them.
  3. Loop over all listings on that one page.
  4. Add pagination to loop over multiple pages.
  5. Save results to CSV.

Run with: python -m scraper.scraper
"""

import time
import csv
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper.config import (
    BASE_URL,
    HEADERS,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    SELECTORS,
    OUTPUT_CSV_PATH,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def fetch_page(url: str) -> str | None:
    """Fetch a single page and return its HTML, or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def parse_listing(card) -> dict:
    """Extract fields from a single listing card (a BeautifulSoup element)."""

    def safe_text(selector):
        if not selector:
            return None
        el = card.select_one(selector)
        return el.get_text(strip=True) if el else None

    def safe_href(selector):
        if not selector:
            return None
        el = card.select_one(selector)
        return el.get("href") if el else None

    return {
        "title": safe_text(SELECTORS["title"]),
        "price": safe_text(SELECTORS["price"]),
        "location": safe_text(SELECTORS["location"]),
        "rooms": safe_text(SELECTORS["rooms"]),
        "area_sqm": safe_text(SELECTORS["area_sqm"]),
        "link": safe_href(SELECTORS["link"]),
    }


def parse_page(html: str) -> list[dict]:
    """Parse a page's HTML into a list of listing dicts."""
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(SELECTORS["listing_card"])
    logger.info(f"Found {len(cards)} listing cards on page")
    return [parse_listing(card) for card in cards]


def save_to_csv(listings: list[dict], path: str):
    if not listings:
        logger.warning("No listings to save.")
        return

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=listings[0].keys())
        writer.writeheader()
        writer.writerows(listings)

    logger.info(f"Saved {len(listings)} listings to {output_path}")


def main():
    logger.info(f"Fetching: {BASE_URL}")
    html = fetch_page(BASE_URL)

    if html is None:
        logger.error("No HTML returned, stopping.")
        return

    listings = parse_page(html)

    # Inspect the first result to sanity check your selectors
    if listings:
        logger.info(f"First listing parsed: {listings[0]}")

    time.sleep(REQUEST_DELAY_SECONDS)
    save_to_csv(listings, OUTPUT_CSV_PATH)


if __name__ == "__main__":
    main()
