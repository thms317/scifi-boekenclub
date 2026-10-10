# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python data analysis project for analyzing the "Sci-Fi Boekenclub" (Sci-Fi Book Club) reading data. The project combines Goodreads export data from multiple club members with book club meeting records to analyze reading preferences and ratings over time.

## Architecture

The project is a Streamlit web app (`app.py`) backed by a pure Python package (`src/scifi/`).

### Module layout
- `app.py`: Streamlit entrypoint; calls `scifi.ui` pages
- `src/scifi/`:
  - `paths.py`: Paths to the data files
  - `members.py`: Member registry mapping export file names to names
  - `pipeline.py`: CSV readers and the pipeline that combines them into the dashboard frame
  - `analysis.py`: Pure computations on Polars DataFrames
  - `visualizer.py`: Plotly figure builders
  - `ui/`: Streamlit pages (one `render()` function per module)
- `books/sparrow/`: physics side notebooks on The Sparrow; linted, otherwise unrelated to the app

### Data sources
- Goodreads CSV exports from individual members (in `data/goodreads/clean/`)
- Book club meeting records (`data/bookclub/bookclub.csv`)
- Manual ratings (`data/bookclub/manual_ratings.csv`)
- Authors, one row per author (`data/bookclub/authors.csv`)

### Import rules
1. **Imports point down:** `app.py` → `scifi.ui.*` → `analysis`, `visualizer`, `pipeline` → `members`, `paths`. Nothing in `scifi` imports `app.py`.
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

`src/scifi/pipeline.py` runs live on every page render (about 0.2 s). There is no cache and no processed-data file. The steps, each a tested function:

- `read_combine_goodreads()`: every shelf of every export, combined by column name (an export without a column gets nulls)
- `read_bookclub()` and `read_manual_ratings()`: the club's own CSVs
- `pivot_goodreads_data()`: one row per book, a Float64 column per member in registry order
- `merge_manual_ratings()`: manual ratings win over Goodreads ratings
- `process_bookclub_data()`: joins everything on the lowercased title (every book club book is kept), adds the club average and the author columns, and fixes the column order
