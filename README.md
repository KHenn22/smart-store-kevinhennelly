# Smart Sales Starter Files

> Start a BI pipeline by reading raw data into pandas DataFrames (a two-dimensional representation similar to an Excel sheet).

---

## WORKFLOW 1. Set Up Your Machine (DONE in P1)

Proper setup is critical. Follow earlier instructions to set up your machine.

---

## WORKFLOW 2. Set Up Your Project (DONE in P1)

We used these one-time commands when first starting the project.

```bash
uv python pin 3.12
uv venv
uv sync --extra dev --extra docs --upgrade
uv run pre-commit install
uv run python --version
```

**macOS / Linux / WSL:**

```bash
source .venv/bin/activate
```

---

## WORKFLOW 3. Daily Workflow

As we progress, we'll use this daily workflow often.

### 3.1 Git Pull from GitHub

Always start with:

```bash
git pull
```

### 3.2 Run Checks as You Work

Run these one at a time to keep your environment updated and code clean.

```bash
uv sync --extra dev --extra docs --upgrade
uv cache clean
git add .
uvx ruff check --fix
uvx pre-commit autoupdate
uv run pre-commit run --all-files
git add .
uv run pytest
```

### 3.3 Build Project Documentation

```bash
uv run mkdocs build --strict
uv run mkdocs serve
```

- After running the serve command, press **CMD + click** the local URL to open docs.
- Press **CTRL C** to stop the hosting process.

---

# P2: BI Python – Reading Raw Data into pandas DataFrames

## Overview

This project demonstrates how to use Python and pandas to load raw CSV data files into DataFrames as part of a BI workflow.

### Run the Data Preparation Module

```bash
uv run python -m analytics_project.data_prep
```

This command executes the module directly from the project root.
It reads each raw CSV file found in `data/raw/`, loads it into a pandas DataFrame, and logs the file name and shape.

---

## Results Summary

| File Name            | Rows | Columns |
|----------------------|------|----------|
| customers_data.csv   | 201  | 6        |
| products_data.csv    | 100  | 4        |
| sales_data.csv       | 2001 | 8        |

---

# P3: Prepare Data for ETL

## Objective

This stage focuses on **cleaning and preparing data for Extract, Transform, and Load (ETL)** processes.
The goal is to ensure all datasets are consistent, accurate, and ready for business intelligence (BI) use.

---

## Processing Steps

We combined all data cleaning logic into a single module (`data_prep.py`) that calls functions from `data_scrubber.py`.
The process standardized and validated all three datasets.

### Summary of Cleaning Actions

- Removed unnecessary columns (`FirstName`, `LastName`, `TenureDays`).
- Replaced `?` with appropriate defaults:
  - Numeric fields → `0`
  - Text fields → empty string `""`
- Preserved rows that had missing **LastPurchaseDate** (kept `<NA>` instead of deleting).
- Standardized text columns (capitalized region names, removed whitespace).
- Removed duplicate records.
- Confirmed all files exported cleanly to `data/clean`.

---

### Input and Output Files

| Input File | Clean Output File |
|-------------|-------------------|
| `data/raw/customers_data.csv` | `data/clean/customers_data_clean.csv` |
| `data/raw/products_data.csv`  | `data/clean/products_data_clean.csv` |
| `data/raw/sales_data.csv`     | `data/clean/sales_data_clean.csv` |

---

## Commands Used During Cleaning

```bash
# activate the environment
source .venv/bin/activate

# run the ETL preparation process
uv run python -m analytics_project.data_prep
```

This:
1. Loads all raw CSV files.
2. Cleans each dataset using the `DataScrubber` class.
3. Exports cleaned versions into `data/clean/`.
4. Prints before/after summaries for rows, nulls, and duplicates.

---

## Example Terminal Output

```
customers_data: rows 201 -> 201 | nulls 4 -> 4 | dupes 1 -> 0
products_data: rows 100 -> 100 | nulls 5 -> 0 | dupes 0 -> 0
sales_data: rows 2001 -> 2000 | nulls 2 -> 0 | dupes 1 -> 0
data preparation complete. Clean files are in data/clean
```

---

## Git Commands Used

```bash
git add .
git commit -m "Clean and prepare data for ETL – replaced ?, removed dupes, preserved NA"
git push -u origin main
```

---

## Notes and Lessons Learned

- Retaining `<NA>` values is essential for accurate analytics.
- Data cleaning consumed roughly **70% of project time**, matching industry norms.
- Using reusable modules (`data_scrubber` + `data_prep`) ensures consistent future ETL steps.

---

## Final Verification

```bash
ls data/clean/
```

Expected output:

```
customers_data_clean.csv
products_data_clean.csv
sales_data_clean.csv
```

---

**Next Step:** The cleaned files in `data/clean/` are now ready to be loaded into your ETL or BI workflow for analysis.
