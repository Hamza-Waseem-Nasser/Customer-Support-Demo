"""
Database setup and data initialization
"""
import os
import shutil
import sqlite3
import pandas as pd
import requests
from datetime import datetime
import pytz


def setup_sample_database():
    """Set up the sample database with travel data"""
    db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
    local_file = "travel2.sqlite"
    backup_file = "travel2.backup.sqlite"
    
    # Download the database if it doesn't exist
    if not os.path.exists(local_file):
        print("Downloading sample database...")
        response = requests.get(db_url)
        response.raise_for_status()
        with open(local_file, "wb") as f:
            f.write(response.content)
        shutil.copy(local_file, backup_file)
        print("Sample database downloaded successfully!")
    
    return update_dates(local_file)


def update_dates(file):
    """Update the dates in the database to current time"""
    shutil.copy("travel2.backup.sqlite", file)
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).name.tolist()
    tdf = {}
    for t in tables:
        tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

    example_time = pd.to_datetime(
        tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
    ).max()
    current_time = pd.to_datetime("now").tz_localize(example_time.tz)
    time_diff = current_time - example_time

    tdf["bookings"]["book_date"] = (
        pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
        + time_diff
    )

    datetime_columns = [
        "scheduled_departure",
        "scheduled_arrival", 
        "actual_departure",
        "actual_arrival",
    ]
    for column in datetime_columns:
        tdf["flights"][column] = (
            pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
        )

    for table_name, df in tdf.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    del df
    del tdf
    conn.commit()
    conn.close()

    return file


def get_company_policies():
    """Download company policies for the retriever"""
    response = requests.get(
        "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md"
    )
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    # Initialize database when run directly
    db_file = setup_sample_database()
    print(f"Database ready: {db_file}")
