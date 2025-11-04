#!/usr/bin/env python3
"""Add two columns to data/raw/sales_data.csv:

- Quantity      : int in [1..5], skewed toward 1–3
- PaymentMethod : categorical (Visa, Mastercard, Amex, Discover, PayPal, ApplePay, GooglePay, Cash)

Output -> data/raw/sales_data_with_extra_cols.csv
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import random

# ---------- Paths (robust regardless of where you run) ----------
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "data" / "raw" / "sales_data.csv"
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "sales_data_with_extra_cols.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------- Helpers ----------
def rng_for(*keys: str) -> random.Random:
    """Deterministic RNG seeded from any mix of keys."""
    s = "|".join(keys)
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))


PAYMENT_METHODS = [
    "Visa",
    "Mastercard",
    "Amex",
    "Discover",
    "PayPal",
    "ApplePay",
    "GooglePay",
    "Cash",
]


def draw_quantity(r: random.Random) -> int:
    """Skew toward smaller basket sizes."""
    # Weighted: 1(35%), 2(30%), 3(20%), 4(10%), 5(5%)
    x = r.random()
    if x < 0.35:
        return 1
    if x < 0.65:
        return 2
    if x < 0.85:
        return 3
    if x < 0.95:
        return 4
    return 5


def draw_payment_method(r: random.Random) -> str:
    # Light bias toward card wallets / major cards
    weights = [0.24, 0.24, 0.10, 0.08, 0.10, 0.10, 0.09, 0.05]
    t = r.random()
    acc = 0.0
    for method, w in zip(PAYMENT_METHODS, weights):
        acc += w
        if t <= acc:
            return method
    return PAYMENT_METHODS[-1]


# ---------- Guardrail ----------
if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Could not find input CSV at:\n  {INPUT_PATH}\n"
        f"Expected layout:\n{REPO_ROOT.name}/data/raw/sales_data.csv"
    )

# ---------- Transform ----------
with (
    INPUT_PATH.open(newline="", encoding="utf-8") as inf,
    OUTPUT_PATH.open("w", newline="", encoding="utf-8") as outf,
):
    reader = csv.DictReader(inf)
    base_fields = list(reader.fieldnames) if reader.fieldnames else []

    fieldnames = base_fields[:]
    if "Quantity" not in fieldnames:
        fieldnames.append("Quantity")
    if "PaymentMethod" not in fieldnames:
        fieldnames.append("PaymentMethod")

    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        tx_id = (row.get("TransactionID") or "").strip()
        cust = (row.get("CustomerID") or "").strip()

        r = rng_for(tx_id or cust)

        row["Quantity"] = str(draw_quantity(r))
        row["PaymentMethod"] = draw_payment_method(r)

        writer.writerow(row)

print(f"✅ Wrote augmented CSV to: {OUTPUT_PATH}")
print(f"   Read from: {INPUT_PATH}")
