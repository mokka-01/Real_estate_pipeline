"""
Syncs data from PostgreSQL (Supabase) into BigQuery.

This is a full-refresh sync: every run truncates the BigQuery table and
reloads it completely from Postgres. That's a deliberate simplification —
with ~2,000 rows, a full reload is cheap and always leaves BigQuery in a
state that exactly matches Postgres, with zero risk of drift or duplicate
logic bugs. Incremental/append-only syncing is a reasonable future upgrade
once the dataset is large enough that full reloads become slow or costly.

Run with: python -m warehouse.sync_to_bigquery
"""

import logging
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_postgres_connection():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not found in .env")
    return psycopg2.connect(database_url)


def get_bigquery_client() -> bigquery.Client:
    load_dotenv()
    key_path = os.getenv("GCP_KEY_PATH")
    project_id = os.getenv("GCP_PROJECT_ID")

    if not key_path or not project_id:
        raise RuntimeError(
            "GCP_KEY_PATH and GCP_PROJECT_ID must be set in .env. "
            "GCP_KEY_PATH should point to your service account JSON file."
        )

    credentials = service_account.Credentials.from_service_account_file(key_path)
    return bigquery.Client(credentials=credentials, project=project_id)


def fetch_postgres_data(conn) -> pd.DataFrame:
    """Pull the full raw_listings table into a pandas DataFrame."""
    query = "SELECT * FROM raw_listings;"
    df = pd.read_sql(query, conn)
    return df


def sync_to_bigquery(client: bigquery.Client, df: pd.DataFrame, dataset: str):
    table_id = f"{client.project}.{dataset}.raw_listings"

    job_config = bigquery.LoadJobConfig(
        autodetect=True,                                  # infer schema from the DataFrame
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # full refresh each run
    )

    load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()  # blocks until the load finishes (or raises on failure)

    table = client.get_table(table_id)
    logger.info(f"Loaded {table.num_rows} rows into {table_id}")


def main():
    load_dotenv()
    dataset = os.getenv("BQ_DATASET", "real_estate")

    logger.info("Connecting to Postgres...")
    pg_conn = get_postgres_connection()
    try:
        logger.info("Fetching raw_listings from Postgres...")
        df = fetch_postgres_data(pg_conn)
        logger.info(f"Fetched {len(df)} rows from Postgres")
    finally:
        pg_conn.close()

    logger.info("Connecting to BigQuery...")
    bq_client = get_bigquery_client()

    logger.info(f"Syncing to BigQuery dataset '{dataset}'...")
    sync_to_bigquery(bq_client, df, dataset)


if __name__ == "__main__":
    main()
