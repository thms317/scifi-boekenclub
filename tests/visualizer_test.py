"""Tests for the visualizer module."""

from datetime import date

import plotly.graph_objects as go
import polars as pl
import pytest

from scifi.visualizer import (
    create_author_bar_chart,
    create_books_per_decade_bar,
    create_books_per_year_bar,
    create_club_vs_goodreads_discrepancies,
    create_correlation_heatmap,
    create_member_average_bar,
    create_member_count_bar,
    create_member_radar,
    create_rating_comparison_bar,
    create_rating_scatter,
    create_rating_trend_chart,
    create_suggester_box_plot,
)


@pytest.fixture
def sample_df() -> pl.DataFrame:
    """Create a small sample dataframe for testing."""
    return pl.DataFrame(
        {
            "index": [1, 2, 3],
            "title": ["Book A", "Book B", "Book C"],
            "author": ["Author A", "Author B", "Author C"],
            "date": [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)],
            "suggested_by": ["Member1", "Member2", "Member1"],
            "original_publication_year": [2020, 2021, 2022],
            "average_goodreads_rating": [4.0, 3.5, 4.5],
            "average_bookclub_rating": [4.2, 3.8, 4.7],
            "Member1": [4.0, None, 4.5],
            "Member2": [4.5, 3.5, 4.9],
            "location": ["NYC", "LA", "SF"],
        }
    )


@pytest.fixture
def sample_stats_df() -> pl.DataFrame:
    """Create a small sample stats dataframe."""
    return pl.DataFrame(
        {
            "Member": ["Member1", "Member2"],
            "Count": [2, 3],
            "Average": [4.25, 4.1],
            "Std Dev": [0.25, 0.6],
            "Min": [4.0, 3.5],
            "Max": [4.5, 4.9],
        }
    )


class TestCreateRatingScatter:
    """Tests for create_rating_scatter."""

    def test_returns_figure(self, sample_df: pl.DataFrame) -> None:
        """Test that create_rating_scatter returns a go.Figure."""
        fig = create_rating_scatter(sample_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateRatingComparisonBar:
    """Tests for create_rating_comparison_bar."""

    def test_returns_figure(self) -> None:
        """Test that create_rating_comparison_bar returns a go.Figure."""
        book_data = {
            "average_goodreads_rating": 4.0,
            "average_bookclub_rating": 4.5,
        }
        fig = create_rating_comparison_bar(book_data)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateMemberRadar:
    """Tests for create_member_radar."""

    def test_returns_figure_with_ratings(self) -> None:
        """Test that create_member_radar returns a go.Figure with ratings."""
        members = ["Member1", "Member2"]
        member_ratings = {"Member1": 4.0, "Member2": 4.5}
        fig = create_member_radar(members, member_ratings, "Test Book")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_returns_figure_without_ratings(self) -> None:
        """Test that create_member_radar returns a go.Figure without ratings."""
        members = ["Member1", "Member2"]
        member_ratings = {"Member1": None, "Member2": None}
        fig = create_member_radar(members, member_ratings, "Test Book")
        assert isinstance(fig, go.Figure)


class TestCreateMemberCountBar:
    """Tests for create_member_count_bar."""

    def test_returns_figure(self, sample_stats_df: pl.DataFrame) -> None:
        """Test that create_member_count_bar returns a go.Figure."""
        fig = create_member_count_bar(sample_stats_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateMemberAverageBar:
    """Tests for create_member_average_bar."""

    def test_returns_figure(self, sample_stats_df: pl.DataFrame) -> None:
        """Test that create_member_average_bar returns a go.Figure."""
        fig = create_member_average_bar(sample_stats_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateBooksPerYearBar:
    """Tests for create_books_per_year_bar."""

    def test_returns_figure(self) -> None:
        """Test that create_books_per_year_bar returns a go.Figure."""
        yearly_df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "count": [1, 2, 3],
            }
        )
        fig = create_books_per_year_bar(yearly_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateBooksPerDecadeBar:
    """Tests for create_books_per_decade_bar."""

    def test_returns_figure(self) -> None:
        """Test that create_books_per_decade_bar returns a go.Figure."""
        decade_df = pl.DataFrame(
            {
                "decade_label": ["2010s", "2020s"],
                "count": [2, 1],
            }
        )
        fig = create_books_per_decade_bar(decade_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateRatingTrendChart:
    """Tests for create_rating_trend_chart."""

    def test_returns_figure(self) -> None:
        """Test that create_rating_trend_chart returns a go.Figure."""
        trend_df = pl.DataFrame(
            {
                "date": [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)],
                "title": ["Book A", "Book B", "Book C"],
                "average_bookclub_rating": [4.0, 4.5, 4.2],
                "rolling_avg": [4.0, 4.25, 4.35],
                "trend": [4.0, 4.1, 4.2],
            }
        )
        fig = create_rating_trend_chart(trend_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateSuggesterBoxPlot:
    """Tests for create_suggester_box_plot."""

    def test_returns_figure(self, sample_df: pl.DataFrame) -> None:
        """Test that create_suggester_box_plot returns a go.Figure."""
        stats_df = pl.DataFrame(
            {
                "suggested_by": ["Member1", "Member2"],
                "book_count": [2, 1],
                "avg_rating": [4.25, 3.8],
            }
        )
        fig = create_suggester_box_plot(sample_df, stats_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateAuthorBarChart:
    """Tests for create_author_bar_chart."""

    def test_returns_figure(self) -> None:
        """Test that create_author_bar_chart returns a go.Figure."""
        stats_df = pl.DataFrame(
            {
                "group": ["Fiction", "Non-Fiction"],
                "book_count": [5, 3],
                "avg_rating": [4.2, 3.8],
            }
        )
        fig = create_author_bar_chart(stats_df, "avg_rating", "Average Rating", 5.0, 2)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateCorrelationHeatmap:
    """Tests for create_correlation_heatmap."""

    def test_returns_figure(self) -> None:
        """Test that create_correlation_heatmap returns a go.Figure."""
        corr_df = pl.DataFrame(
            {
                "member_1": ["Member1", "Member1"],
                "member_2": ["Member2", "Member3"],
                "correlation": [0.8, 0.6],
                "shared_books": [3, 3],
            }
        )
        fig = create_correlation_heatmap(corr_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestCreateClubVsGoodreadsDiscrepancies:
    """Tests for create_club_vs_goodreads_discrepancies."""

    def test_returns_figure(self, sample_df: pl.DataFrame) -> None:
        """Test that create_club_vs_goodreads_discrepancies returns a go.Figure."""
        fig = create_club_vs_goodreads_discrepancies(sample_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
