# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python data analysis project for analyzing the "Sci-Fi Boekenclub" (Sci-Fi Book Club) reading data. The project combines Goodreads export data from multiple club members with book club meeting records to analyze reading preferences and ratings over time.

## Architecture

The project is a Streamlit web app (`app.py`) backed by a pure Python package (`src/scifi/`) and Jupyter notebooks for one-off analysis.

### Module layout
- `app.py`: Streamlit entrypoint; calls `scifi.ui` pages
- `src/scifi/`:
  - `paths.py`: Paths to data files and utilities to detect data changes
  - `members.py`: Member registry mapping export file names to names
  - `utils.py`: CSV readers and data joining
  - `data_processor.py`: The pipeline that combines and cleans data
  - `analysis.py`: Pure computations on Polars DataFrames
  - `visualizer.py`: Plotly figure builders
  - `ui/`: Streamlit pages (one `render()` function per module)
- `notebooks/`:
  - `cleaning.ipynb`: Clean and standardize Goodreads CSV exports
  - `aggregating.ipynb`: Combine data sources and create aggregated datasets
  - `eda.ipynb`: Exploratory analysis and visualization

### Data sources
- Goodreads CSV exports from individual members (in `data/goodreads/clean/`)
- Book club meeting records (`data/bookclub/bookclub.csv`)
- Manual ratings (`data/bookclub/manual_ratings.csv`)
- Authors, one row per author (`data/bookclub/authors.csv`)

### Import rules
1. **Imports point down:** `app.py` → `scifi.ui.*` → `analysis`, `visualizer`, `data_processor` → `utils`, `members`, `paths`. Nothing in `scifi` imports `app.py`.
2. **Only `scifi.ui` imports streamlit.** Everything else runs and is tested without a Streamlit runtime.
3. **Use absolute imports only,** for example `from scifi.analysis import rank_books`.
4. **Only `paths.py` contains `"data/..."` strings.**
5. **Use Polars everywhere.** No pandas in `src/` or `app.py`.

## Development Commands

Use the Makefile:

- `make setup`: `uv sync` and install the git hooks (prek)
- `make lint`: ruff format check, ruff, ty and pydoclint
- `make test`: pytest with coverage
- `make dashboard`: run the Streamlit app from `app.py`
- `make clean`: remove caches and build artifacts; keeps `uv.lock` and the virtual environment

`uv sync` installs the dependencies (groups `dev` and `notebooks`) and the package itself.

## Testing and Quality

- Tests are in `tests/` and use pytest. `tests/data_test.py` holds the data contracts and runs on the real CSVs.
- Code quality: ruff (lint and format), ty (types) and pydoclint (numpy docstrings). `make lint` runs them, CI runs the same checks plus the tests with coverage and a package build check, and the git hooks in `.pre-commit-config.yaml` (installed by `make setup` via prek) run them on commit.

## Data Processing Notes

The core data processing uses Polars for performance. Key functions in `src/scifi/utils.py`:

- `read_combine_goodreads()`: Loads and standardizes Goodreads CSV exports
- `read_bookclub()`: Processes book club meeting data
- `pivot_goodreads_data()`: Transforms individual ratings into club member columns
- `match_dataframes()`: Joins book club and Goodreads data on the lowercased title
- `merge_manual_ratings()`: Adds manual ratings; these take precedence over Goodreads ratings

The app runs the pipeline live; `data/processed_data.csv` is only an export.
