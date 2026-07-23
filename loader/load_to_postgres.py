"""
Loads scraped listings from CSV into a PostgreSQL (Supabase) database.

This is the "L" (Load) step of an ELT pipeline: we load the RAW scraped
values as-is (as TEXT), and leave cleaning/type conversion for a later
transformation step (dbt, eventually). Don't be tempted to convert prices
to numbers here — that logic belongs in the transform stage, not the loader.

Run with: python -m loader.load_to_postgres
"""

import csv
import logging
import os

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CSV_PATH = "data/raw/listings.csv"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_listings (
    id SERIAL PRIMARY KEY,
    title TEXT,
    address TEXT,
    price_eur TEXT,
    price_per_sqm TEXT,
    rooms TEXT,
    area_sqm TEXT,
    floor TEXT,
    link TEXT UNIQUE,
    scraped_at TIMESTAMP DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO raw_listings (title, address, price_eur, price_per_sqm, rooms, area_sqm, floor, link)
VALUES %s
ON CONFLICT (link) DO NOTHING
RETURNING id;
"""


def get_connection():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL not found. Make sure you have a .env file with "
            "DATABASE_URL=postgresql://... in your project root."
        )
    return psycopg2.connect(database_url)


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_listings(conn, listings: list[dict]):
    skipped_no_link = 0
    valid_rows = []

    for row in listings:
        if not row.get("link"):
            skipped_no_link += 1
            logger.warning(
                f"Skipping row with no link (incomplete scrape) — "
                f"address={row.get('address')!r}, price={row.get('price_eur')!r}"
            )
            continue

        valid_rows.append((
            row.get("title"),
            row.get("address"),
            row.get("price_eur"),
            row.get("price_per_sqm_eur"),
            row.get("rooms"),
            row.get("area_sqm"),
            row.get("floor"),
            row.get("link"),
        ))

    inserted = 0
    if valid_rows:
        with conn.cursor() as cur:
            # execute_values groups rows into batches of page_size, so a
            # 2,000-row load becomes ~4 network round-trips instead of 2,000.
            # fetch=True collects every RETURNING id across all batches,
            # which tells us exactly how many rows were genuinely inserted
            # (skipped-as-duplicate rows return no id at all).
            inserted_ids = execute_values(
                cur, INSERT_SQL, valid_rows, page_size=500, fetch=True
            )
            inserted = len(inserted_ids)

    conn.commit()
    skipped_duplicate = len(valid_rows) - inserted
    return inserted, skipped_duplicate, skipped_no_link


def main():
    logger.info(f"Reading {CSV_PATH}")
    listings = read_csv(CSV_PATH)
    logger.info(f"Found {len(listings)} rows in CSV")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        logger.info("Ensured raw_listings table exists")

        inserted, skipped_duplicate, skipped_no_link = load_listings(conn, listings)
        logger.info(
            f"Inserted {inserted} new rows, skipped {skipped_duplicate} duplicates, "
            f"skipped {skipped_no_link} incomplete rows (no link)"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()