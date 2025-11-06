"""prepare_products_data.py
Cleans data/raw/products_data.csv and writes data/prepared/products_prepared.csv

Expected columns:
- ProductID, ProductName, Category, UnitPrice, StockLevel, Discontinued
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

# ------------------------- Paths -------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PREPARED_DATA_DIR = DATA_DIR / "prepared"
PREPARED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------- Logging -----------------------
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "prepare_products.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ------------------------- Config ------------------------
EXPECTED_COLUMNS = [
    "ProductID",
    "ProductName",
    "Category",
    "UnitPrice",
    "StockLevel",
    "Discontinued",
]

TRUTHY = {"y", "yes", "true", "1", "t"}
FALSY = {"n", "no", "false", "0", "f", ""}


# ------------------------- Helpers -----------------------
def read_raw(file_name: str) -> pd.DataFrame:
    fp = RAW_DATA_DIR / file_name
    logger.info(f"Reading raw file: {fp}")
    df = pd.read_csv(fp)
    df.columns = df.columns.str.strip()
    return df


def normalize_discontinued(val: str) -> str:
    if pd.isna(val):
        return "no"
    v = str(val).strip().lower()
    if v in TRUTHY:
        return "yes"
    if v in FALSY:
        return "no"
    return "no"  # conservative default


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    if "ProductID" in df.columns:
        df = df.drop_duplicates(subset=["ProductID"])
    else:
        df = df.drop_duplicates()
    logger.info(f"Duplicates removed: {before - len(df)}")
    return df


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # IDs as strings (preserve leading zeros if any)
    df["ProductID"] = df["ProductID"].astype(str).str.strip()

    # Numeric coercion
    for col in ["UnitPrice", "StockLevel"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Text cleanup
    df["ProductName"] = (
        df["ProductName"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )
    df["Category"] = (
        df["Category"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )

    # Discontinued normalization
    df["Discontinued"] = df["Discontinued"].apply(normalize_discontinued)

    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    # Require ProductID & ProductName
    before = len(df)
    df = df[df["ProductID"].str.strip().ne("") & df["ProductName"].str.strip().ne("")]
    logger.info(f"Dropped {before - len(df)} rows missing ProductID/ProductName.")

    # Fill Category
    df["Category"] = df["Category"].replace({"Nan": "Uncategorized"}).fillna("Uncategorized")

    # UnitPrice: fill with median of available values (or 0 if all NA)
    if df["UnitPrice"].isna().all():
        df["UnitPrice"] = 0.0
    else:
        df["UnitPrice"].fillna(df["UnitPrice"].median(), inplace=True)

    # StockLevel: fill missing with 0
    df["StockLevel"].fillna(0, inplace=True)

    return df


def validate_and_fix(df: pd.DataFrame) -> pd.DataFrame:
    # No negatives
    neg_price = (df["UnitPrice"] < 0).sum()
    if neg_price:
        logger.warning(f"Found {neg_price} negative UnitPrice values; setting to 0.")
        df.loc[df["UnitPrice"] < 0, "UnitPrice"] = 0

    neg_stock = (df["StockLevel"] < 0).sum()
    if neg_stock:
        logger.warning(f"Found {neg_stock} negative StockLevel values; setting to 0.")
        df.loc[df["StockLevel"] < 0, "StockLevel"] = 0

    # Round price, cast stock to int
    df["UnitPrice"] = df["UnitPrice"].round(2)
    df["StockLevel"] = df["StockLevel"].round(0).astype(int)

    return df


def remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    # IQR-based trimming for UnitPrice and StockLevel (robust to skew)
    for col in ["UnitPrice", "StockLevel"]:
        if (
            col in df.columns
            and pd.api.types.is_numeric_dtype(df[col])
            and len(df[col].dropna()) > 10
        ):
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            before = len(df)
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            logger.info(
                f"Outliers removed in {col}: {before - len(df)} (kept {lower:.2f}–{upper:.2f})"
            )
    return df


def final_order(df: pd.DataFrame) -> pd.DataFrame:
    ordered = [c for c in EXPECTED_COLUMNS if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    return df[ordered + extras]


# ----------------------- Pipeline ------------------------
def clean_products(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Verify columns exist
    missing = [c for c in EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    df = df_raw.copy()
    df = remove_duplicates(df)
    df = coerce_types(df)
    df = handle_missing(df)
    df = validate_and_fix(df)
    df = remove_outliers_iqr(df)
    df = final_order(df)
    return df.reset_index(drop=True)


def main() -> None:
    input_file = "products_data.csv"
    output_file = "products_prepared.csv"

    raw_df = read_raw(input_file)
    original_shape = raw_df.shape
    logger.info(f"Raw shape: {original_shape}")

    clean_df = clean_products(raw_df)
    cleaned_shape = clean_df.shape
    logger.info(f"Cleaned shape: {cleaned_shape}")

    out_path = PREPARED_DATA_DIR / output_file
    clean_df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned data to: {out_path}")

    logger.info("Summary:")
    logger.info(f"  Records (raw)    : {original_shape[0]}")
    logger.info(f"  Records (cleaned): {cleaned_shape[0]}")
    logger.info(f"  Columns          : {list(clean_df.columns)}")


if __name__ == "__main__":
    main()
