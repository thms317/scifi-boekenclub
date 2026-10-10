"""Tests for analysis module functions."""

from datetime import date

import polars as pl
import pytest

from scifi.analysis import (
    current_meeting,
    member_correlations,
    rank_books,
    rating_trend,
    suggester_stats,
)


@pytest.fixture
def sample_data() -> pl.DataFrame:
    """Create sample bookclub data for testing."""
    return pl.DataFrame(
        {
            "index": [1, 2, 3, 4, 5],
            "date": [
                date(2024, 1, 15),
                date(2024, 2, 10),
                date(2024, 3, 20),
                date(2024, 3, 20),
                date(2024, 4, 5),
            ],
            "title": ["Book A", "Book B", "Book C", "Book D", "Book E"],
            "author": ["Author A", "Author B", "Author C", "Author D", "Author E"],
            "suggested_by": ["Alice", "Bob", "Alice", None, "Carol"],
            "original_publication_year": [2000, 2010, None, 2015, 2020],
            "number_of_pages": [300, 400, None, 350, 280],
            "average_goodreads_rating": [4.0, 3.8, 4.2, 3.5, 4.1],
            "average_bookclub_rating": [4.5, 4.0, 3.8, None, 4.2],
            "Alice": [5.0, 4.0, 4.0, 3.0, 4.0],
            "Bob": [4.0, 4.5, None, 4.0, 5.0],
            "Carol": [4.0, 3.5, 4.5, None, 4.0],
        }
    )


class TestCurrentMeeting:
    """Tests for current_meeting function."""

    def test_upcoming_meeting(self, sample_data: pl.DataFrame) -> None:
        """Test that the first meeting on or after today is picked."""
        meeting = current_meeting(sample_data, date(2024, 1, 1))
        assert meeting["date"].to_list() == [date(2024, 1, 15)]

    def test_only_past_meetings(self, sample_data: pl.DataFrame) -> None:
        """Test that the last meeting is picked when every meeting is in the past."""
        meeting = current_meeting(sample_data, date(2025, 1, 1))
        assert meeting["date"].to_list() == [date(2024, 4, 5)]

    def test_multiple_books_same_date(self, sample_data: pl.DataFrame) -> None:
        """Test that every book of the meeting is returned."""
        meeting = current_meeting(sample_data, date(2024, 3, 1))
        assert meeting["title"].to_list() == ["Book C", "Book D"]


class TestRankBooks:
    """Tests for rank_books function."""

    def test_ranked_by_club_rating(self, sample_data: pl.DataFrame) -> None:
        """Test that books are ranked by club rating."""
        ranked = rank_books(sample_data)
        # First should be highest rated
        assert ranked["rank"].to_list()[0] == 1

    def test_unrated_books_last(self, sample_data: pl.DataFrame) -> None:
        """Test that unrated books appear last."""
        ranked = rank_books(sample_data)
        unrated = ranked.filter(pl.col("average_bookclub_rating").is_null())
        assert len(unrated) == 1
        assert unrated["rank"][0] is None

    def test_ties_use_min_rank(self) -> None:
        """Test that ties use min rank (no skipping)."""
        data = pl.DataFrame(
            {
                "index": [1, 2, 3],
                "title": ["A", "B", "C"],
                "author": ["A", "B", "C"],
                "average_bookclub_rating": [4.0, 4.0, 3.0],
            }
        )
        ranked = rank_books(data)
        # Both 4.0 should have rank 1
        top_two = ranked.filter(pl.col("average_bookclub_rating") == 4.0)
        assert all(r == 1 for r in top_two["rank"].to_list())


class TestRatingTrend:
    """Tests for rating_trend function."""

    def test_fewer_than_two_rated_books(self) -> None:
        """Test with fewer than 2 rated books."""
        data = pl.DataFrame(
            {
                "date": [date(2024, 1, 1)],
                "title": ["A"],
                "average_bookclub_rating": [4.0],
            }
        )
        trend = rating_trend(data)
        assert trend["trend"][0] is None

    def test_rolling_average_computed(self, sample_data: pl.DataFrame) -> None:
        """Test that rolling average is computed."""
        trend = rating_trend(sample_data)
        assert "rolling_avg" in trend.columns
        assert trend["rolling_avg"][0] is not None


class TestMemberCorrelations:
    """Tests for member_correlations function."""

    def test_no_variance_gives_none(self) -> None:
        """Test that pairs with no variance return None."""
        data = pl.DataFrame(
            {
                "Alice": [4.0, 4.0, 4.0],  # No variance
                "Bob": [3.0, 4.0, 5.0],  # Has variance
            }
        )
        result = member_correlations(data, ["Alice", "Bob"], min_ratings=1, min_shared=2)
        # No valid pairs since Alice has no variance
        assert result.is_empty()

    def test_insufficient_shared_books(self) -> None:
        """Test that pairs with few shared books are excluded."""
        data = pl.DataFrame(
            {
                "Alice": [4.0, None, 5.0],
                "Bob": [None, 4.0, 5.0],
            }
        )
        result = member_correlations(data, ["Alice", "Bob"], min_ratings=1, min_shared=3)
        # Only 1 shared book, need at least 3
        assert result.is_empty()


class TestSuggesterStats:
    """Tests for suggester_stats function."""

    def test_active_member_rule(self, sample_data: pl.DataFrame) -> None:
        """Test that active members are included even with < 3 books."""
        result = suggester_stats(sample_data, ["Alice"], min_books=3)
        # Alice should be included as an active member
        assert any(r["suggested_by"] == "Alice" for r in result.to_dicts())
