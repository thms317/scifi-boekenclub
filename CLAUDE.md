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
3. **Use absolute imports only,** for example `from scifi.analysis import member_stats`.
4. **Only `paths.py` contains `"data/..."` strings.**
5. **Use Polars everywhere.** No pandas in `src/` or `app.py`.

## Development Commands

Use the provided Makefile for common tasks:

- `make setup`: Complete development environment setup (installs dependencies, pre-commit hooks)
- `make test`: Run full test suite with coverage reporting
- `make clean`: Remove virtual environment, caches, and build artifacts; keeps `uv.lock`
- `make dashboard`: Run the Streamlit app from `app.py`

Python package management uses `uv`:
- `uv sync`: Install/update dependencies (includes `dev` and `notebooks` groups)
- `uv build`: Build the package
- `uv run pytest`: Run tests directly

## Testing and Quality

- Tests are in `tests/` directory using pytest
- Code quality enforced by:
  - Ruff (linting and formatting)
  - ty (type checking)
  - pre-commit hooks
- Run `make test` to execute full test suite with coverage

## Data Processing Notes

The core data processing uses Polars for performance. Key functions in `src/scifi/utils.py`:

- `read_combine_goodreads()`: Loads and standardizes Goodreads CSV exports
- `read_bookclub()`: Processes book club meeting data
- `pivot_goodreads_data()`: Transforms individual ratings into club member columns
- `match_dataframes()`: Joins book club and Goodreads data on title/author
- `merge_manual_ratings()`: Adds manual ratings; these take precedence over Goodreads ratings

The app runs the pipeline live; `data/processed_data.csv` is only an export.
