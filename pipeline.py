"""
Orchestrated pipeline: scrape storia.ro, load into Postgres, sync to BigQuery.

This wraps scraper.scraper.main(), loader.load_to_postgres.main(), and
warehouse.sync_to_bigquery.main() as Prefect tasks, run in sequence as one flow.

Note on retry scope: retries apply PER TASK, not to the whole flow. If
sync_task() fails after scrape_task() and load_task() already succeeded,
only sync_task() retries -- the scraper doesn't re-run. But if you re-run
pipeline.py itself (a brand new flow run), everything starts from scratch,
including a full re-scrape. Retries recover from a failure *within* one run;
they don't make re-running the whole script resume where it left off.

Run with: python pipeline.py
"""

from prefect import flow, task

from scraper.scraper import main as run_scraper
from loader.load_to_postgres import main as run_loader
from warehouse.sync_to_bigquery import main as run_bigquery_sync


@task(name="scrape-listings", retries=2, retry_delay_seconds=30)
def scrape_task():
    run_scraper()


@task(name="load-to-postgres", retries=2, retry_delay_seconds=30)
def load_task():
    run_loader()


@task(name="sync-to-bigquery", retries=2, retry_delay_seconds=30)
def sync_task():
    run_bigquery_sync()


@flow(name="real-estate-pipeline")
def real_estate_pipeline():
    scrape_task()
    load_task()
    sync_task()


if __name__ == "__main__":
    real_estate_pipeline()