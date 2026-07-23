"""
Scraper configuration.

Fill in BASE_URL and SELECTORS after you've inspected the target site's
HTML with browser dev tools (right-click a listing -> Inspect).
"""

# The search/listing page you want to scrape, e.g. apartments for sale in Bucharest.
BASE_URL = "https://www.storia.ro/ro/rezultate/vanzare/apartament/bucuresti"

# Fixed query params confirmed from the real site (page gets added dynamically
# per request — see build_page_url() in scraper.py).
SEARCH_PARAMS = {
    "limit": 36,
    "ownerTypeSingleSelect": "ALL",
    "by": "DEFAULT",
    "direction": "DESC",
}

# Pagination targets
TARGET_LISTINGS = 2000   # stop once we've collected at least this many
MAX_PAGES = 70           # hard safety cap so a bug can't loop forever

# Polite scraping settings
REQUEST_DELAY_SECONDS = 1.5   # minimum pause between requests
REQUEST_TIMEOUT_SECONDS = 10

# Retry/backoff settings for transient failures (network blips, momentary
# server errors). Wait times double each retry: 2s, 4s, 8s, then give up.
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# CSS selectors confirmed by inspecting the real storia.ro HTML.
SELECTORS = {
    "listing_card": "article",
    # Both regular AND promoted ("VipAdvertCard") listings wrap their title
    # in an <a> with this exact class — unlike data-cy attributes, which
    # promoted listings sometimes omit on the title/link elements.
    "title_link_anchor": "a.text-foreground-action-primary.no-underline",
    "address": "p[data-cy='advert-card-address']",
    "price_main": "div[data-cy='listing-item-price'] span:nth-of-type(1)",
    "price_per_sqm": "div[data-cy='listing-item-price'] span:nth-of-type(2)",
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
