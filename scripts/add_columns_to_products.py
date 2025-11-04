#!/usr/bin/env python3
"""Add two columns to data/raw/products_data.csv:

- StockLevel    : int, deterministic per ProductID/Name, category-aware range
- Discontinued  : "yes"/"no", small probability (category-aware)

Output -> data/raw/products_data_with_extra_cols.csv
"""

from __future__ import annotations

import csv
from datetime import datetime
import hashlib
from pathlib import Path
import random

# ---------- Paths (robust regardless of where you run) ----------
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "data" / "raw" / "products_data.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "products_data_with_extra_cols.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Optional stable "today" if you later want to add time-based fields
TODAY = datetime(2025, 11, 3)


# ---------- Helpers ----------
def rng_for(*keys: str) -> random.Random:
    """Deterministic RNG seeded from any mix of keys."""
    joined = "|".join(keys)
    h = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))


def category_ranges(category: str) -> tuple[int, int, float]:
    """Returns (min_stock, max_stock, discontinued_prob)
    Tweak these to fit your business rules.
    """
    c = (category or "").strip().lower()
    if c in {"electronics"}:
        return (5, 80, 0.04)
    if c in {"clothing", "apparel"}:
        return (20, 400, 0.03)
    if c in {"home", "household", "kitchen"}:
        return (10, 250, 0.05)
    if c in {"office", "office-home"}:
        return (15, 300, 0.02)
    # default
    return (10, 200, 0.05)


# ---------- Guardrail ----------
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Could not find input CSV at:\n  {INPUT_PATH}\n"
        f"Expected project layout:\n"
        f"{REPO_ROOT.name}/\n"
        f"  data/raw/products_data.csv\n"
        f"  scripts/add_columns_to_products.py"
    )

# ---------- Transform ----------
with (
    INPUT_PATH.open(newline="", encoding="utf-8") as inf,
    OUTPUT_PATH.open("w", newline="", encoding="utf-8") as outf,
):
    reader = csv.DictReader(inf)
    base_fields = list(reader.fieldnames) if reader.fieldnames else []

    # Ensure new columns once
    fieldnames = base_fields[:]
    if "StockLevel" not in fieldnames:
        fieldnames.append("StockLevel")
    if "Discontinued" not in fieldnames:
        fieldnames.append("Discontinued")

    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        pid = (row.get("ProductID") or "").strip()
        name = (row.get("ProductName") or "").strip()
        category = (row.get("Category") or "").strip()

        # Deterministic RNG per product
        r = rng_for(pid or name, category)

        # Category-aware ranges and probability
        min_s, max_s, p_disc = category_ranges(category)

        # Stock level (skew slightly higher for cheaper items if UnitPrice present)
        try:
            price = float((row.get("UnitPrice") or "").strip())
        except Exception:
            price = None

        stock = r.randint(min_s, max_s)
        if price is not None:
            # Cheaper items tend to have more units; nudge within bounds
            # (price factor is crude but deterministic)
            price_factor = max(0.6, min(1.4, 200.0 / max(1.0, price)))
            stock = int(max(min_s, min(max_s, round(stock * price_factor))))

        row["StockLevel"] = str(stock)
        row["Discontinued"] = "yes" if (r.random() < p_disc) else "no"

        writer.writerow(row)

print(f"✅ Wrote augmented CSV to: {OUTPUT_PATH}")
print(f"   Read from: {INPUT_PATH}")
