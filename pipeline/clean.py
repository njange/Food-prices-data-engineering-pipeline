import numpy as np
import pandas as pd


def _standardize_text(series: pd.Series) -> pd.Series:
    return series.fillna("Unknown").astype(str).str.strip().str.title()


def _calculate_kg_factor(unit_value) -> float:
    unit_str = str(unit_value).upper().strip()
    if not unit_str or unit_str == "NAN":
        return np.nan

    if "KG" in unit_str:
        num_part = "".join(character for character in unit_str if character.isdigit() or character == ".")
        return float(num_part) if num_part else 1.0

    if "MT" in unit_str:
        return 1000.0

    return np.nan


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms raw Bronze data into a cleaned, standardized Silver layer."""
    print("[*] Beginning Silver transformation process...")

    silver_df = df.copy()
    silver_df.columns = [column.lower().strip() for column in silver_df.columns]

    silver_df["date"] = pd.to_datetime(silver_df["date"], errors="coerce")
    silver_df["price"] = pd.to_numeric(silver_df["price"], errors="coerce")
    silver_df["usdprice"] = pd.to_numeric(silver_df["usdprice"], errors="coerce")

    initial_count = len(silver_df)
    silver_df = silver_df.dropna(subset=["date", "price", "commodity", "market"])
    silver_df = silver_df[silver_df["price"] > 0]

    for column in ["market", "commodity", "admin1", "admin2", "category", "unit", "priceflag", "pricetype", "currency"]:
        if column in silver_df.columns:
            silver_df[column] = _standardize_text(silver_df[column])

    silver_df["kg_factor"] = silver_df["unit"].apply(_calculate_kg_factor)
    silver_df = silver_df.dropna(subset=["kg_factor"])

    silver_df["price_per_kg"] = silver_df["price"] / silver_df["kg_factor"]
    silver_df["usd_price_per_kg"] = silver_df["usdprice"] / silver_df["kg_factor"]
    silver_df = silver_df.drop(columns=["kg_factor"])

    silver_df = silver_df.reset_index(drop=True)
    dropped_count = initial_count - len(silver_df)
    print(f"[-] Dropped {dropped_count} rows with missing, invalid, or non-convertible values.")
    print(f"[+] Silver transformation complete. Result: {len(silver_df)} highly uniform rows.")
    return silver_df
