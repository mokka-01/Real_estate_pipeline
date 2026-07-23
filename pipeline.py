"""
Orchestrated pipeline: scrape storia.ro, then load results into Postgres.

This wraps the existing scraper.scraper.main() and loader.load_to_postgres.main()
functions as Prefect tasks, and runs them in sequence as a single flow.

Note on retry granularity: each task retries the ENTIRE function it wraps.
If scrape_task() fails on page 40 of 57, a retry re-scrapes from page 1 again
-- it doesn't resume from where it left off. That's a real, known tradeoff of
wrapping whole scripts as single tasks (rather than breaking "fetch page N"
into its own task), worth knowing rather than assuming retries are "free."

Run with: python pipeline.py
"""

from prefect import flow, task

from scraper.scraper import main as run_scraper
from loader.load_to_postgres import main as run_loader


@task(name="scrape-listings", retries=2, retry_delay_seconds=30)
def scrape_task():
    run_scraper()


@task(name="load-to-postgres", retries=2, retry_delay_seconds=30)
def load_task():
    run_loader()


@flow(name="real-estate-pipeline")
def real_estate_pipeline():
    scrape_task()
    load_task()


if __name__ == "__main__":
    real_estate_pipeline()
