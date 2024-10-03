"""Tests for the file_utils module."""

from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
import pytest

from scifi.file_utils import match_dataframes, pivot_goodreads_data, read_bookclub, read_goodreads


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
                }
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
                }
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
                }
            )
            df1.write_csv(tmpdir_path / "koen_goodreads_library_export.csv")
            df2.write_csv(tmpdir_path / "thomas_goodreads_library_export.csv")
            df3.write_csv(tmpdir_path / "koen_m_goodreads_library_export.csv")
            yield tmpdir_path

    def test_read_goodreads(self, test_goodreads_dir: Path) -> None:
        """Test for the read_goodreads function."""
        df_goodreads_test = read_goodreads(test_goodreads_dir)
        # Assert that df is a Polars DataFrame
        assert isinstance(
            df_goodreads_test, pl.DataFrame
        ), "read_goodreads did not return a Polars DataFrame"
        # Assert column names
        expected_columns = [
            "title",
            "author",
            "rating",
            "average_goodreads_rating",
            "original_publication_year",
            "number_of_pages",
            "path",
        ]
        for column in expected_columns:
            assert column in df_goodreads_test.columns, f"Missing column: {column}"
        # Assert that only read books are included
        expected = {"Sample Book", "Another Book"}
        result = set(df_goodreads_test["title"].to_list())
        assert expected == result, "Titles in the DataFrame do not match expected values"

    def test_read_goodreads_empty_directory(self) -> None:
        """Test how read_goodreads handles an empty directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Call the function with an empty directory
            with pytest.raises(pl.exceptions.ComputeError, match="expected at least 1 source"):
                _ = read_goodreads(tmpdir_path)


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
                }
            )
            csv_bookclub_path = tmpdir_path / "sample_bookclub.csv"
            df_bookclub_test.write_csv(csv_bookclub_path)
            yield csv_bookclub_path

    def test_read_bookclub(self, test_bookclub_csv: Path) -> None:
        """Test that read_bookclub returns a DataFrame with expected columns and data."""
        df_bookclub_test = read_bookclub(test_bookclub_csv)
        # Assert that df is a Polars DataFrame
        assert isinstance(
            df_bookclub_test, pl.DataFrame
        ), "read_bookclub did not return a Polars DataFrame"
        # Assert column names
        expected_columns = {
            "index",
            "date",
            "title",
            "author",
            "blame",
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
        assert (
            expected_titles == actual_titles
        ), "Titles in the DataFrame do not match expected values"
        # Assert that the 'date' column is of datetime type
        assert df_bookclub_test["date"].dtype == pl.Datetime, "Date column is not of datetime type"
        # Assert specific date values
        expected_dates = [
            datetime(2020, 1, 1),  # noqa: DTZ001
            datetime(2021, 2, 15),  # noqa: DTZ001
        ]
        actual_dates = df_bookclub_test["date"].to_list()
        assert expected_dates == actual_dates, "Parsed dates do not match expected datetime values"

    def test_read_bookclub_empty_directory(self) -> None:
        """Test that read_bookclub handles an empty directory gracefully."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Call the function with an empty directory
            with pytest.raises(pl.exceptions.ComputeError, match="expected at least 1 source"):
                _ = read_bookclub(tmpdir_path)


class TestPivotGoodreadsData:
    """Test class for the pivot_goodreads_data function."""

    @pytest.fixture(scope="class")
    def reviewer_mapping(self) -> dict[str, str]:
        """Fixture for dictionary mapping file paths to reviewer names."""
        return {
            "data/goodreads/koen_goodreads_library_export.csv": "Koen",
            "data/goodreads/thomas_goodreads_library_export.csv": "Thomas",
        }

    @pytest.fixture(scope="class")
    def df_goodreads(self) -> pl.DataFrame:
        """Fixture for a sample Goodreads DataFrame."""
        return pl.DataFrame(
            {
                "title": ["Sample Book", "Sample Book"],
                "author": ["Sample Author", "Sample Author"],
                "average_goodreads_rating": [4.5, 4.5],
                "original_publication_year": [2020, 2020],
                "number_of_pages": [300, 300],
                "rating": [5, 4],
                "path": [
                    "data/goodreads/koen_goodreads_library_export.csv",
                    "data/goodreads/thomas_goodreads_library_export.csv",
                ],
            }
        )

    def test_pivot_goodreads_data(
        self, df_goodreads: pl.DataFrame, reviewer_mapping: dict[str, str]
    ) -> None:
        """Test the pivot_goodreads_data."""
        df_pivot = pivot_goodreads_data(df_goodreads, reviewer_mapping)
        # Assert that df_pivot is a Polars DataFrame
        assert isinstance(df_pivot, pl.DataFrame)
        # Assert column names and shape
        expected_columns = [
            "title",
            "author",
            "average_goodreads_rating",
            "original_publication_year",
            "number_of_pages",
            "Koen",
            "Thomas",
            "average_bookclub_rating",
        ]
        assert set(df_pivot.columns) == set(expected_columns)
        assert df_pivot.shape[0] == 1
        # Assert average_bookclub_rating calculation
        assert df_pivot["average_bookclub_rating"][0] == 4.5


class TestMatchDataframes:
    """Test class for the match_dataframes function."""

    @pytest.fixture(scope="class")
    def df_bookclub(self) -> pl.DataFrame:
        """Fixture for a sample Bookclub DataFrame."""
        return pl.DataFrame(
            {
                "title": ["Sample Book", "Non-Matching Book"],
                "author": ["Sample Author", "Unknown Author"],
                "date": [pl.datetime(2020, 1, 1), pl.datetime(2021, 1, 1)],
            }
        )

    @pytest.fixture(scope="class")
    def df_pivot(self) -> pl.DataFrame:
        """Fixture for a sample pivoted DataFrame."""
        return pl.DataFrame(
            {
                "title": ["Sample Book", "Another Book"],
                "author": ["Sample Author", "Another Author"],
                "average_goodreads_rating": [4.5, 4.0],
            }
        )

    @pytest.fixture(scope="class")
    def df_pivot_lowercase(self) -> pl.DataFrame:
        """Fixture for a lowercase sample pivoted DataFrame."""
        return pl.DataFrame(
            {
                "title": ["sample Book", "another Book"],
                "author": ["sample Author", "another Author"],
                "average_goodreads_rating": [4.5, 4.0],
            }
        )

    def test_match_dataframes_inner_join(
        self, df_bookclub: pl.DataFrame, df_pivot: pl.DataFrame
    ) -> None:
        """Test that match_dataframes performs an inner join correctly."""
        matched_df = match_dataframes(df_bookclub, df_pivot, on="title", how="inner")
        assert matched_df.shape[0] == 1
        assert matched_df["title"][0] == "Sample Book"

    def test_match_dataframes_left_join(
        self, df_bookclub: pl.DataFrame, df_pivot: pl.DataFrame
    ) -> None:
        """Test that match_dataframes performs a left join correctly."""
        matched_df = match_dataframes(df_bookclub, df_pivot, on="title", how="left")
        assert matched_df.shape[0] == 2
        # The non-matching book should have nulls for the pivoted data
        assert matched_df["title"][1] == "Non-Matching Book"
        assert matched_df["average_goodreads_rating"][1] is None

    def test_match_dataframes_case_insensitive(
        self, df_bookclub: pl.DataFrame, df_pivot_lowercase: pl.DataFrame
    ) -> None:
        """Test that match_dataframes matches titles case-insensitively."""
        matched_df = match_dataframes(df_bookclub, df_pivot_lowercase, on="title", how="inner")
        assert matched_df.shape[0] == 1
        assert matched_df["title"][0].lower() == "sample book"

    def test_match_dataframes_anti_join(
        self, df_bookclub: pl.DataFrame, df_pivot: pl.DataFrame
    ) -> None:
        """Test that match_dataframes performs an anti join correctly."""
        matched_df = match_dataframes(df_bookclub, df_pivot, on="title", how="anti")
        assert matched_df.shape[0] == 1
        assert matched_df["title"][0] == "Non-Matching Book"
