import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from pipeline.clean import clean_and_transform
from pipeline.extract import extract_local_csv


def load_env_file(env_path: str = ".env") -> None:
    env_file = Path(env_path)
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "kenya_food_db")
DB_MAINTENANCE_DB = os.getenv("DB_MAINTENANCE_DB", "postgres")


def create_db_engine():
    if not DB_PASSWORD:
        raise RuntimeError("DB_PASSWORD is not set. Set DB_PASSWORD before running the pipeline.")

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
        connection.execute(text(f'CREATE DATABASE "{safe_database_name}"'))
        print(f"[+] Created missing database: {DB_NAME}")


def ensure_schema_exists(engine, schema_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))


def main():
    start_time = datetime.now()
    print("==================================================")
    print(f"Starting Kenyan Food Prices ETL Pipeline at {start_time}")
    print("==================================================")

    ensure_database_exists()
    engine = create_db_engine()
    ensure_schema_exists(engine, "silver")

    raw_data = extract_local_csv("./data/wfp_food_prices_ken.csv")
    cleaned_data = clean_and_transform(raw_data)
    cleaned_data["processed_at"] = datetime.now()

    print("[*] Loading records to silver.clean_food_prices...")
    cleaned_data.to_sql(
        name="clean_food_prices",
        con=engine,
        schema="silver",
        if_exists="replace",
        index=False,
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print("==================================================")
    print(f"[SUCCESS] Pipeline finished in {duration:.2f} seconds.")
    print("==================================================")


if __name__ == "__main__":
    main()
