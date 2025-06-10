# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python data analysis project for analyzing the "Sci-Fi Boekenclub" (Sci-Fi Book Club) reading data. The project combines Goodreads export data from multiple club members with book club meeting records to analyze reading preferences and ratings over time.

## Architecture

The project follows a data pipeline structure:

1. **Data Sources**:
   - Goodreads CSV exports from individual members (in `data/goodreads/`)
   - Book club meeting records (`data/bookclub_source.csv`)

2. **Core Processing**:
   - Data cleaning and combination utilities in `src/scifi/utils.py`
   - Jupyter notebooks for analysis workflow in `notebooks/`

3. **Analysis Pipeline**:
   - `cleaning.ipynb`: Clean and standardize Goodreads data
   - `aggregating.ipynb`: Combine data sources and create aggregated datasets
   - `exploration.ipynb`: Main analysis and visualization
   - `visualization.ipynb`: Additional charts and plots

## Development Commands

Use the provided Makefile for common tasks:

- `make setup`: Complete development environment setup (installs dependencies, pre-commit hooks)
- `make test`: Run full test suite with coverage reporting
- `make clean`: Remove virtual environment, lock files, and caches

Python package management uses `uv`:
- `uv sync`: Install/update dependencies
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

The project handles multiple reviewer mappings and calculates both individual and average ratings across club members.
