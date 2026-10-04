"""Configuration and paths for the scifi project."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]  # src/scifi/paths.py → repo root
DATA_DIR = ROOT_DIR / "data"
GOODREADS_DIR = DATA_DIR / "goodreads" / "clean"
BOOKCLUB_PATH = DATA_DIR / "bookclub" / "bookclub.csv"
MANUAL_RATINGS_PATH = DATA_DIR / "bookclub" / "manual_ratings.csv"
AUTHORS_PATH = DATA_DIR / "bookclub" / "authors.csv"
PROCESSED_PATH = DATA_DIR / "processed_data.csv"
