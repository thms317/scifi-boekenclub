"""Paths to the data files."""

from pathlib import Path

DATA_DIR = Path("data")
GOODREADS_DIR = DATA_DIR / "goodreads" / "clean"
BOOKCLUB_PATH = DATA_DIR / "bookclub" / "bookclub.csv"
MANUAL_RATINGS_PATH = DATA_DIR / "bookclub" / "manual_ratings.csv"
AUTHORS_PATH = DATA_DIR / "bookclub" / "authors.csv"
