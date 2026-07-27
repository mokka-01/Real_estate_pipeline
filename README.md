# Real Estate Data Pipeline

Portfolio project: a complete data pipeline scraping Romanian real estate
listings (storia.ro), loading them into PostgreSQL, orchestrating with
Prefect, syncing to BigQuery, transforming with dbt, and visualizing in
Metabase.

**Pipeline stages, all working end to end:**
scraper -> Postgres (Supabase) -> Prefect orchestration -> BigQuery -> dbt -> Metabase

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (never committed — already
gitignored) with:

```
DATABASE_URL=postgresql://...           # Supabase Session Pooler connection string
GCP_PROJECT_ID=your-project-id
GCP_KEY_PATH=gcp-service-account.json   # BigQuery service account key, also gitignored
BQ_DATASET=real_estate
```

## Running the pipeline

**Full pipeline, one command** (scrape -> Postgres -> BigQuery):
```bash
python pipeline.py
```

**Individual stages**, if you want to run just one:
```bash
python -m scraper.scraper              # scrape storia.ro -> data/raw/listings.csv
python -m loader.load_to_postgres      # load CSV -> Postgres raw_listings table
python -m warehouse.sync_to_bigquery   # Postgres -> BigQuery raw_listings table
```

**dbt transformation** (cleans raw scraped text into typed columns):
```bash
cd dbt
dbt run     # builds/rebuilds the stg_raw_listings view in BigQuery
dbt test    # runs data quality checks (not_null, unique on link)
```

## Viewing the dashboard (Metabase)

Metabase isn't part of the automated pipeline — it's a separate app you run
locally to explore the data and view the dashboard.

1. Metabase lives in its own folder outside this repo (e.g. `D:\work\Projects\Metabase`),
   since it creates its own local database files on first run.
2. From that folder, start it:
   ```bash
   java --add-opens java.base/java.nio=ALL-UNNAMED -jar metabase.jar
   ```
   (Requires Java 21+. If port 3000 is already in use, set a different port
   first: `$env:MB_JETTY_PORT=3001` on Windows PowerShell.)
3. Once it's running, open `http://localhost:3000` (or whichever port you set).
4. Log in with the admin account created during first-time setup.
5. The **Real Estate Pipeline** database connection (pointing at BigQuery,
   using the same `gcp-service-account.json` key) should already be
   configured from initial setup — no need to reconnect it each time, since
   Metabase remembers it locally.
6. The **"Bucharest Real Estate Overview"** dashboard has three charts:
   average price by sector, average price per m² by sector (the
   size-normalized, more accurate view), and listing count by sector
   (explains why the first two charts diverge).

## Project structure

```
scraper/      -- scrapes storia.ro, handles pagination + retry/backoff
loader/       -- loads scraped CSV into Postgres, dedupes by link
warehouse/    -- syncs Postgres data into BigQuery (full refresh each run)
dbt/          -- cleans raw scraped text into typed, tested columns
pipeline.py   -- Prefect flow orchestrating scraper -> loader -> warehouse sync
```

## Known data quirks (intentionally handled, not bugs)

- storia.ro serves two different HTML templates for regular vs. promoted
  ("VIP") listings — handled by anchoring on a shared CSS class rather than
  template-specific selectors.
- `price_eur` uses spaces as thousands separators (no decimals);
  `price_per_sqm` uses a comma as its decimal separator — genuinely
  inconsistent formatting from the same site, handled explicitly in the
  dbt model.
- `floor` is either a number or the literal word "parter" (ground floor) —
  mapped to `0` rather than left as a silent NULL.
- Some listings (outside Bucharest's numbered sectors, e.g. Ilfov county
  suburbs) have no extractable `sector` value — shows as a blank/null
  group in sector-based charts, which is correct, not a bug.

## Roadmap / possible future additions

- [x] Scraper with pagination and retry/backoff
- [x] Load into PostgreSQL with deduplication
- [x] Orchestrate with Prefect
- [x] Sync to BigQuery
- [x] Transform with dbt (staging model + data tests)
- [x] Visualize in Metabase
- [ ] Add a second ingestion pipeline against a real API (not scraping)
- [ ] Add a small streaming-pipeline demo (e.g. Wikipedia EventStreams)
- [ ] Add CI via GitHub Actions (run dbt tests automatically on push)

