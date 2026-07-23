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
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from scraper.config import (
    BASE_URL,
    HEADERS,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    SELECTORS,
    SPEC_LABELS,
    SEARCH_PARAMS,
    TARGET_LISTINGS,
    MAX_PAGES,
    MAX_RETRIES,
    BACKOFF_BASE_SECONDS,
    OUTPUT_CSV_PATH,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_page_url(page: int) -> str:
    """Build the full search URL for a given page number."""
    params = {**SEARCH_PARAMS, "page": page}
    return f"{BASE_URL}?{urlencode(params)}"


def fetch_page(url: str) -> str | None:
    """
    Fetch a single page and return its HTML, or None if every attempt fails.

    Retries with exponential backoff: on failure, wait BACKOFF_BASE_SECONDS,
    then double the wait each subsequent attempt (2s, 4s, 8s...). This gives
    transient issues (a dropped connection, a momentarily overloaded server)
    a real chance to resolve, instead of killing the whole scrape on one blip.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {e}")
                return None
            wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                f"Attempt {attempt}/{MAX_RETRIES} failed for {url} ({e}); "
                f"retrying in {wait}s"
            )
            time.sleep(wait)


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

    # Title and link both live inside the same anchor tag, but the exact
    # attributes on that anchor differ between regular and promoted listing
    # templates. Selecting the anchor itself (by its stable CSS class) and
    # pulling both pieces from it works for both card types.
    anchor = card.select_one(SELECTORS["title_link_anchor"])
    link = anchor.get("href") if anchor else None
    title_el = anchor.find("p") if anchor else None
    title = title_el.get_text(strip=True) if title_el else None

    listing = {
        "title": title,
        "address": safe_text(SELECTORS["address"]),
        "price_eur": safe_text(SELECTORS["price_main"]),
        "price_per_sqm_eur": safe_text(SELECTORS["price_per_sqm"]),
        "link": link,
    }
    listing.update(parse_specs(card))
    return listing


def parse_page(html: str, page_number: int = 1) -> list[dict]:
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

    listings = []
    debug_dir = Path("data/debug_incomplete_cards")
    for i, card in enumerate(visible_cards):
        listing = parse_listing(card)

        # A listing with no title or no link is unusable data (can't dedupe,
        # can't trace back to the source) — flag it loudly instead of letting
        # it slip through as a silently incomplete row.
        if not listing.get("title") or not listing.get("link"):
            logger.warning(
                f"Incomplete listing (missing title and/or link) — "
                f"address={listing.get('address')!r}, price={listing.get('price_eur')!r}"
            )
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"page{page_number}_card_{i}.html"
            debug_path.write_text(str(card), encoding="utf-8")
            logger.warning(f"Saved raw HTML of this card to {debug_path} for inspection")

        listings.append(listing)

    return listings


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
    all_listings = []
    page = 1

    while len(all_listings) < TARGET_LISTINGS and page <= MAX_PAGES:
        url = build_page_url(page)
        logger.info(f"Fetching page {page}: {url}")
        html = fetch_page(url)

        if html is None:
            logger.error(f"No HTML returned for page {page}, stopping.")
            break

        page_listings = parse_page(html, page_number=page)

        if not page_listings:
            logger.info(f"Page {page} returned no listings — reached the end of results.")
            break

        all_listings.extend(page_listings)
        logger.info(
            f"Page {page}: got {len(page_listings)} listings "
            f"(total so far: {len(all_listings)}/{TARGET_LISTINGS})"
        )

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    if page > MAX_PAGES:
        logger.warning(f"Hit MAX_PAGES safety cap ({MAX_PAGES}) before reaching target.")

    logger.info(f"Finished: collected {len(all_listings)} listings across {page - 1} pages")
    save_to_csv(all_listings, OUTPUT_CSV_PATH)


if __name__ == "__main__":
    main()
