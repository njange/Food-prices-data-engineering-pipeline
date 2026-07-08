CREATE SCHEMA IF NOT EXISTS bronze;

DROP TABLE IF EXISTS bronze.raw_food_prices;

CREATE TABLE bronze.raw_food_prices (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    admin1 VARCHAR(100),
    admin2 VARCHAR(100),
    market VARCHAR(100),
    market_id INT,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    category VARCHAR(100),
    commodity VARCHAR(100),
    commodity_id INT,
    unit VARCHAR(50),
    priceflag VARCHAR(50),
    pricetype VARCHAR(50),
    currency VARCHAR(10),
    price NUMERIC(12, 2),    -- Local price (KES)
    usdprice NUMERIC(12, 2), -- USD normalized price
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);