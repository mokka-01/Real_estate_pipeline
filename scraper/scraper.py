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
    SPEC_LABELS,
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


def parse_specs(card) -> dict:
    """
    Rooms / area / floor share one CSS class across all three <dd> values,
    so we can't select them directly. Instead we walk the <dt>/<dd> pairs
    and match each value to its label text (see SPEC_LABELS in config.py).
    """
    specs = {"rooms": None, "area_sqm": None, "floor": None}
    dl = card.select_one(SELECTORS["specs_list"])
    if not dl:
        return specs

    labels = dl.find_all("dt")
    values = dl.find_all("dd")
    for label, value in zip(labels, values):
        field_name = SPEC_LABELS.get(label.get_text(strip=True))
        if field_name:
            specs[field_name] = value.get_text(strip=True)
    return specs


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

    listing = {
        "title": safe_text(SELECTORS["title"]),
        "address": safe_text(SELECTORS["address"]),
        "price_eur": safe_text(SELECTORS["price_main"]),
        "price_per_sqm_eur": safe_text(SELECTORS["price_per_sqm"]),
        "link": safe_href(SELECTORS["link"]),
    }
    listing.update(parse_specs(card))
    return listing


def parse_page(html: str) -> list[dict]:
    """Parse a page's HTML into a list of listing dicts."""
    soup = BeautifulSoup(html, "lxml")
    all_cards = soup.select(SELECTORS["listing_card"])

    # Skip the hidden no-JS fallback duplicate storia.ro includes at the end
    # of the list (wrapped in a <li style="display:none">).
    visible_cards = []
    for card in all_cards:
        parent_li = card.find_parent("li")
        if parent_li and "display:none" in (parent_li.get("style") or ""):
            continue
        visible_cards.append(card)

    logger.info(f"Found {len(visible_cards)} visible listing cards on page "
                f"({len(all_cards)} total, {len(all_cards) - len(visible_cards)} hidden duplicates skipped)")
    return [parse_listing(card) for card in visible_cards]


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
