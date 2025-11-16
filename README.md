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

## P4: Create and Populate DW

> Build a SQLite Data Warehouse (DW) using the cleaned datasets, and validate the structure for analytics use.

---

### WORKFLOW 1. Overview

This stage creates a **SQLite Data Warehouse (DW)** using the cleaned CSVs from `data/clean/`.
The goal is to load, structure, and verify data for use in business intelligence analysis.

---

### WORKFLOW 2. Objective

- Connect to or create a SQLite database file (`smart_sales.dw`)
- Load all cleaned CSVs from `data/clean/`
- Create and populate dimension and fact tables
- Verify table structures and record counts

---

### WORKFLOW 3. Run the ETL Script

Activate the virtual environment and run the ETL script:

    source .venv/bin/activate
    python src/analytics_project/etl_to_dw.py

This script connects to the data warehouse and performs the following:

1. Loads all cleaned CSVs
2. Creates seven tables:
   - `dates`
   - `customers`
   - `products`
   - `stores`
   - `campaigns`
   - `payment_methods`
   - `sales`
3. Inserts all records and commits to the database

---

### WORKFLOW 4. Example Terminal Output

    Building DW at: data/dw/smart_sales.dw
    dates             -> 281 rows
    customers         -> 201 rows
    products          -> 100 rows
    stores            -> 4 rows
    campaigns         -> 4 rows
    payment_methods   -> 9 rows
    sales             -> 1999 rows
    Done.

---

### WORKFLOW 5. Validate the Data Warehouse (Task 3)

Use the **SQLite Viewer** extension in VS Code to confirm successful table creation and data population.

#### Steps

1. Install the **SQLite** extension by *alexcvzz*
2. Right-click `data/dw/smart_sales.dw` → **Open Database**
3. Review all tables and confirm record counts
4. Open each table to verify that data populated correctly

---

### WORKFLOW 6. Results Summary

| Table | Rows | Status |
|---|---:|:--:|
| dates | 281 | ✅ |
| customers | 201 | ✅ |
| products | 100 | ✅ |
| stores | 4 | ✅ |
| campaigns | 4 | ✅ |
| payment_methods | 9 | ✅ |
| sales | 1999 | ✅ |

---

### WORKFLOW 7. Notes and Lessons Learned

- Empty quotes (`""`) in some columns (e.g., campaigns) represent null or missing values — this is acceptable.
- The `.dw` file extension stands for **Data Warehouse** and functions the same as `.db`.
- The `etl_to_dw.py` script enforces **foreign key integrity** for accurate relational linking.
- The **SQLite Viewer** extension is a simple, effective tool to verify schema structure and data accuracy.

---

### WORKFLOW 8. Git Commands Used

    git add .
    git commit -m "Created and populated smart_sales.dw data warehouse with cleaned data"
    git push

---

### WORKFLOW 9. Final Verification

The Data Warehouse was successfully created and validated.
All tables were populated correctly, relationships verified, and record counts confirmed.

### WORKFLOW 10. Screenshots

![campaigns](image-1.png)
![customers](image-2.png)
![dates](image-3.png)
![payment method](image-4.png)
![products](image-5.png)
![sales](image-6.png)
![stores](image-7.png)

**Next Step:** Proceed to document final BI analysis and visualization using the populated `smart_sales.dw` database.

<!-- ...existing code... -->

## Platform & tool choices (why these on my machine)

- OS: macOS Seqouia 15.6.1. I use the integrated Terminal and Finder shortcuts below.
- Editor: Visual Studio Code — lightweight, great notebook support and Python/Spark debugging.
- Python: 3.12 (managed via project tooling shown in this repo).
- Spark: pyspark + local SparkSession with SQLite JDBC (sqlite_jdbc-3.51.0.0.jar) — lets me query the DW (smart_sales.dw) using familiar SQL semantics at scale.
- Data storage: local SQLite DW for easy reproducible demos.
- Vizuals: Pandas + Seaborn / Matplotlib for quick charts inside notebooks.
- Optional BI: Power BI Desktop (Windows) or Power BI service — useful for model view and interactive reports; Spark outputs can also be exported for Power BI ingestion.

Quick macOS screenshot tips

## SQL queries & reports (what each cell does)

- Top customers
  - Query: GROUP BY customer name, SUM(SaleAmount) ORDER BY total DESC.
  - Purpose: identify high-value customers for targeting / cohort analysis.

- Sales by region
  - Query: GROUP BY customers.Region, SUM(SaleAmount).
  - Purpose: geographic performance and where to allocate spend.

- Region × Product Category (dice)
  - Query: GROUP BY customers.Region, products.Category, SUM(SaleAmount) ORDER BY region, total_sales DESC.
  - Purpose: two-dimensional view (region vs category) to spot strengths and opportunities.

- Slice operation
  - Operation: filter the dice result for a single product_category (example: Electronics).
  - Purpose: a focused regional comparison for that category.

- Drilldown operation
  - Operation: aggregate at region level and optionally break down by product (or customer) to examine drivers of region totals.
  - Purpose: move from summary to detail to troubleshoot or explain changes.

Example SQL snippets (as used in the notebook)
- Top customers:
  SELECT c.Name AS name, SUM(s.SaleAmount) AS total_spent
  FROM sales s JOIN customers c
    ON CAST(s.CustomerID AS STRING) = CAST(c.CustomerID AS STRING)
  GROUP BY c.Name
  ORDER BY total_spent DESC;

- Region × Category (dice):
  SELECT c.Region AS region, p.Category AS product_category, SUM(s.SaleAmount) AS total_sales
  FROM sales s
  JOIN customers c ON CAST(s.CustomerID AS STRING) = CAST(c.CustomerID AS STRING)
  JOIN products p ON s.ProductID = p.ProductID
  GROUP BY c.Region, p.Category
  ORDER BY c.Region, total_sales DESC;

## Screenshots

1. Slice result (filtered category)
   ![alt text](image-8.png)

2. Dice result (region × category)
   ![alt text](image-9.png)

3. Drilldown result (sales trend by region)
   ![alt text](image-10.png)





