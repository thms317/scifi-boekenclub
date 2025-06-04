# Sci-Fi Boekenclub

[![python](https://img.shields.io/badge/python-3.12-g)](https://www.python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pydocstyle](https://img.shields.io/badge/pydocstyle-enabled-AD4CD3)](http://www.pydocstyle.org/en/stable/)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)

[![ci](https://github.com/revodatanl/scifi/actions/workflows/ci.yml/badge.svg)](https://github.com/revodatanl/scifi/actions/workflows/ci.yml)
[![semantic-release](https://github.com/revodatanl/scifi/actions/workflows/semantic-release.yml/badge.svg)](https://github.com/revodatanl/scifi/actions/workflows/semantic-release.yml)

The `scifi` project was generated from [RevoData Asset Bundle Templates](https://github.com/revodatanl/revo-asset-bundle-templates) version `0.15.1`.

## Prerequisites

This project heavily depends on the provided `Makefile` for various tasks. Without [`make`](https://www.gnu.org/software/make) installed, you will need to run the commands described in the `Makefile` manually.

## Getting Started

With [make](https://www.gnu.org/software/make) installed, run the following command to set up a fully configured development environment:

```bash
make setup
```

This installs [`Homebrew`](https://brew.sh), [`Git`](https://git-scm.com), [`uv`](https://github.com/astral-sh/uv), configures Python, sets up a virtual environment, and installs pre-commit hooks.

## Command Reference

The following additional commands are available to make development easy:

| Command | Description |
|---------|-------------|
| `make clean` | Removes virtual environment, lock files, and caches |
| `make test` | Runs a full test suite including coverage reporting |
