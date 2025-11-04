#!/usr/bin/env python3
"""Add two useful columns to data/raw/customers_data.csv:

- LastPurchaseDate : a deterministic date between join date (or 2020-01-01) and TODAY
- EmailOptIn       : "yes"/"no" with a probability that varies by join year

Output is written to:
data/raw/customers_data_with_extra_cols.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import random

# ---------- Paths (robust regardless of where you run the script) ----------
# This file lives at <repo_root>/scripts/add_columns_to_customers.py
REPO_ROOT = Path(__file__).resolve().parent.parent  # go up from /scripts to repo root

INPUT_PATH = REPO_ROOT / "data" / "raw" / "customers_data.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "customers_data_with_extra_cols.csv"

# Create the output directory if needed
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------- Controls ----------
# Freeze "today" for reproducibility (set this to datetime.today() to use real now)
TODAY = datetime(2025, 11, 3)


# ---------- Helpers ----------
def deterministic_rng(key: str) -> random.Random:
    """Create a deterministic RNG seeded from an arbitrary string key."""
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)


def parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):  # a few common formats
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def format_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


# ---------- Guardrails ----------
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Could not find input CSV at:\n  {INPUT_PATH}\n"
        f"Tip: Your project should look like:\n"
        f"{REPO_ROOT.name}/\n"
        f"  data/raw/customers_data.csv\n"
        f"  scripts/add_columns_to_customers.py"
    )

# ---------- Main transform ----------
with (
    INPUT_PATH.open(newline="", encoding="utf-8") as inf,
    OUTPUT_PATH.open("w", newline="", encoding="utf-8") as outf,
):
    reader = csv.DictReader(inf)
    base_fieldnames = list(reader.fieldnames) if reader.fieldnames else []

    # Ensure new columns exist (and don’t duplicate if already present)
    fieldnames = base_fieldnames[:]
    if "LastPurchaseDate" not in fieldnames:
        fieldnames.append("LastPurchaseDate")
    if "EmailOptIn" not in fieldnames:
        fieldnames.append("EmailOptIn")

    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        cust_id = (row.get("CustomerID") or "").strip()
        join_date = parse_date(row.get("JoinDate"))
        rng = deterministic_rng(cust_id or row.get("Name", ""))

        # ---- LastPurchaseDate ----
        # Start from join_date (if present) else a floor date; clamp so it's not after TODAY.
        start = join_date or datetime(2020, 1, 1)
        if start > TODAY:
            start = TODAY

        # Ensure at least a 1-day window
        days_range = max(1, (TODAY - start).days)
        last_purchase = start + timedelta(days=rng.randint(0, days_range))
        row["LastPurchaseDate"] = format_date(last_purchase)

        # ---- EmailOptIn ----
        # Base probability ~45%, slightly higher for recent join years
        join_year = join_date.year if join_date else 2021
        base_prob = 0.45 + min(0.25, max(0.0, (2025 - join_year) * 0.02))
        prob_value = rng.random()
        row["EmailOptIn"] = "yes" if prob_value < base_prob else "no"

        writer.writerow(row)

print(f"✅ Wrote augmented CSV to: {OUTPUT_PATH}")
print(f"   Read from: {INPUT_PATH}")
