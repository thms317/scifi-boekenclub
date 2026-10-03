"""Configuration and paths for the scifi project."""

import os
from pathlib import Path


def _repo_root() -> Path:
    """Return the repository root: SCIFI_ROOT, else the editable-install root, else the cwd.

    Returns
    -------
    Path
        The repository root directory.
    """
    if root := os.environ.get("SCIFI_ROOT"):
        return Path(root)
    root = Path(__file__).resolve().parents[2]  # src/scifi/paths.py → repo root
    return root if (root / "data").is_dir() else Path.cwd()  # non-editable install (Cloud)


ROOT_DIR = _repo_root()
DATA_DIR = ROOT_DIR / "data"
GOODREADS_DIR = DATA_DIR / "goodreads" / "clean"
BOOKCLUB_PATH = DATA_DIR / "bookclub" / "bookclub.csv"
MANUAL_RATINGS_PATH = DATA_DIR / "bookclub" / "manual_ratings.csv"
AUTHORS_PATH = DATA_DIR / "bookclub" / "authors.csv"
PROCESSED_PATH = DATA_DIR / "processed_data.csv"
