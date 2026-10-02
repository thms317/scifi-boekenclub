"""Tests for data contract and integrity."""

from pathlib import Path

import polars as pl

from scifi.members import BookClubMembers
from scifi.paths import (
    AUTHORS_PATH,
    BOOKCLUB_PATH,
    GOODREADS_DIR,
    MANUAL_RATINGS_PATH,
    PROCESSED_PATH,
)
from scifi.utils import read_bookclub


class TestAuthors:
    """Test class for the authors data.

    Verifies that the authors.csv file is correctly structured
    and contains all required book club authors.

    """

    data_dir = Path(__file__).parents[1] / "data" / "bookclub"

    def test_authors_csv(self) -> None:
        """Test that every book club author has exactly one complete row.

        Asserts that:
        - Each author appears exactly once (unique)
        - No null values exist in the authors file
        - All book club authors are covered in the authors file

        """
        authors = pl.read_csv(self.data_dir / "authors.csv")
        assert authors["author"].is_unique().all()
        assert authors.null_count().sum_horizontal().item() == 0
        # The pipeline joins on the exact author name
        bookclub_authors = set(read_bookclub(self.data_dir / "bookclub.csv")["author"])
        assert bookclub_authors <= set(authors["author"])


class TestBookclub:
    """Test class for the bookclub data integrity.

    Verifies that bookclub.csv meets the data contract
    required by the pipeline and analysis.

    """

    data_dir = Path(__file__).parents[1] / "data" / "bookclub"

    def test_bookclub_index_unique(self) -> None:
        """Test that the bookclub index (Nummer) is unique.

        The index is used as the primary key and must be unique
        for proper data identification.

        """
        bookclub = read_bookclub(self.data_dir / "bookclub.csv")
        assert bookclub["index"].n_unique() == len(bookclub)

    def test_bookclub_no_null_dates(self) -> None:
        """Test that no dates are null in the bookclub data.

        All book club meetings must have a date, as the date
        is used for filtering and time-based analysis.

        """
        bookclub = read_bookclub(self.data_dir / "bookclub.csv")
        assert bookclub["date"].null_count() == 0

    def test_bookclub_unique_titles_lowercase(self) -> None:
        """Test that titles are unique after lowercasing.

        The join between bookclub and Goodreads data uses
        lowercased titles as the key. Duplicate titles
        (after lowercasing) would cause ambiguity in the join.

        """
        bookclub = read_bookclub(self.data_dir / "bookclub.csv")
        titles_lower = bookclub["title"].str.to_lowercase()
        assert titles_lower.n_unique() == len(titles_lower)


class TestMembers:
    """Test class for the member data contract.

    Verifies that the members registry is consistent with
    the data files and paths configuration.

    """

    def test_paths_exist(self) -> None:
        """Test that every constant in paths.py exists.

        All path constants must point to files or directories
        that exist on disk.

        """
        assert GOODREADS_DIR.is_dir(), f"GOODREADS_DIR does not exist: {GOODREADS_DIR}"
        assert BOOKCLUB_PATH.is_file(), f"BOOKCLUB_PATH does not exist: {BOOKCLUB_PATH}"
        assert MANUAL_RATINGS_PATH.is_file(), (
            f"MANUAL_RATINGS_PATH does not exist: {MANUAL_RATINGS_PATH}"
        )
        assert AUTHORS_PATH.is_file(), f"AUTHORS_PATH does not exist: {AUTHORS_PATH}"
        assert PROCESSED_PATH.parent.is_dir(), (
            f"PROCESSED_PATH parent directory does not exist: {PROCESSED_PATH.parent}"
        )

    def test_mapped_files_exist(self) -> None:
        """Test that every mapped file name exists in GOODREADS_DIR.

        Each member with a file_name must have a corresponding
        CSV file in the Goodreads directory.

        """
        reviewer_mapping = BookClubMembers.get_reviewer_mapping()
        for file_name, member_name in reviewer_mapping.items():
            file_path = GOODREADS_DIR / file_name
            assert file_path.is_file(), f"File for member {member_name} does not exist: {file_path}"

    def test_all_goodreads_files_mapped(self) -> None:
        """Test that every CSV in GOODREADS_DIR maps to a member.

        All Goodreads CSV files must be registered in the members list.
        Otherwise an unregistered export would show up as an unnamed rating column.

        """
        reviewer_mapping = BookClubMembers.get_reviewer_mapping()
        mapped_file_names = set(reviewer_mapping.keys())
        goodreads_files = {f.name for f in GOODREADS_DIR.glob("*.csv")}
        assert goodreads_files <= mapped_file_names, (
            f"Unmapped Goodreads files: {goodreads_files - mapped_file_names}"
        )
