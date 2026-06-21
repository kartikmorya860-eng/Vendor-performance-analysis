# Use this script to save csv files into database with their filename as tablename
import pandas as pd
import os
from pathlib import Path
from sqlalchemy import create_engine
import logging
import time

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

engine = create_engine('sqlite:///inventory.db')

def ingest_db(df, table_name, engine):
    '''this function will ingest the dataframe into database table'''
    df.to_sql(table_name, con = engine, if_exists = 'replace', index = False)
    
def load_raw_data():
    '''this function will load the CSVs as dataframe and ingest into db'''
    data_dir = Path('data')
    # fallback for archives that contain files under __MACOSX/data
    if not data_dir.exists():
        alt = Path('__MACOSX') / 'data'
        if alt.exists():
            logging.info('Using alternate data directory: %s', alt)
            data_dir = alt
        else:
            logging.error('Data directory not found: %s', data_dir)
            return

    start = time.time()
    for file in sorted(data_dir.iterdir()):
        if file.suffix.lower() == '.csv':
            try:
                df = pd.read_csv(file)
                logging.info(f'Ingesting {file.name} in db')
                ingest_db(df, file.stem, engine)
            except Exception as exc:
                logging.exception('Failed to ingest %s: %s', file.name, exc)
    end = time.time()
    total_time = (end - start) / 60
    logging.info('--------------Ingestion Complete------------')
    logging.info(f'\nTotal Time Taken: {total_time:.2f} minutes')

if __name__ == '__main__':
    load_raw_data()
