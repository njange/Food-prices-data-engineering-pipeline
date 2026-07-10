import os

import pandas as pd


def extract_local_csv(file_path: str) -> pd.DataFrame:
    """Locates and extracts raw data from a local CSV path into a DataFrame."""
    print(f"[*] Extracting data from: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source data file not found at {file_path}")

    df = pd.read_csv(file_path)
    print(f"[+] Extraction complete. Captured {len(df)} raw records.")
    return df
