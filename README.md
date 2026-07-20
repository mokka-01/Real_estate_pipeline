# Real Estate Data Pipeline — Scraper Stage

Portfolio project: scraping Romanian real estate listings as the ingestion
layer of a full data pipeline (scraper -> Postgres -> BigQuery -> dbt -> Metabase).

This repo currently covers **stage 1: the scraper only.**

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Before you run anything

1. Open the target site's `robots.txt` (e.g. `https://www.storia.ro/robots.txt`)
   and read its Terms of Service. Confirm listing pages aren't disallowed.
2. Open a real search results page in your browser, right-click a listing,
   choose "Inspect", and find the actual CSS selectors/classes for:
   title, price, location, rooms, area, and the link to the full listing.
3. Update `scraper/config.py` with the real `BASE_URL` and `SELECTORS`.
   The values currently in there are placeholders/guesses and will likely
   need correcting.

## Run

```bash
python -m scraper.scraper
```

This fetches one page, parses listing cards, and writes results to
`data/raw/listings.csv`.

## Roadmap

- [ ] Get single-page scraping working with correct selectors
- [ ] Add pagination to loop through multiple result pages
- [ ] Add retry/backoff logic for failed requests
- [ ] Load CSV output into PostgreSQL
- [ ] Orchestrate with Prefect or Dagster
- [ ] Sync to BigQuery
- [ ] Transform with dbt
- [ ] Visualize in Metabase
