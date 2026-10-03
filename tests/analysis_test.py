"""Tests for analysis module functions."""

from datetime import date, timedelta

import polars as pl
import pytest

from scifi.analysis import (
    Book,
    books_per_decade,
    club_duration_label,
    countdown_label,
    current_meeting,
    member_correlations,
    member_stats,
    overview_metrics,
    past_books,
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


class TestCountdownLabel:
    """Tests for countdown_label function."""

    def test_today(self) -> None:
        """Test label for today."""
        today = date.today()
        label = countdown_label(today, today)
        assert "(TODAY)" in label

    def test_tomorrow(self) -> None:
        """Test label for tomorrow."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        label = countdown_label(tomorrow, today)
        assert "(TOMORROW)" in label

    def test_future_date(self) -> None:
        """Test label for a future date."""
        today = date.today()
        future = today + timedelta(days=10)
        label = countdown_label(future, today)
        assert "10 days left" in label

    def test_past_date(self) -> None:
        """Test label for a past date."""
        today = date.today()
        past = today - timedelta(days=5)
        label = countdown_label(past, today)
        assert "5 days ago" in label


class TestClubDurationLabel:
    """Tests for club_duration_label function."""

    def test_less_than_a_year(self) -> None:
        """Test duration under one year."""
        first = date(2024, 1, 1)
        last = date(2024, 7, 15)
        label = club_duration_label(first, last)
        assert "m" in label
        assert "y" not in label

    def test_more_than_a_year(self) -> None:
        """Test duration over one year."""
        first = date(2022, 1, 1)
        last = date(2024, 7, 15)
        label = club_duration_label(first, last)
        assert "y" in label
        assert "m" in label


class TestCurrentMeeting:
    """Tests for current_meeting function."""

    def test_upcoming_meeting(self, sample_data: pl.DataFrame) -> None:
        """Test finding an upcoming meeting."""
        today = date(2024, 1, 1)
        meeting = current_meeting(sample_data, today)
        assert meeting is not None
        assert meeting.is_upcoming
        assert meeting.date == date(2024, 1, 15)

    def test_only_past_meetings(self, sample_data: pl.DataFrame) -> None:
        """Test when only past meetings exist."""
        today = date(2025, 1, 1)
        meeting = current_meeting(sample_data, today)
        assert meeting is not None
        assert not meeting.is_upcoming
        assert meeting.date == date(2024, 4, 5)

    def test_multiple_books_same_date(self, sample_data: pl.DataFrame) -> None:
        """Test meeting with multiple books on same date."""
        today = date(2024, 3, 1)
        meeting = current_meeting(sample_data, today)
        assert meeting is not None
        assert meeting.date == date(2024, 3, 20)
        assert len(meeting.books) == 2
        assert all(isinstance(b, Book) for b in meeting.books)

    def test_empty_frame(self) -> None:
        """Test with empty DataFrame."""
        empty = pl.DataFrame({"date": pl.Series([], dtype=pl.Date)})
        result = current_meeting(empty, date.today())
        assert result is None


class TestPastBooks:
    """Tests for past_books function."""

    def test_returns_past_books(self, sample_data: pl.DataFrame) -> None:
        """Test that past books are returned."""
        today = date(2024, 3, 15)
        past = past_books(sample_data, today)
        assert len(past) > 0
        assert all(d < today for d in past["date"].to_list())

    def test_all_books_if_no_past(self, sample_data: pl.DataFrame) -> None:
        """Test that all books are returned if none are past."""
        today = date(2020, 1, 1)
        result = past_books(sample_data, today)
        assert len(result) == len(sample_data)


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


class TestMemberStats:
    """Tests for member_stats function."""

    def test_counts_ratings(self, sample_data: pl.DataFrame) -> None:
        """Test that ratings are counted correctly."""
        members = ["Alice", "Bob", "Carol"]
        stats = member_stats(sample_data, members)
        alice_stats = stats.filter(pl.col("member") == "Alice").to_dicts()[0]
        assert alice_stats["count"] == 5

    def test_skips_nulls(self, sample_data: pl.DataFrame) -> None:
        """Test that nulls are skipped in calculations."""
        members = ["Bob"]
        stats = member_stats(sample_data, members)
        bob_stats = stats.to_dicts()[0]
        # Bob has one null, so count should be 4, not 5
        assert bob_stats["count"] == 4


class TestBooksPerDecade:
    """Tests for books_per_decade function."""

    def test_handles_null_years(self, sample_data: pl.DataFrame) -> None:
        """Test that books with null publication year are filtered."""
        result = books_per_decade(sample_data)
        # Should exclude the one with null year
        assert result["count"].sum() == 4


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
        assert result is None or len(result) == 0

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
        assert result is None or len(result) == 0


class TestSuggesterStats:
    """Tests for suggester_stats function."""

    def test_active_member_rule(self, sample_data: pl.DataFrame) -> None:
        """Test that active members are included even with < 3 books."""
        result = suggester_stats(sample_data, ["Alice"], min_books=3)
        # Alice should be included as an active member
        assert any(r["suggested_by"] == "Alice" for r in result.to_dicts())


class TestOverviewMetrics:
    """Tests for overview_metrics function."""

    def test_computes_all_metrics(self, sample_data: pl.DataFrame) -> None:
        """Test that all metrics are computed."""
        members = ["Alice", "Bob", "Carol"]
        metrics = overview_metrics(sample_data, members)

        assert metrics.total_books == 5
        assert metrics.goodreads_avg > 0
        assert metrics.club_avg > 0
        assert metrics.most_active_member in members
        assert isinstance(metrics.first_date, date)
        assert isinstance(metrics.last_date, date)
