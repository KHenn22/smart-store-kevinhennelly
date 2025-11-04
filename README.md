# Smart Sales Starter Files

> Start a processing a BI pipeline by reading raw data into pandas DataFrames (a two dimensional representation much like an Excel sheet).

---

## WORKFLOW 1. Set Up Your Machine (DONE in P1)

Proper setup is critical. Follow earlier instructions to set up your machine.

---

## WORKFLOW 2. Set Up Your Project (DONE in P1)

We used these one-time commands when first starting the project.

```shell
uv python pin 3.12
uv venv
uv sync --extra dev --extra docs --upgrade
uv run pre-commit install
uv run python --version

```

**macOS / Linux / WSL:**

```shell
source .venv/bin/activate
```

---

## WORKFLOW 3. Daily Workflow

As we progress, we'll use this daily workflow often.

### 3.1 Git Pull from GitHub

Always start with `git pull` to check for any changes made to the GitHub repo.

```shell
git pull
```

### 3.2 Run Checks as You Work

If we need additional packages, we first add them to pyproject.toml.
Add pre-commit to pyproject.toml if you haven't already.

1. Update dependencies (for security and compatibility).
2. Clean unused cached packages to free space.
3. Use `git add .` to stage all changes.
4. Run ruff and fix minor issues.
5. Update pre-commit periodically.
6. Run pre-commit quality checks on all code files (**twice if needed**, the first pass may fix things).
7. Run tests.

In VS Code, open your repository, then open a terminal (Terminal / New Terminal) and run the following commands one at a time to check the code.

```shell
uv sync --extra dev --extra docs --upgrade
uv cache clean
git add .
uvx ruff check --fix
uvx pre-commit autoupdate
uv run pre-commit run --all-files
git add .
uv run pytest
```

NOTE: The second `git add .` ensures any automatic fixes made by Ruff or pre-commit are included before testing or committing.

### 3.3 Build Project Documentation

Make sure you have current doc dependencies, then build your docs, fix any errors, and serve them locally to test.

```shell
uv run mkdocs build --strict
uv run mkdocs serve
```

- After running the serve command, the local URL of the docs will be provided. To open the site, press **CTRL and click** the provided link (at the same time) to view the documentation. On a Mac, use **CMD and click**.
- Press **CTRL c** (at the same time) to stop the hosting process.

# P2: BI Python – Reading Raw Data into pandas DataFrames

## Project Overview
This project demonstrates how to use Python and pandas to load raw CSV data files into DataFrames as part of a business intelligence workflow.
The goal is to automate data preparation so each CSV file is read, verified, and logged for its shape and structure.

During this module, I created a new source file named `data_prep.py` inside the `src/analytics_project` folder.
This script reads all CSV files in the `data/raw` directory and creates a pandas DataFrame for each file.
The results are logged to both the console and a project log file.

---

## Commands and Workflow

> ### Activate the Virtual Environment (macOS)
> To activate the virtual environment for this project, run:
>
> ```bash
> source .venv/bin/activate
> ```
>
> This ensures that all dependencies are managed locally within the project environment.

---

> ### Run the Data Preparation Module
> To execute the data preparation module and load the raw CSV files into pandas DataFrames, run:
>
> ```bash
> uv run python -m analytics_project.data_prep
> ```
>
> This command executes the module directly from the project root.
> It reads each raw CSV file found in `data/raw/`, loads it into a pandas DataFrame, and logs the file name and shape to both the console and the project log file.

---

## Output Verification

After running the command above, the terminal log confirmed that each DataFrame was created successfully:

---

## Results Summary

| File Name            | Rows | Columns |
|----------------------|------|----------|
| customers_data.csv   | 201  | 4        |
| products_data.csv    | 100  | 4        |
| sales_data.csv       | 2001 | 7        |

One DataFrame was successfully created for each raw data file.
The module executed with no remaining errors.
The log file (`project_log`) contains a full record of the run.

---

## Git Commands Used

To add, commit, and push changes to GitHub, use the following commands:

```bash
git add .
git commit -m "describe your change in quotes"
git push -u origin main

<!-- ...existing code... -->

## D3.1 Data Collectiom

Date: 2025-11-03

Summary
- Added two new customer columns: LastPurchaseDate (YYYY-MM-DD) and EmailOptIn (yes/no).
- Added a small script to generate deterministic values and update the CSV.
- Script creates a backup before writing the augmented CSV.

Files added/changed
- scripts/add_customer_columns.py — script that deterministically generates LastPurchaseDate and EmailOptIn per customer and writes the result.
- data/raw/customers_data.bak.csv — backup copy created when the script runs (keeps original).
- data/raw/customers_data.csv — overwritten by the augmented CSV (contains the two new columns).

How the script works (short)
- Uses CustomerID (or Name if CustomerID missing) to seed a SHA256-based deterministic RNG.
- Picks LastPurchaseDate between JoinDate (or 2020-01-01 if missing) and a fixed TODAY reference.
- Sets EmailOptIn to "yes" or "no" deterministically with a probability biased slightly by join year.
- Makes a backup before overwriting the CSV.

Commands I used (macOS, run in VS Code terminal with .venv activated)
```bash
# activate venv (if not active)
source .venv/bin/activate

# run the augmentation script (creates backup and updates CSV)
python scripts/add_customer_columns.py

# quick verification (view header + first 5 lines)
head -n 6 data/raw/customers_data.csv
```

Notes
- The script writes a backup at data/raw/customers_data.bak.csv before replacing customers_data.csv.
- If you want to regenerate different deterministic values, update the script's TODAY constant or change the seed logic.
- If you prefer to keep the original file and write a new file, the script can be adjusted — tell me and I'll modify it.

Git workflow to record the change
```bash
git add scripts/add_customer_columns.py data/raw/customers_data.csv
git commit -m "Add deterministic augmentation: LastPurchaseDate and EmailOptIn; backup created"
git push
```
