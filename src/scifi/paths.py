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

    Returns the Goodreads export CSVs and the three bookclub input files,
    but not the generated outputs like processed_data.csv.

    Parameters
    ----------
    data_dir : Path, optional
        The data directory to search, by default DATA_DIR.

    Returns
    -------
    list[Path]
        A sorted list of input file paths.
    """
    files = []

    # Add Goodreads CSV exports
    goodreads_dir = data_dir / "goodreads" / "clean"
    if goodreads_dir.is_dir():
        files.extend(sorted(goodreads_dir.glob("*.csv")))

    # Add bookclub input files
    bookclub_dir = data_dir / "bookclub"
    for filename in ["bookclub.csv", "manual_ratings.csv", "authors.csv"]:
        path = bookclub_dir / filename
        if path.is_file():
            files.append(path)

    return sorted(files)


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
    fingerprints: list[tuple[str, int, int]] = []

    for file_path in files:
        if file_path.is_file():
            stat = file_path.stat()
            fingerprints.append((str(file_path), stat.st_mtime_ns, stat.st_size))

    return tuple(sorted(fingerprints))
