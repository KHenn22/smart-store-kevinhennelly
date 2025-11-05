"""
prepare_sales_data.py
Cleans data/raw/sales_data.csv and writes data/prepared/sales_prepared.csv

Expected columns:
TransactionID, SaleDate, CustomerID, ProductID, StoreID, CampaignID, SaleAmount, Quantity, PaymentMethod
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
        logging.FileHandler(LOGS_DIR / "prepare_sales.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ------------------------- Config ------------------------
EXPECTED_COLUMNS = [
    "TransactionID",
    "SaleDate",
    "CustomerID",
    "ProductID",
    "StoreID",
    "CampaignID",
    "SaleAmount",
    "Quantity",
    "PaymentMethod",
]

PAYMENT_CANON = {
    "visa": "Visa",
    "mastercard": "Mastercard",
    "amex": "Amex",
    "americanexpress": "Amex",
    "discover": "Discover",
    "cash": "Cash",
    "applepay": "ApplePay",
    "googlepay": "GooglePay",
}


# ------------------------- Helpers -----------------------
def read_raw(file_name: str) -> pd.DataFrame:
    fp = RAW_DATA_DIR / file_name
    logger.info(f"Reading raw file: {fp}")
    df = pd.read_csv(fp)
    df.columns = df.columns.str.strip()
    return df


def normalize_payment(pm: str) -> str:
    if pd.isna(pm) or str(pm).strip() == "":
        return "Unknown"
    key = str(pm).strip().lower().replace(" ", "")
    return PAYMENT_CANON.get(key, "Unknown")


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    if "TransactionID" in df.columns:
        df = df.drop_duplicates(subset=["TransactionID"])
    else:
        df = df.drop_duplicates()
    logger.info(f"Duplicates removed: {before - len(df)}")
    return df


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # IDs as strings
    for col in ["TransactionID", "CustomerID", "ProductID", "StoreID", "CampaignID"]:
        df[col] = df[col].astype(str).str.strip()

    # Numerics
    df["SaleAmount"] = pd.to_numeric(df["SaleAmount"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

    # Dates
    df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors="coerce", infer_datetime_format=True)

    # Payment method
    df["PaymentMethod"] = df["PaymentMethod"].apply(normalize_payment)

    return df


def handle_missing_and_rules(df: pd.DataFrame) -> pd.DataFrame:
    # Drop rows missing core identifiers
    before = len(df)
    keep = (
        df["TransactionID"].str.strip().ne("")
        & df["CustomerID"].str.strip().ne("")
        & df["ProductID"].str.strip().ne("")
    )
    df = df[keep].copy()
    logger.info(f"Dropped {before - len(df)} rows missing TransactionID/CustomerID/ProductID.")

    # Require a valid date for a sale; drop if missing
    before = len(df)
    df = df[df["SaleDate"].notna()].copy()
    logger.info(f"Dropped {before - len(df)} rows with missing/invalid SaleDate.")

    # Impute SaleAmount: median (or 0 if all missing)
    if df["SaleAmount"].isna().all():
        df["SaleAmount"] = 0.0
        logger.info("All SaleAmount missing → set to 0.0")
    else:
        miss = df["SaleAmount"].isna().sum()
        if miss:
            median_val = df["SaleAmount"].median()
            df["SaleAmount"].fillna(median_val, inplace=True)
            logger.info(f"Filled {miss} missing SaleAmount with median {median_val:.2f}")

    # Quantity: missing or < 1 → 1
    q_miss = df["Quantity"].isna().sum()
    if q_miss:
        df.loc[df["Quantity"].isna(), "Quantity"] = 1
        logger.info(f"Filled {q_miss} missing Quantity with 1")
    q_bad = (df["Quantity"] < 1).sum()
    if q_bad:
        df.loc[df["Quantity"] < 1, "Quantity"] = 1
        logger.info(f"Corrected {q_bad} Quantity values < 1 to 1")

    return df


def validate_and_finalize(df: pd.DataFrame) -> pd.DataFrame:
    # Negative SaleAmount → 0
    neg = (df["SaleAmount"] < 0).sum()
    if neg:
        df.loc[df["SaleAmount"] < 0, "SaleAmount"] = 0
        logger.info(f"Corrected {neg} negative SaleAmount values to 0")

    # Round/typing
    df["SaleAmount"] = df["SaleAmount"].round(2)
    df["Quantity"] = df["Quantity"].round(0).astype(int)

    # Optional: mild IQR trimming for extreme outliers (only if enough rows)
    for col in ["SaleAmount", "Quantity"]:
        s = df[col]
        if not pd.api.types.is_numeric_dtype(s) or s.dropna().size < 11:
            continue
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        before = len(df)
        df = df[(df[col] >= lower) & (df[col] <= upper)].copy()
        removed = before - len(df)
        if removed:
            logger.info(f"Removed {removed} outliers in {col} (kept {lower:.2f}–{upper:.2f})")

    # Final column order (keep expected first; retain any extras at end)
    ordered = [c for c in EXPECTED_COLUMNS if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    return df[ordered + extras]


# ----------------------- Pipeline ------------------------
def clean_sales(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Guard: required columns present
    missing = [c for c in EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    df = df_raw.copy()
    df = remove_duplicates(df)
    df = coerce_types(df)
    df = handle_missing_and_rules(df)
    df = validate_and_finalize(df)
    return df.reset_index(drop=True)


def main() -> None:
    input_file = "sales_data.csv"
    output_file = "sales_prepared.csv"

    raw_df = read_raw(input_file)
    original_shape = raw_df.shape
    logger.info(f"Raw shape: {original_shape}")

    clean_df = clean_sales(raw_df)
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
