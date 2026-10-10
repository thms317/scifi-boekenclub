"""Tests for the pipeline module."""

from collections.abc import Generator
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
import pytest

from scifi.members import BookClubMember, BookClubMembers
from scifi.pipeline import (
    merge_manual_ratings,
    pivot_goodreads_data,
    process_bookclub_data,
    read_bookclub,
    read_combine_goodreads,
)


class TestReadGoodreads:
    """Test class for the read_goodreads function."""

    @pytest.fixture(scope="class")
    def test_goodreads_dir(self) -> Generator[Path, None, None]:
        """Fixture for creating sample CSVs in a temporary directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            df1 = pl.DataFrame(
                {
                    "Title": ["Sample Book"],
                    "Author": ["Sample Author"],
                    "My Rating": [5],
                    "Average Rating": [4.5],
                    "Original Publication Year": [2020],
                    "Number of Pages": [300],
                    "Exclusive Shelf": ["read"],
                },
            )
            df2 = pl.DataFrame(
                {
                    "Title": ["Another Book"],
                    "Author": ["Another Author"],
                    "My Rating": [4],
                    "Average Rating": [4.0],
                    "Original Publication Year": [2019],
                    "Number of Pages": [250],
                    "Exclusive Shelf": ["read"],
                },
            )
            df3 = pl.DataFrame(
                {
                    "Title": ["Unread Book"],
                    "Author": ["Some Author"],
                    "My Rating": [0],
                    "Average Rating": [3.5],
                    "Original Publication Year": [2018],
                    "Number of Pages": [200],
                    "Exclusive Shelf": ["to-read"],
                },
            )
            df1.write_csv(tmpdir_path / "koen_goodreads_library_export.csv")
            df2.write_csv(tmpdir_path / "thomas_goodreads_library_export.csv")
            df3.write_csv(tmpdir_path / "koen_m_goodreads_library_export.csv")
            yield tmpdir_path

    def test_read_goodreads(self, test_goodreads_dir: Path) -> None:
        """Test for the read_goodreads function."""
        df_goodreads_test = read_combine_goodreads(test_goodreads_dir)
        # Assert column names
        expected_columns = [
            "title",
            "author",
            "rating",
            "average_goodreads_rating",
            "original_publication_year",
            "number_of_pages",
            "file_name",
        ]
        for column in expected_columns:
            assert column in df_goodreads_test.columns, f"Missing column: {column}"
        # Assert that books on every shelf are included (to-read books still provide book data)
        expected = {"Sample Book", "Another Book", "Unread Book"}
        result = set(df_goodreads_test["title"].to_list())
        assert expected == result, "Titles in the DataFrame do not match expected values"
        # Assert that a 0 rating (not rated) becomes null
        unread = df_goodreads_test.filter(pl.col("title") == "Unread Book")
        assert unread["rating"][0] is None

    def test_read_goodreads_missing_column(self, test_goodreads_dir: Path) -> None:
        """Test that an export without a column gets nulls for it instead of failing."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            for csv_file in test_goodreads_dir.glob("*.csv"):
                (tmpdir_path / csv_file.name).write_text(csv_file.read_text())
            pl.DataFrame(
                {
                    "Title": ["New Export Book"],
                    "Author": ["New Author"],
                    "My Rating": [3],
                    "Original Publication Year": [2021],
                    "Number of Pages": [100],
                    "Exclusive Shelf": ["read"],
                },
            ).write_csv(tmpdir_path / "new_export.csv")
            df_goodreads_test = read_combine_goodreads(tmpdir_path)
        new_book = df_goodreads_test.filter(pl.col("title") == "New Export Book")
        assert new_book["average_goodreads_rating"][0] is None
        assert df_goodreads_test.height == 4

    def test_read_goodreads_empty_directory(self) -> None:
        """Test how read_goodreads handles an empty directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Call the function with an empty directory
            with pytest.raises(FileNotFoundError, match="No CSV files found"):
                _ = read_combine_goodreads(tmpdir_path)


class TestReadBookclub:
    """Test class for the read_bookclub function."""

    @pytest.fixture(scope="class")
    def test_bookclub_csv(self) -> Generator[Path, None, None]:
        """Fixture for creating sample Bookclub CSV files in a temporary directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            df_bookclub_test = pl.DataFrame(
                {
                    "Nummer": [1, 2],
                    "Datum": ["01/01/2020", "02/15/2021"],
                    "Boek": ["Sample Book", "Another Book"],
                    "Auteur": ["Sample Author", "Another Author"],
                    "Wie heeft gekozen?": ["Member A", "Member B"],
                    "Locatie": ["Location A", "Location B"],
                },
            )
            csv_bookclub_path = tmpdir_path / "sample_bookclub.csv"
            df_bookclub_test.write_csv(csv_bookclub_path)
            yield csv_bookclub_path

    def test_read_bookclub(self, test_bookclub_csv: Path) -> None:
        """Test that read_bookclub returns a DataFrame with expected columns and data."""
        df_bookclub_test = read_bookclub(test_bookclub_csv)
        # Assert column names
        expected_columns = {
            "index",
            "date",
            "title",
            "author",
            "suggested_by",
            "location",
        }
        actual_columns = set(df_bookclub_test.columns)
        missing_columns = expected_columns - actual_columns
        unexpected_columns = actual_columns - expected_columns
        assert not missing_columns, f"Missing columns: {missing_columns}"
        assert not unexpected_columns, f"Unexpected columns: {unexpected_columns}"
        # Assert specific data values
        expected_titles = {"Sample Book", "Another Book"}
        actual_titles = set(df_bookclub_test["title"].to_list())
        assert expected_titles == actual_titles, (
            "Titles in the DataFrame do not match expected values"
        )
        # Assert that the 'date' column is of date type
        assert df_bookclub_test["date"].dtype == pl.Date, "Date column is not of date type"
        # Assert specific date values
        expected_dates = [
            date(2020, 1, 1),
            date(2021, 2, 15),
        ]
        actual_dates = df_bookclub_test["date"].to_list()
        assert expected_dates == actual_dates, "Parsed dates do not match expected date values"


class TestPivotGoodreadsData:
    """Test class for the pivot_goodreads_data function."""

    @pytest.fixture(scope="class")
    def members(self) -> list[BookClubMember]:
        """Fixture for two members with an export."""
        return [
            BookClubMember("Koen", "koen_goodreads_library_export.csv"),
            BookClubMember("Thomas", "thomas_goodreads_library_export.csv"),
        ]

    @pytest.fixture(scope="class")
    def df_goodreads(self) -> pl.DataFrame:
        """Fixture for a sample Goodreads DataFrame."""
        return pl.DataFrame(
            {
                "title": ["Sample Book", "Sample Book"],
                "author": ["Sample Author", "Sample Author"],
                "average_goodreads_rating": [4.5, 4.7],
                "original_publication_year": [2020, 2020],
                "number_of_pages": [250, 300],
                "rating": [5, 4],
                "file_name": [
                    "koen_goodreads_library_export.csv",
                    "thomas_goodreads_library_export.csv",
                ],
            },
        )

    def test_pivot_goodreads_data(
        self,
        df_goodreads: pl.DataFrame,
        members: list[BookClubMember],
    ) -> None:
        """Test the pivot_goodreads_data."""
        df_pivot = pivot_goodreads_data(df_goodreads, members)
        # Assert column names and shape
        expected_columns = [
            "title",
            "author",
            "average_goodreads_rating",
            "original_publication_year",
            "number_of_pages",
            "Koen",
            "Thomas",
        ]
        assert set(df_pivot.columns) == set(expected_columns)
        assert df_pivot.shape[0] == 1
        # Assert that the averaged goodreads value is correct (in case of rating drift)
        assert df_pivot["average_goodreads_rating"][0] == 4.6
        # Pages are averaged over editions with different page counts
        assert df_pivot["number_of_pages"][0] == 275

    def test_pivot_goodreads_data_different_years(
        self,
        df_goodreads: pl.DataFrame,
        members: list[BookClubMember],
    ) -> None:
        """Test that editions with a different original year are still one book."""
        df_goodreads = df_goodreads.with_columns(
            pl.Series("original_publication_year", [1963, 1953])
        )
        df_pivot = pivot_goodreads_data(df_goodreads, members)
        assert df_pivot.shape[0] == 1
        assert df_pivot["original_publication_year"][0] == 1953

    def test_pivot_goodreads_data_member_without_export(
        self,
        df_goodreads: pl.DataFrame,
    ) -> None:
        """Test that a member without an export, or with an empty one, gets an all-null column."""
        members = [
            BookClubMember("Koen", "koen_goodreads_library_export.csv"),
            BookClubMember("Thomas", "thomas_goodreads_library_export.csv"),
            BookClubMember("Empty", "empty_export.csv"),  # This file has no rows
            BookClubMember("Marloes"),
        ]
        df_pivot = pivot_goodreads_data(df_goodreads, members)
        assert df_pivot["Koen"][0] == 5
        for member in ("Empty", "Marloes"):
            assert df_pivot[member].dtype == pl.Float64
            assert df_pivot[member].is_null().all()


class TestMergeManualRatings:
    """Test class for the merge_manual_ratings function."""

    def test_manual_rating_overrides_existing(self) -> None:
        """Test that a manual rating wins over an existing rating, and empty ones do not."""
        processed = pl.DataFrame({"title": ["Book A"], "Robert": [5.0], "Peter": [4.0]})
        manual = pl.DataFrame(
            {"title": ["book a"], "author": ["X"], "Robert": [4.0], "Peter": [None]},
            schema_overrides={"Peter": pl.Float64},
        )
        merged = merge_manual_ratings(processed, manual)
        assert merged["Robert"][0] == 4.0
        assert merged["Peter"][0] == 4.0


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
                    "Title": ["Book A", "BOOK B"],  # Titles are matched case-insensitively
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

    @pytest.fixture(scope="class")
    def bookclub_df(self, test_data_dir: Path) -> pl.DataFrame:
        """Fixture for the processed book club data of the tiny dataset."""
        return process_bookclub_data(
            goodreads_dir=test_data_dir / "goodreads",
            bookclub_path=test_data_dir / "bookclub.csv",
            manual_ratings_path=test_data_dir / "manual_ratings.csv",
            authors_path=test_data_dir / "authors.csv",
        )

    def test_exact_column_list(self, bookclub_df: pl.DataFrame) -> None:
        """Test that process_bookclub_data returns the exact expected column list."""
        # Expected schema: bookclub cols, goodreads cols, member cols (in registry order),
        # average_bookclub_rating, author cols
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
            *BookClubMembers.get_member_names(),
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

    def test_titles_match_case_insensitively(self, bookclub_df: pl.DataFrame) -> None:
        """Test that a Goodreads title in another case still matches the book club title."""
        book_b = bookclub_df.filter(pl.col("title") == "Book B")
        assert book_b["average_goodreads_rating"][0] == 3.5
        assert book_b["Thomas"][0] == 3.0

    def test_member_without_data_is_float64_null_column(self, bookclub_df: pl.DataFrame) -> None:
        """Test that a member without data gets an all-null Float64 column."""
        # Marloes is in the registry but has no data
        assert "Marloes" in bookclub_df.columns
        assert bookclub_df["Marloes"].dtype == pl.Float64
        # All values should be null
        assert bookclub_df["Marloes"].is_null().all()

    def test_manual_rating_overrides_goodreads(self, bookclub_df: pl.DataFrame) -> None:
        """Test that a manual rating overrides the Goodreads rating."""
        # Book A has Thomas rating of 5 in Goodreads but manual rating of 4.5
        book_a = bookclub_df.filter(pl.col("title") == "Book A")
        assert book_a["Thomas"][0] == 4.5

    def test_average_ignores_nulls(self, bookclub_df: pl.DataFrame) -> None:
        """Test that the average_bookclub_rating ignores null ratings."""
        # Book A has Thomas=4.5 and Dion=4.0, so average should be 4.25
        book_a = bookclub_df.filter(pl.col("title") == "Book A")
        # All other members should be null, so average should only use Thomas and Dion
        assert book_a["average_bookclub_rating"][0] == 4.25

    def test_no_right_columns(self, bookclub_df: pl.DataFrame) -> None:
        """Test that no _right suffix columns are left."""
        right_cols = [col for col in bookclub_df.columns if col.endswith("_right")]
        assert len(right_cols) == 0, f"Found unwanted right columns: {right_cols}"
