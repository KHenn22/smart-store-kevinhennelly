"""
prepare_customers_data.py
Reads customers_data.csv from data/raw/, cleans it, and writes customers_prepared.csv to data/prepared/.
No extra columns (FirstName, LastName, TenureDays) are added.
"""

from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

# ------------------------------------------------------------------------------
# Paths (this file is at <project_root>/src/data_preparation/prepare_customers_data.py)
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PREPARED_DATA_DIR = DATA_DIR / "prepared"
PREPARED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "prepare_customers.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Config / Helpers
# ------------------------------------------------------------------------------
EXPECTED_COLUMNS = [
    "CustomerID",
    "Name",
    "Region",
    "JoinDate",
    "LastPurchaseDate",
    "EmailOptIn",
]

REGION_MAP = {
    "north": "North",
    "south": "South",
    "east": "East",
    "west": "West",
    "central": "Central",
    "northeast": "North-East",
    "north-east": "North-East",
    "southwest": "South-West",
    "south-west": "South-West",
}

TRUTHY = {"y", "yes", "true", "1", "t"}
FALSY = {"n", "no", "false", "0", "f", ""}


def read_raw_csv(file_name: str) -> pd.DataFrame:
    fp = RAW_DATA_DIR / file_name
    logger.info(f"Reading raw file: {fp}")
    df = pd.read_csv(fp, dtype=str)  # read as strings first; we’ll coerce later
    df.columns = df.columns.str.strip()
    return df


def coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("JoinDate", "LastPurchaseDate"):
        if col in df.columns:
            before_nulls = df[col].isna().sum()
            df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
            after_nulls = df[col].isna().sum()
            if after_nulls > before_nulls:
                logger.info(
                    f"{col}: {after_nulls} nulls after parsing (invalid strings set to NaT)."
                )
    return df


def normalize_region(val: str) -> str:
    if pd.isna(val):
        return "Unknown"
    key = str(val).strip().lower().replace(" ", "").replace("_", "")
    return REGION_MAP.get(key, str(val).strip().title())


def normalize_email_opt_in(val: str) -> str:
    if pd.isna(val):
        return "no"
    v = str(val).strip().lower()
    if v in TRUTHY:
        return "yes"
    if v in FALSY:
        return "no"
    return "no"


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    if "CustomerID" not in df.columns:
        return df
    logger.info("Deduplicating by CustomerID (keeping latest LastPurchaseDate).")
    # Ensure date parsed for sorting
    if "LastPurchaseDate" in df.columns and not pd.api.types.is_datetime64_any_dtype(
        df["LastPurchaseDate"]
    ):
        df["LastPurchaseDate"] = pd.to_datetime(df["LastPurchaseDate"], errors="coerce")
    sorted_df = df.sort_values(by=["CustomerID", "LastPurchaseDate"], ascending=[True, False])
    before = len(sorted_df)
    deduped = sorted_df.drop_duplicates(subset=["CustomerID"], keep="first")
    logger.info(f"Duplicates removed: {before - len(deduped)}")
    return deduped


def handle_missing_and_rules(df: pd.DataFrame) -> pd.DataFrame:
    # Drop rows with missing required IDs/Name/JoinDate
    before = len(df)
    required_mask = (
        df["CustomerID"].astype(str).str.strip().ne("")
        & df["Name"].astype(str).str.strip().ne("")
        & df["JoinDate"].notna()
    )
    df = df[required_mask]
    logger.info(f"Dropped {before - len(df)} rows missing CustomerID/Name/JoinDate.")

    # Region + EmailOptIn normalization
    df["Region"] = df["Region"].apply(normalize_region)
    df["EmailOptIn"] = df["EmailOptIn"].apply(normalize_email_opt_in)

    # If LastPurchaseDate missing, set to JoinDate
    if "LastPurchaseDate" in df.columns:
        missing_lpd = df["LastPurchaseDate"].isna().sum()
        if missing_lpd:
            logger.info(f"Filling {missing_lpd} missing LastPurchaseDate with JoinDate.")
            df.loc[df["LastPurchaseDate"].isna(), "LastPurchaseDate"] = df.loc[
                df["LastPurchaseDate"].isna(), "JoinDate"
            ]

        # If LastPurchaseDate < JoinDate, swap
        bad_order = (df["LastPurchaseDate"] < df["JoinDate"]).sum()
        if bad_order:
            logger.info(f"Found {bad_order} rows where LastPurchaseDate < JoinDate; swapping.")
            mask = df["LastPurchaseDate"] < df["JoinDate"]
            tmp = df.loc[mask, "JoinDate"].copy()
            df.loc[mask, "JoinDate"] = df.loc[mask, "LastPurchaseDate"]
            df.loc[mask, "LastPurchaseDate"] = tmp

    # Trim Name (keep original casing/value otherwise)
    df["Name"] = df["Name"].astype(str).str.strip().replace(r"\s+", " ", regex=True)

    return df


def final_order(df: pd.DataFrame) -> pd.DataFrame:
    """Return only the expected columns, in order; keep any unexpected columns after."""
    ordered = [c for c in EXPECTED_COLUMNS if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    return df[ordered + extras]


def clean_customers(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Verify expected columns exist
    missing = [c for c in EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Coerce types
    df = df_raw.copy()
    df["CustomerID"] = df["CustomerID"].astype(str).str.strip()

    # Dates
    df = coerce_dates(df)

    # Dedup, missing handling, rules
    df = remove_duplicates(df)
    df = handle_missing_and_rules(df)

    # Final order (no extra columns added)
    df = final_order(df)

    return df.reset_index(drop=True)


def main() -> None:
    input_file = "customers_data.csv"
    output_file = "customers_prepared.csv"

    # Read
    raw_df = read_raw_csv(input_file)
    original_shape = raw_df.shape
    logger.info(f"Raw shape: {original_shape}")

    # Clean
    clean_df = clean_customers(raw_df)
    cleaned_shape = clean_df.shape
    logger.info(f"Cleaned shape: {cleaned_shape}")

    # Save
    out_path = PREPARED_DATA_DIR / output_file
    clean_df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned data to: {out_path}")

    # Summary
    logger.info("Summary:")
    logger.info(f"  Records (raw)    : {original_shape[0]}")
    logger.info(f"  Records (cleaned): {cleaned_shape[0]}")
    logger.info(f"  Columns          : {list(clean_df.columns)}")


if __name__ == "__main__":
    main()
