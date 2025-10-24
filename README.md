# BI & Analytics Project — Starter

A basic, compact, professional repository for Python-based analytics projects.
This project demonstrates best-practice structure, logging, demo modules, tests, and documentation suited for quick prototyping.

## Quick links
- Project configuration: [pyproject.toml](pyproject.toml)
- Documentation config: [mkdocs.yml](mkdocs.yml) → docs: [docs/index.md](docs/index.md)
- Notebooks: [notebooks/demo_notebook.ipynb](notebooks/demo_notebook.ipynb)
- Setup guides: [SET_UP_MACHINE.md](SET_UP_MACHINE.md), [SET_UP_PROJECT.md](SET_UP_PROJECT.md)
- Project structure overview: [STRUCTURE.md](STRUCTURE.md)
- License: [LICENSE](LICENSE)

## What’s included
- Demo modules that show common analytics tasks:
  - Basics: [`analytics_project.demo_module_basics.demo_basics`](src/analytics_project/demo_module_basics.py) — [src/analytics_project/demo_module_basics.py](src/analytics_project/demo_module_basics.py)
  - Languages (i18n examples): [`analytics_project.demo_module_languages.demo_greetings`](src/analytics_project/demo_module_languages.py) — [src/analytics_project/demo_module_languages.py](src/analytics_project/demo_module_languages.py)
  - Stats: [`analytics_project.demo_module_stats.demo_stats`](src/analytics_project/demo_module_stats.py) — [src/analytics_project/demo_module_stats.py](src/analytics_project/demo_module_stats.py)
  - Visualization: [`analytics_project.demo_module_viz.demo_viz`](src/analytics_project/demo_module_viz.py) — [src/analytics_project/demo_module_viz.py](src/analytics_project/demo_module_viz.py)
- Centralized logging helper:
  - [`analytics_project.utils_logger.init_logger`](src/analytics_project/utils_logger.py), [`analytics_project.utils_logger.get_log_file_path`](src/analytics_project/utils_logger.py), [`analytics_project.utils_logger.log_example`](src/analytics_project/utils_logger.py) — [src/analytics_project/utils_logger.py](src/analytics_project/utils_logger.py)
- Package entrypoint: [`analytics_project.main.main`](src/analytics_project/main.py) — [src/analytics_project/main.py](src/analytics_project/main.py)
- Tests: [tests/test_smoke.py](tests/test_smoke.py), [tests/test_utils_logger.py](tests/test_utils_logger.py)

## Getting started (local)
1. Create and activate a virtual environment (project recommends Python 3.12). See [SET_UP_PROJECT.md](SET_UP_PROJECT.md).
2. Install dependencies (uses uv/uvx in project docs). Or with plain pip:
   - pip install -r requirements (see [pyproject.toml](pyproject.toml) for declared deps)
3. Initialize the logger and run demos:
   - Run modules directly:
     - uv run python -m analytics_project.demo_module_basics
     - uv run python -m analytics_project.demo_module_languages
     - uv run python -m analytics_project.demo_module_stats
     - uv run python -m analytics_project.demo_module_viz
   - The shared logger is configured via [`analytics_project.utils_logger.init_logger`](src/analytics_project/utils_logger.py).

## Run tests
- Run the test suite with pytest:
  - uv run pytest
- Tests exercise imports and basic behavior:
  - [tests/test_smoke.py](tests/test_smoke.py)
  - [tests/test_utils_logger.py](tests/test_utils_logger.py)

## Logging
- Centralized logging lives in [src/analytics_project/utils_logger.py](src/analytics_project/utils_logger.py). Use:
  - [`analytics_project.utils_logger.init_logger`](src/analytics_project/utils_logger.py) to configure logging
  - [`analytics_project.utils_logger.get_log_file_path`](src/analytics_project/utils_logger.py) to find the log file used by the process

## Documentation
- API docs are auto-generated via MkDocs + mkdocstrings. Configure site in [mkdocs.yml](mkdocs.yml). Source docs live in [docs/index.md](docs/index.md).

## Contributing
- Follow formatting and lint rules in [pyproject.toml](pyproject.toml).
- Pre-commit hooks are configured in [.pre-commit-config.yaml](.pre-commit-config.yaml).
- Run ruff/pytest before pushing. CI is defined in [.github/workflows/ci.yml](.github/workflows/ci.yml) and docs deploy in [.github/workflows/deploy-docs.yml](.github/workflows/deploy-docs.yml).

## Project layout (high level)
- src/analytics_project/ — package code (see [src/analytics_project/__init__.py](src/analytics_project/__init__.py))
- tests/ — pytest-based tests ([tests/test_smoke.py](tests/test_smoke.py), [tests/test_utils_logger.py](tests/test_utils_logger.py))
- notebooks/ — demonstration notebooks ([notebooks/demo_notebook.ipynb](notebooks/demo_notebook.ipynb))
- docs/ — site content ([docs/index.md](docs/index.md))



