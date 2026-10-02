"""Tests for the data processing pipeline."""

from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
import pytest

from scifi.data_processor import process_bookclub_data
from scifi.members import BookClubMembers


class TestProcessBookclubData:
    """Test class for the process_bookclub_data function."""

    @pytest.fixture(scope="class")
    def test_data_dir(self) -> Generator[Path, None, None]:
        """Fixture for creating a complete tiny dataset in a temporary directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create goodreads directory
            goodreads_dir = tmpdir_path / "goodreads"
            goodreads_dir.mkdir()

            # Create goodreads exports for two members
            thomas_export = pl.DataFrame(
                {
                    "Title": ["Book A", "Book B"],
                    "Author": ["Author A", "Author B"],
                    "My Rating": [5, 3],
                    "Average Rating": [4.0, 3.5],
                    "Original Publication Year": [2020, 2019],
                    "Number of Pages": [300, 250],
                    "Exclusive Shelf": ["read", "read"],
                },
            )
            thomas_export.write_csv(goodreads_dir / "thomas_goodreads_library_export.csv")

            dion_export = pl.DataFrame(
                {
                    "Title": ["Book A", "Book C"],
                    "Author": ["Author A", "Author C"],
                    "My Rating": [4, 0],
                    "Average Rating": [4.0, 3.0],
                    "Original Publication Year": [2020, 2018],
                    "Number of Pages": [300, 200],
                    "Exclusive Shelf": ["read", "to-read"],
                },
            )
            dion_export.write_csv(goodreads_dir / "dion_goodreads_library_export.csv")

            # Create bookclub CSV
            bookclub_csv = pl.DataFrame(
                {
                    "Nummer": [1, 2, 3],
                    "Datum": ["01/15/2020", "02/15/2020", "03/15/2020"],
                    "Boek": ["Book A", "Book B", "Book C"],
                    "Auteur": ["Author A", "Author B", "Author C"],
                    "Wie heeft gekozen?": ["Thomas", "Dion", "Thomas"],
                    "Locatie": ["Amsterdam", "Utrecht", "Rotterdam"],
                },
            )
            bookclub_csv.write_csv(tmpdir_path / "bookclub.csv")

            # Create manual ratings CSV
            manual_ratings_csv = pl.DataFrame(
                {
                    "title": ["Book A"],
                    "author": ["Author A"],
                    "Thomas": [4.5],
                },
                schema_overrides={"Thomas": pl.Float64},
            )
            manual_ratings_csv.write_csv(tmpdir_path / "manual_ratings.csv")

            # Create authors CSV (just a minimal version)
            authors_csv = pl.DataFrame(
                {
                    "author": ["Author A", "Author B", "Author C"],
                    "gender": ["man", "woman", "man"],
                    "country": ["Country1", "Country2", "Country3"],
                    "religion": ["religion1", "religion2", "religion3"],
                    "lgbtq": ["no", "no", "no"],
                    "ethnicity": ["ethnicity1", "ethnicity2", "ethnicity3"],
                },
            )
            authors_csv.write_csv(tmpdir_path / "authors.csv")

            yield tmpdir_path

    def test_exact_column_list(self, test_data_dir: Path) -> None:
        """Test that process_bookclub_data returns the exact expected column list."""
        bookclub_df, _, _ = process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

        # Expected schema: bookclub cols, goodreads cols, member cols (in registry order),
        # average_bookclub_rating, author cols
        all_member_names = BookClubMembers.get_member_names()
        expected_columns = [
            "index",
            "date",
            "title",
            "author",
            "suggested_by",
            "location",
            "original_publication_year",
            "average_goodreads_rating",
            "number_of_pages",
            *all_member_names,
            "average_bookclub_rating",
            "gender",
            "country",
            "religion",
            "lgbtq",
            "ethnicity",
        ]

        assert list(bookclub_df.columns) == expected_columns, (
            f"Column mismatch. Expected: {expected_columns}\nGot: {list(bookclub_df.columns)}"
        )

    def test_member_without_data_is_float64_null_column(self, test_data_dir: Path) -> None:
        """Test that a member without data gets an all-null Float64 column."""
        bookclub_df, _, _ = process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

        # Marloes is in the registry but has no data
        assert "Marloes" in bookclub_df.columns
        assert bookclub_df["Marloes"].dtype == pl.Float64
        # All values should be null
        assert bookclub_df["Marloes"].is_null().all()

    def test_manual_rating_overrides_goodreads(self, test_data_dir: Path) -> None:
        """Test that a manual rating overrides the Goodreads rating."""
        bookclass_df, _, _ = process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

        # Book A has Thomas rating of 5 in Goodreads but manual rating of 4.5
        book_a = bookclass_df.filter(pl.col("title") == "Book A")
        assert book_a["Thomas"][0] == 4.5

    def test_average_ignores_nulls(self, test_data_dir: Path) -> None:
        """Test that the average_bookclub_rating ignores null ratings."""
        bookclub_df, _, _ = process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

        # Book A has Thomas=4.5 and Dion=4.0, so average should be 4.25
        book_a = bookclub_df.filter(pl.col("title") == "Book A")
        # All other members should be null, so average should only use Thomas and Dion
        assert book_a["average_bookclub_rating"][0] == 4.25

    def test_no_right_columns(self, test_data_dir: Path) -> None:
        """Test that no _right suffix columns are left."""
        bookclub_df, _, _ = process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

        right_cols = [col for col in bookclub_df.columns if col.endswith("_right")]
        assert len(right_cols) == 0, f"Found unwanted right columns: {right_cols}"
