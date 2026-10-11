"""Tests for data contract and integrity."""

from pathlib import Path

import polars as pl
import pytest

from scifi.members import BookClubMembers
from scifi.paths import AUTHORS_PATH, BOOKCLUB_PATH, GOODREADS_DIR, MANUAL_RATINGS_PATH
from scifi.pipeline import process_bookclub_data, read_bookclub, read_manual_ratings


class TestAuthors:
    """Test class for the authors data.

    Verifies that the authors.csv file is correctly structured
    and contains all required book club authors.

    """

    def test_authors_csv(self) -> None:
        """Test that every book club author has exactly one complete row.

        Asserts that:
        - Each author appears exactly once (unique)
        - No null values exist in the authors file
        - All book club authors are covered in the authors file

        """
        authors = pl.read_csv(AUTHORS_PATH)
        assert authors["author"].is_unique().all()
        assert authors.null_count().sum_horizontal().item() == 0
        # The pipeline joins on the exact author name
        bookclub_authors = set(read_bookclub(BOOKCLUB_PATH)["author"])
        assert bookclub_authors <= set(authors["author"])


class TestBookclub:
    """Test class for the bookclub data integrity.

    Verifies that bookclub.csv meets the data contract
    required by the pipeline and analysis.

    """

    def test_bookclub_index_unique(self) -> None:
        """Test that the bookclub index (Nummer) is unique.

        The index is used as the primary key and must be unique
        for proper data identification.

        """
        bookclub = read_bookclub(BOOKCLUB_PATH)
        assert bookclub["index"].n_unique() == len(bookclub)

    def test_bookclub_no_null_dates(self) -> None:
        """Test that no dates are null in the bookclub data.

        All book club meetings must have a date, as the date
        is used for filtering and time-based analysis.

        """
        bookclub = read_bookclub(BOOKCLUB_PATH)
        assert bookclub["date"].null_count() == 0

    def test_bookclub_unique_titles_lowercase(self) -> None:
        """Test that titles are unique after lowercasing.

        The join between bookclub and Goodreads data uses
        lowercased titles as the key. Duplicate titles
        (after lowercasing) would cause ambiguity in the join.

        """
        bookclub = read_bookclub(BOOKCLUB_PATH)
        titles_lower = bookclub["title"].str.to_lowercase()
        assert titles_lower.n_unique() == len(titles_lower)


class TestGoodreadsExports:
    """Test class for the Goodreads export files.

    Verifies that every file in GOODREADS_DIR is a standard Goodreads export.
    The pipeline combines the exports by column name and reads a malformed
    file or row as nulls or garbage instead of failing.

    """

    @pytest.mark.parametrize("csv_file", sorted(GOODREADS_DIR.glob("*.csv")), ids=lambda f: f.name)
    def test_export_is_a_standard_goodreads_csv(self, csv_file: Path) -> None:
        """Test that an export parses and has the pipeline's columns and a title on every row."""
        export = pl.read_csv(csv_file)
        assert export["Book Id"].dtype == pl.Int64, "A row is mangled: its Book Id is not a number"
        # "Average Rating" is not required: Thomas's exports lack it (see data/README.md)
        required = {"Title", "Author", "My Rating", "Original Publication Year", "Number of Pages"}
        assert required <= set(export.columns), f"Missing columns: {required - set(export.columns)}"
        assert export["Title"].null_count() == 0


class TestMembers:
    """Test class for the member data contract.

    Verifies that the members registry is consistent with
    the Goodreads export files.

    """

    def test_mapped_files_exist(self) -> None:
        """Test that every mapped file name exists in GOODREADS_DIR.

        Each member with a file_name must have a corresponding
        CSV file in the Goodreads directory.

        """
        for member in BookClubMembers.get_all_members():
            if member.file_name is not None:
                file_path = GOODREADS_DIR / member.file_name
                assert file_path.is_file(), f"File for {member.name} does not exist: {file_path}"

    def test_all_goodreads_files_mapped(self) -> None:
        """Test that every CSV in GOODREADS_DIR maps to a member.

        All Goodreads CSV files must be registered in the members list.
        Otherwise an unregistered export would show up as an unnamed rating column.

        """
        mapped_file_names = {
            member.file_name
            for member in BookClubMembers.get_all_members()
            if member.file_name is not None
        }
        goodreads_files = {f.name for f in GOODREADS_DIR.glob("*.csv")}
        assert goodreads_files <= mapped_file_names, (
            f"Unmapped Goodreads files: {goodreads_files - mapped_file_names}"
        )


class TestManualRatings:
    """Test class for the manual ratings data contract."""

    def test_manual_columns_are_members(self) -> None:
        """Test that every rating column in manual_ratings.csv is a registered member.

        The pipeline applies only the manual columns that exist in the
        processed data, so a misspelled member would be ignored silently.

        """
        manual = read_manual_ratings(MANUAL_RATINGS_PATH).drop("title", "author")
        unknown = set(manual.columns) - set(BookClubMembers.get_member_names())
        assert not unknown, f"Manual rating columns that are not members: {unknown}"


class TestProcessedData:
    """Test class for the contract of the processed data on the real files."""

    def test_every_book_has_goodreads_average(self) -> None:
        """Test that every book club book, the next one included, has a Goodreads average.

        The average comes from the Goodreads exports, so add a book to an export
        when its meeting is planned. Thomas's exports lack the "Average Rating"
        column, so his file is maintained by hand; committing a raw export would
        silently drop the average of every book only he has.

        """
        bookclub_df = process_bookclub_data()
        missing = bookclub_df.filter(pl.col("average_goodreads_rating").is_null())["title"]
        assert missing.is_empty(), f"Books without a Goodreads average: {missing.to_list()}"

    def test_one_row_per_book(self) -> None:
        """Test that the join with the Goodreads data duplicates no book club book.

        Exports that spell a title or author differently must still be one
        Goodreads book, or the club book is ranked twice.

        """
        bookclub_df = process_bookclub_data()
        assert bookclub_df["index"].n_unique() == len(bookclub_df)
