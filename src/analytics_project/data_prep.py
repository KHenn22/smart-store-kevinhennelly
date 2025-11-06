"""Single-module data prep runner that cleans all three raw CSVs:
- data/raw/customers_data.csv
- data/raw/products_data.csv
- data/raw/sales_data.csv

Outputs:
- data/clean/customers_data_clean.csv
- data/clean/products_data_clean.csv
- data/clean/sales_data_clean.csv
"""

from pathlib import Path

import pandas as pd

from src.analytics_project.data_scrubber import DataScrubber

# ---------- helpers ----------


def summarize(df: pd.DataFrame) -> tuple[int, int, int]:
    rows = len(df)
    nulls = int(df.isnull().sum().sum())
    dupes = int(df.duplicated().sum())
    return rows, nulls, dupes


def print_summary(label: str, before: tuple[int, int, int], after: tuple[int, int, int]) -> None:
    br, bn, bd = before
    ar, an, ad = after
    print(f"{label}: rows {br} -> {ar}; nulls {bn} -> {an}; dupes {bd} -> {ad}")


def find_col(df: pd.DataFrame, target_lower: str) -> str | None:
    """Return the actual column name that matches case-insensitively, else None."""
    tl = target_lower.replace("_", "").strip().lower()
    for c in df.columns:
        if c.replace("_", "").strip().lower() == tl:
            return c
    return None


def replace_global_question_marks(df: pd.DataFrame) -> pd.DataFrame:
    """Replace any lone '?' values (optionally surrounded by whitespace) with NaN across the DataFrame."""
    out = df.copy()
    obj_cols = out.select_dtypes(include=["object", "string"]).columns
    if len(obj_cols) > 0:
        out[obj_cols] = out[obj_cols].apply(
            lambda s: s.astype(str).str.strip().where(s.astype(str).str.strip() != "?", other=pd.NA)
        )
    return out


# ---------- cleaners ----------


def clean_customers(base_path: Path, out_path: Path) -> None:
    in_file = base_path / "customers_data.csv"
    if not in_file.exists():
        print("customers_data.csv not found, skipping.")
        return

    df = pd.read_csv(in_file)
    before = summarize(df)

    # Replace lone '?' with NaN, then clean with DataScrubber
    df = replace_global_question_marks(df)
    ds = DataScrubber(df)

    # Normalize Region (keep simple lowercasing)
    region_col = find_col(ds.df, "region")
    if region_col:
        ds.df[region_col] = ds.df[region_col].astype(str).str.strip().str.lower()

    # Normalize EmailOptIn and default missing to 'no'
    email_col = find_col(ds.df, "emailoptin")
    if email_col:
        s = ds.df[email_col].astype(str).str.strip().str.lower()
        s = s.replace(
            {
                "": "no",
                "n": "no",
                "no": "no",
                "y": "yes",
                "yes": "yes",
                "na": "no",
                "none": "no",
                "null": "no",
                pd.NA: "no",
            }
        )
        ds.df[email_col] = s.fillna("no")

    # Parse dates; KEEP rows with missing LastPurchaseDate (set to NaT), only drop if JoinDate is missing
    join_col = find_col(ds.df, "joindate")
    last_col = find_col(ds.df, "lastpurchasedate")

    for c in [join_col, last_col]:
        if c:
            ds.df[c] = pd.to_datetime(ds.df[c], errors="coerce")  # '?' -> NaT (kept)

    # Drop only if JoinDate is missing; DO NOT drop for missing LastPurchaseDate
    if join_col:
        ds.df.dropna(subset=[join_col], inplace=True)

    # Remove exact duplicate rows
    ds.remove_duplicate_records()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.df.to_csv(out_path, index=False)

    after = summarize(ds.df)
    print_summary("customers_data", before, after)


def clean_products(base_path: Path, out_path: Path) -> None:
    in_file = base_path / "products_data.csv"
    if not in_file.exists():
        print("products_data.csv not found, skipping.")
        return

    df = pd.read_csv(in_file)
    before = summarize(df)

    df = replace_global_question_marks(df)
    ds = DataScrubber(df)

    # StockLevel -> numeric; invalid/missing -> 0
    stock_col = find_col(ds.df, "stocklevel")
    if stock_col:
        col = pd.to_numeric(ds.df[stock_col], errors="coerce").fillna(0).astype(int)
        ds.df[stock_col] = col

    # Discontinued -> yes/no; default missing to 'no'
    disc_col = find_col(ds.df, "discontinued")
    if disc_col:
        s = ds.df[disc_col].astype(str).str.strip().str.lower()
        s = s.replace(
            {
                "": "no",
                "y": "yes",
                "yes": "yes",
                "true": "yes",
                "n": "no",
                "no": "no",
                "false": "no",
                pd.NA: "no",
            }
        )
        ds.df[disc_col] = s.fillna("no")

    ds.remove_duplicate_records()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.df.to_csv(out_path, index=False)

    after = summarize(ds.df)
    print_summary("products_data", before, after)


def clean_sales(base_path: Path, out_path: Path) -> None:
    in_file = base_path / "sales_data.csv"
    if not in_file.exists():
        print("sales_data.csv not found, skipping.")
        return

    df = pd.read_csv(in_file)
    before = summarize(df)

    df = replace_global_question_marks(df)
    ds = DataScrubber(df)

    # For numeric columns: fill NaN with 0; for strings: trim whitespace
    for col in ds.df.columns:
        if pd.api.types.is_numeric_dtype(ds.df[col]):
            ds.df[col] = ds.df[col].fillna(0)
        else:
            ds.df[col] = ds.df[col].astype(str).str.strip()

    ds.remove_duplicate_records()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.df.to_csv(out_path, index=False)

    after = summarize(ds.df)
    print_summary("sales_data", before, after)


# ---------- main ----------


def main() -> int:
    print("Starting data preparation...")

    base_path = Path("data/raw")
    clean_dir = Path("data/clean")

    clean_customers(base_path, clean_dir / "customers_data_clean.csv")
    clean_products(base_path, clean_dir / "products_data_clean.csv")
    clean_sales(base_path, clean_dir / "sales_data_clean.csv")

    print("Data preparation complete. Clean files are in data/clean/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
