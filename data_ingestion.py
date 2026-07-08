import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

def load_env_file(env_path: str = ".env") -> None:
    env_file = Path(env_path)
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()

# 1. Database Connection Configuration
DB_USER = os.getenv("DB_USER", "postgres") # In the dotenv file.
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "kenya_food_db")
DB_MAINTENANCE_DB = os.getenv("DB_MAINTENANCE_DB", "postgres")


def create_db_engine():
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is not set. Set DB_PASSWORD to your PostgreSQL password before running ingestion."
        )

    database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(database_url)


def ensure_database_exists() -> None:
    maintenance_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_MAINTENANCE_DB}"
    maintenance_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")

    with maintenance_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": DB_NAME},
        ).scalar()

        if exists:
            return

        safe_database_name = DB_NAME.replace('"', '""')
        try:
            connection.execute(text(f'CREATE DATABASE "{safe_database_name}"'))
            print(f"[+] Created missing database: {DB_NAME}")
        except Exception as exc:
            raise RuntimeError(
                f"Could not create database '{DB_NAME}'. Ensure the PostgreSQL user has CREATE DATABASE privileges."
            ) from exc


def ensure_schema_exists(engine, schema_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

SQL_COLUMNS = [
    "date",
    "admin1",
    "admin2",
    "market",
    "market_id",
    "latitude",
    "longitude",
    "category",
    "commodity",
    "commodity_id",
    "unit",
    "priceflag",
    "pricetype",
    "currency",
    "price",
    "usdprice",
]

def ingest_wfp_data():
    csv_path = "./data/wfp_food_prices_ken.csv"  
    ensure_database_exists()
    engine = create_db_engine()
    ensure_schema_exists(engine, "bronze")
    
    print(f"[*] Reading target file: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[!] Error: Could not find file at {csv_path}")
        return

    # 2. Load into Pandas DataFrame
    # Explicitly telling pandas how to interpret the headers
    df = pd.read_csv(csv_path)
    print(f"[+] Loaded {len(df)} rows from source.")

    # 3. Clean and Standardize
    # Remove hidden spaces from headers and make them lower-case
    df.columns = [col.lower().strip() for col in df.columns]

    missing_columns = [column for column in SQL_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {missing_columns}")

    # Keep only the columns defined in the SQL table and match that order.
    df = df[SQL_COLUMNS]
    
    # Standardize the date parsing
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Inject processing metadata timestamp
    df['ingested_at'] = datetime.now()

    # 4. Stream directly to Bronze Layer
    print("[*] Writing records to bronze.raw_food_prices...")
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE bronze.raw_food_prices RESTART IDENTITY"))

    df.to_sql(
        name='raw_food_prices',
        con=engine,
        schema='bronze',
        if_exists='append',
        index=False
    )
    print(f"[+] Ingestion complete! {len(df)} rows mapped successfully.")

if __name__ == "__main__":
    ingest_wfp_data()