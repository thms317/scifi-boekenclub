"""Configuration and paths for the scifi project."""

from collections.abc import Iterable
from pathlib import Path

DATA_DIR = Path("data")
GOODREADS_DIR = DATA_DIR / "goodreads" / "clean"
BOOKCLUB_PATH = DATA_DIR / "bookclub" / "bookclub.csv"
MANUAL_RATINGS_PATH = DATA_DIR / "bookclub" / "manual_ratings.csv"
AUTHORS_PATH = DATA_DIR / "bookclub" / "authors.csv"
PROCESSED_PATH = DATA_DIR / "processed_data.csv"


def input_files(data_dir: Path = DATA_DIR) -> list[Path]:
    """Return the input files for the data pipeline.

    Returns the Goodreads export CSVs and the three bookclub input files that exist,
    but not the generated outputs: processed_data.csv and the goodreads_*.csv files,
    which save_processed_data writes to data/goodreads/, outside the clean/ folder.

    Parameters
    ----------
    data_dir : Path, optional
        The data directory to search, by default DATA_DIR.

    Returns
    -------
    list[Path]
        A sorted list of input file paths.
    """
    # Member exports can start with goodreads_ too (e.g. goodreads_library_export-thirsa.csv)
    goodreads_exports = list((data_dir / "goodreads" / "clean").glob("*.csv"))
    bookclub_files = [
        data_dir / "bookclub" / name
        for name in ("bookclub.csv", "manual_ratings.csv", "authors.csv")
    ]
    return sorted(path for path in goodreads_exports + bookclub_files if path.is_file())


def source_fingerprint(files: Iterable[Path]) -> tuple[tuple[str, int, int], ...]:
    """Return a fingerprint of input files for cache invalidation.

    Returns a sorted tuple of (path, mtime_ns, size) for each file that exists.
    Adding, removing, or editing an input changes the fingerprint.

    Parameters
    ----------
    files : Iterable[Path]
        The files to fingerprint.

    Returns
    -------
    tuple[tuple[str, int, int], ...]
        A sorted tuple of (str(path), st_mtime_ns, st_size) for each existing file.
    """
    stats = [(str(path), path.stat()) for path in files if path.is_file()]
    return tuple(sorted((name, stat.st_mtime_ns, stat.st_size) for name, stat in stats))
