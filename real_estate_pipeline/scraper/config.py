"""
Scraper configuration.

Fill in BASE_URL and SELECTORS after you've inspected the target site's
HTML with browser dev tools (right-click a listing -> Inspect).
"""

# The search/listing page you want to scrape, e.g. apartments for sale in Bucharest.
# Update this once you've built the actual search URL on the site.
BASE_URL = "https://www.storia.ro/ro/rezultate/vanzare/apartament/bucuresti"

# Polite scraping settings
REQUEST_DELAY_SECONDS = 1.5   # minimum pause between requests
REQUEST_TIMEOUT_SECONDS = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# CSS selectors — these are PLACEHOLDERS. Inspect the real page and replace them.
SELECTORS = {
    "listing_card": "article",        # container for a single listing
    "title": "h3",                    # listing title/headline
    "price": "[data-cy='listing-item-price']",
    "location": "[data-cy='listing-item-location']",
    "rooms": None,                    # fill in once you find the right selector
    "area_sqm": None,
    "link": "a",                      # href to the full listing page
}

OUTPUT_CSV_PATH = "data/raw/listings.csv"
