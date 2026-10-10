# Sci-Fi Boekenclub

[![python](https://img.shields.io/badge/python-3.12-g)](https://www.python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)

[![CI](https://github.com/thms317/scifi-boekenclub/actions/workflows/ci.yml/badge.svg)](https://github.com/thms317/scifi-boekenclub/actions/workflows/ci.yml)
[![Semantic Release](https://github.com/thms317/scifi-boekenclub/actions/workflows/semantic-release.yml/badge.svg)](https://github.com/thms317/scifi-boekenclub/actions/workflows/semantic-release.yml)

This is a Python data analysis project for analyzing the `Sci-Fi Boekenclub` reading data. The project combines Goodreads export data from multiple club members with book club meeting records to analyze reading preferences and ratings over time.

The ratings and trends are visualized in a nice [Streamlit dashboard](https://thms317-scifi-boekenclub-srcscifidashboard-erirdk.streamlit.app/).

## Getting Started

With [uv](https://docs.astral.sh/uv/) and [make](https://www.gnu.org/software/make) installed, run:

```bash
make setup
```

This runs `uv sync` and installs the git hooks with prek.

## Build the Dashboard

Instructions on how to update the source data can be found [here](data/README.md).

To build and test the Streamlit dashboard locally, run:

```bash
make dashboard
```

The hosted dashboard is automatically built and updated on every merge to `main`.

## Development

```bash
make lint   # ruff format check, ruff, ty and pydoclint; CI runs the same checks, the tests and a package build
make test   # pytest with coverage
```

Tool versions live in `uv.lock` (`uv lock --upgrade && uv sync` to upgrade) and, for the git hooks, in `.pre-commit-config.yaml` (`uv run prek autoupdate`).
