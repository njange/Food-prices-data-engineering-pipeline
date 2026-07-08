# Phase 1: SQL Foundations & Initial Automation

This phase establishes the Bronze staging layer for Kenya food price data. The goal is to land the raw CSV into PostgreSQL, validate the structure, and perform an initial data quality review before any downstream modeling or transformation work.

## 1. Database Environment Setup

- PostgreSQL staging database: `kenya_food_db`
- Bronze schema: `bronze`
- Raw table: `bronze.raw_food_prices`

The table uses fixed-precision numeric types for price fields so financial values are stored accurately.

## 2. Initial Ingestion

The Python ingestion script uses `pandas` and `sqlalchemy` to:

- Load `data/wfp_food_prices_ken.csv`
- Align the CSV columns to the SQL table definition
- Create the database if it does not exist
- Create the `bronze` schema if it does not exist
- Insert the rows into `bronze.raw_food_prices`

## 3. Data Quality Notes

A short first-pass review of the CSV surfaced these issues:

1. 68 rows are missing geography fields. The missing values are in `admin1`, `admin2`, `latitude`, and `longitude`, which limits location-based analysis for those records.
2. Market naming is not fully standardized. Some markets are recorded as plain names like `Nairobi` or `Kisumu`, while others include county context in parentheses such as `Eldoret town (Uasin Gishu)` and `Karatina (Nyeri)`.
3. Unit labels vary across the file. Similar price observations may appear in different units such as `KG`, `90 KG`, `50 KG`, `400 G`, `500 ML`, and `L`, so unit normalization will be needed before comparing commodities directly.

## 4. Validation Queries To Run

These are the SQL checks for the bronze layer:

### Latest price for a specific market

```sql
SELECT date, market, commodity, price, currency
FROM bronze.raw_food_prices
WHERE market = 'Nairobi'
ORDER BY date DESC, commodity ASC;
```

### Price aggregation by commodity

```sql
SELECT
    commodity,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM bronze.raw_food_prices
GROUP BY commodity
ORDER BY commodity;
```

### High-density commodities

```sql
SELECT
    commodity,
    COUNT(DISTINCT market) AS market_count
FROM bronze.raw_food_prices
GROUP BY commodity
HAVING COUNT(DISTINCT market) > 10
ORDER BY market_count DESC, commodity;
```

### Temporal extraction by year and month

```sql
SELECT
    EXTRACT(YEAR FROM date) AS price_year,
    EXTRACT(MONTH FROM date) AS price_month,
    AVG(price) AS avg_price
FROM bronze.raw_food_prices
GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
ORDER BY price_year, price_month;
```

## 5. Files

- `data_ingestion.py`: CSV-to-PostgreSQL ingestion script
- `food_prices.sql`: Bronze table definition
- `data/wfp_food_prices_ken.csv`: source dataset
