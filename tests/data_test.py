"""Tests for data contract and integrity."""

from pathlib import Path

import polars as pl

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
