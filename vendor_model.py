"""Orchestration module to run ingestion and vendor summary.

This module exposes a simple `main()` that runs the CSV ingestion
defined in `data_ingestion_in_db.py` and the summary flow from
`get_vendor_summary.py`.
"""

from data_ingestion_in_db import load_raw_data
from get_vendor_summary import run_vendor_summary


def main(run_ingest=True, run_summary=True):
    if run_ingest:
        print("Running data ingestion...")
        load_raw_data()
    if run_summary:
        print("Running vendor summary...")
        run_vendor_summary()
    print("Done.")


if __name__ == "__main__":
    main()
