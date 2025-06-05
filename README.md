# Sci-Fi Boekenclub

[![python](https://img.shields.io/badge/python-3.12-g)](https://www.python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pydocstyle](https://img.shields.io/badge/pydocstyle-enabled-AD4CD3)](http://www.pydocstyle.org/en/stable/)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)

[![CI](https://github.com/thms317/scifi-boekenclub/actions/workflows/ci.yml/badge.svg)](https://github.com/thms317/scifi-boekenclub/actions/workflows/ci.yml)
[![Semantic Release](https://github.com/thms317/scifi-boekenclub/actions/workflows/semantic-release.yml/badge.svg)](https://github.com/thms317/scifi-boekenclub/actions/workflows/semantic-release.yml)

This is a Python data analysis project for analyzing the `Sci-Fi Boekenclub` reading data. The project combines Goodreads export data from multiple club members with book club meeting records to analyze reading preferences and ratings over time.

The ratings and trends are visualized in a nice [Streamlit dashboard](https://thms317-scifi-boekenclub-srcscifidashboard-erirdk.streamlit.app/).

The project was generated from [RevoData Asset Bundle Templates](https://github.com/revodatanl/revo-asset-bundle-templates) version `0.15.1`.

## Getting Started

With [make](https://www.gnu.org/software/make) installed, run the following command to set up a fully configured development environment:

```bash
make setup
```

This installs [`Homebrew`](https://brew.sh), [`Git`](https://git-scm.com), [`uv`](https://github.com/astral-sh/uv), configures Python, sets up a virtual environment, and installs pre-commit hooks.

## Build the Dashboard

Instructions on how to update the source data can be found [here](data/README.md).

To build and test the Streamlit dashboard locally, run:

```bash
make dashboard
```

The hosted dashboard is automatically built and updated on every merge to `main`.
