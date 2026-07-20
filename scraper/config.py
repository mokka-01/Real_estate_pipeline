"""
Scraper configuration.

Fill in BASE_URL and SELECTORS after you've inspected the target site's
HTML with browser dev tools (right-click a listing -> Inspect).
"""

# The search/listing page you want to scrape, e.g. apartments for sale in Bucharest.
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

# CSS selectors confirmed by inspecting the real storia.ro HTML.
SELECTORS = {
    "listing_card": "article",
    "title": "p[data-cy='listing-item-title']",
    "address": "p[data-cy='advert-card-address']",
    "price_main": "div[data-cy='listing-item-price'] span:nth-of-type(1)",
    "price_per_sqm": "div[data-cy='listing-item-price'] span:nth-of-type(2)",
    "link": "a[data-cy='listing-item-link']",
    # rooms / area / floor aren't directly selectable — all three <dd> values
    # share the same CSS class. We match them to their <dt> label text instead
    # (handled in scraper.py's parse_specs function).
    "specs_list": "dl",
}

# Romanian <dt> labels used to match each <dd> value to a field name.
SPEC_LABELS = {
    "Numărul de camere": "rooms",
    "Prețul pe metru pătrat": "area_sqm",  # storia.ro's own label is misleading here;
                                            # this dt actually precedes the AREA value (m²), not price/m2.
    "Etaj": "floor",
}

OUTPUT_CSV_PATH = "data/raw/listings.csv"
