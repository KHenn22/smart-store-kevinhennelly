# src/analytics_project/etl_to_dw.py
from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd
import sys

# ---------------- Paths ----------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DW_DIR = PROJECT_ROOT / "data" / "dw"
DW_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DW_DIR / "smart_sales.dw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


# ---------------- Utilities ----------------
def _read_clean(filename: str) -> pd.DataFrame:
    p = CLEAN_DIR / filename
    if not p.exists():
        raise FileNotFoundError(f"Missing expected CSV at {p}")
    return pd.read_csv(p)


def _yn_to_int(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0, "1": 1, "0": 0, "true": 1, "false": 0})
        .fillna(0)
        .astype(int)
    )


def _num(series: pd.Series, as_int=False):
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    return s.astype(int) if as_int else s


# ---------------- Normalizers ----------------
def normalize_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "CustomerID": "customer_id",
            "Name": "name",
            "Region": "region",
            "JoinDate": "join_date",
            "LastPurchaseDate": "last_purchase_date",
            "EmailOptIn": "email_opt_in",
        }
    )
    df["email_opt_in"] = _yn_to_int(df["email_opt_in"])
    return df[["customer_id", "name", "region", "join_date", "last_purchase_date", "email_opt_in"]]


def normalize_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "ProductID": "product_id",
            "ProductName": "product_name",
            "Category": "category",
            "UnitPrice": "unit_price",
            "StockLevel": "stock_level",
            "Discontinued": "discontinued",
        }
    )
    df["unit_price"] = _num(df["unit_price"])
    df["stock_level"] = _num(df["stock_level"], as_int=True)
    df["discontinued"] = _yn_to_int(df["discontinued"])
    return df[
        ["product_id", "product_name", "category", "unit_price", "stock_level", "discontinued"]
    ]


def normalize_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "TransactionID": "sale_id",
            "SaleDate": "date",
            "CustomerID": "customer_id",
            "ProductID": "product_id",
            "StoreID": "store_id",
            "CampaignID": "campaign_id",
            "SaleAmount": "sales_amount",
            "Quantity": "quantity",
            "PaymentMethod": "payment_method_id",
        }
    )
    # Parse & clean
    dt = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df = df[dt.notna()].copy()
    df["date"] = dt.dt.strftime("%Y-%m-%d")
    df["quantity"] = _num(df["quantity"], as_int=True)
    df["sales_amount"] = _num(df["sales_amount"])
    df["store_id"] = df.get("store_id", "UNKNOWN-STORE").astype(str).replace({"": "UNKNOWN-STORE"})
    df["payment_method_id"] = (
        df.get("payment_method_id", "UNKNOWN").astype(str).replace({"": "UNKNOWN"})
    )
    df["campaign_id"] = df["campaign_id"].astype(str).replace({"": None, "nan": None})
    return df


def build_dates_from_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    s = pd.to_datetime(sales_df["date"], format="%Y-%m-%d", errors="coerce").dropna()
    out = (
        pd.DataFrame(
            {
                "date": s.dt.strftime("%Y-%m-%d"),
                "year": s.dt.year,
                "quarter": s.dt.quarter,
                "month": s.dt.month,
                "day": s.dt.day,
                "is_weekend": s.dt.dayofweek.isin([5, 6]).astype(int),
            }
        )
        .drop_duplicates(subset=["date"])
        .sort_values("date")
    )
    return out


def build_dim_from_sales(sales_df, id_col, schema):
    ids = sales_df[id_col].dropna().astype(str).drop_duplicates().to_frame()
    if schema == "stores":
        ids["store_name"] = ""
        ids["region"] = ""
        ids.columns = ["store_id", "store_name", "region"]
    elif schema == "campaigns":
        ids["campaign_name"] = ""
        ids["start_date"] = ""
        ids["end_date"] = ""
        ids.columns = ["campaign_id", "campaign_name", "start_date", "end_date"]
    elif schema == "payment_methods":
        ids["method_name"] = ids[id_col]
        ids.columns = ["payment_method_id", "method_name"]
    return ids


def ensure_dim_covers_sales_keys(sales_df, dim_df, key, fill_cols):
    have = set(dim_df[key].astype(str)) if not dim_df.empty else set()
    need = set(sales_df[key].dropna().astype(str))
    missing = sorted(list(need - have))
    if not missing:
        return dim_df
    add = pd.DataFrame({key: missing})
    for c, v in fill_cols.items():
        add[c] = v if not callable(v) else add[key].map(v)
    return pd.concat([dim_df, add], ignore_index=True)


# ---------------- Schema ----------------
DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS dates (
  date TEXT PRIMARY KEY,
  year INTEGER, quarter INTEGER, month INTEGER, day INTEGER, is_weekend INTEGER);
CREATE TABLE IF NOT EXISTS customers (
  customer_id TEXT PRIMARY KEY,
  name TEXT, region TEXT, join_date TEXT, last_purchase_date TEXT, email_opt_in INTEGER);
CREATE TABLE IF NOT EXISTS products (
  product_id TEXT PRIMARY KEY,
  product_name TEXT, category TEXT, unit_price REAL, stock_level INTEGER, discontinued INTEGER);
CREATE TABLE IF NOT EXISTS stores (
  store_id TEXT PRIMARY KEY, store_name TEXT, region TEXT);
CREATE TABLE IF NOT EXISTS campaigns (
  campaign_id TEXT PRIMARY KEY, campaign_name TEXT, start_date TEXT, end_date TEXT);
CREATE TABLE IF NOT EXISTS payment_methods (
  payment_method_id TEXT PRIMARY KEY, method_name TEXT);
CREATE TABLE IF NOT EXISTS sales (
  sale_id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  store_id TEXT NOT NULL,
  campaign_id TEXT,
  payment_method_id TEXT NOT NULL,
  quantity INTEGER, sales_amount REAL,
  FOREIGN KEY (date) REFERENCES dates(date),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  FOREIGN KEY (store_id) REFERENCES stores(store_id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
  FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id));
"""


# ---------------- Main load ----------------
def load_dw():
    customers_raw = _read_clean("customers_data_clean.csv")
    products_raw = _read_clean("products_data_clean.csv")
    sales_raw = _read_clean("sales_data_clean.csv")

    customers_df = normalize_customers(customers_raw)
    products_df = normalize_products(products_raw)
    sales_df = normalize_sales(sales_raw)
    dates_df = build_dates_from_sales(sales_df)
    stores_df = build_dim_from_sales(sales_df, "store_id", "stores")
    campaigns_df = build_dim_from_sales(sales_df, "campaign_id", "campaigns")
    methods_df = build_dim_from_sales(sales_df, "payment_method_id", "payment_methods")

    # Ensure all FK values exist
    stores_df = ensure_dim_covers_sales_keys(
        sales_df, stores_df, "store_id", {"store_name": "", "region": ""}
    )
    methods_df = ensure_dim_covers_sales_keys(
        sales_df, methods_df, "payment_method_id", {"method_name": lambda x: x}
    )
    campaigns_df = ensure_dim_covers_sales_keys(
        sales_df,
        campaigns_df,
        "campaign_id",
        {"campaign_name": "", "start_date": "", "end_date": ""},
    )
    # Also ensure all customers/products exist if sales references unseen IDs
    customers_df = ensure_dim_covers_sales_keys(
        sales_df,
        customers_df,
        "customer_id",
        {"name": "", "region": "", "join_date": "", "last_purchase_date": "", "email_opt_in": 0},
    )
    products_df = ensure_dim_covers_sales_keys(
        sales_df,
        products_df,
        "product_id",
        {
            "product_name": "",
            "category": "",
            "unit_price": 0.0,
            "stock_level": 0,
            "discontinued": 0,
        },
    )

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.executescript(DDL)
        for t in [
            "sales",
            "payment_methods",
            "campaigns",
            "stores",
            "products",
            "customers",
            "dates",
        ]:
            cur.execute(f"DELETE FROM {t};")

        dates_df.to_sql("dates", conn, if_exists="append", index=False)
        customers_df.to_sql("customers", conn, if_exists="append", index=False)
        products_df.to_sql("products", conn, if_exists="append", index=False)
        stores_df.to_sql("stores", conn, if_exists="append", index=False)
        campaigns_df.to_sql("campaigns", conn, if_exists="append", index=False)
        methods_df.to_sql("payment_methods", conn, if_exists="append", index=False)
        sales_df.to_sql("sales", conn, if_exists="append", index=False)
        conn.commit()

        for t in [
            "dates",
            "customers",
            "products",
            "stores",
            "campaigns",
            "payment_methods",
            "sales",
        ]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                print(f"{t:16s} -> {cur.fetchone()[0]} rows")
            except sqlite3.OperationalError:
                pass


if __name__ == "__main__":
    print(f"Building DW at: {DB_PATH}")
    load_dw()
    print("Done.")
