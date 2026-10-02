"""Time Analysis page of the Sci-Fi Book Club Analytics Dashboard."""

import polars as pl
import streamlit as st

from scifi.analysis import books_per_decade, books_per_year, rating_trend
from scifi.ui.data import get_bookclub
from scifi.visualizer import (
    create_books_per_decade_bar,
    create_books_per_year_bar,
    create_rating_scatter,
    create_rating_trend_chart,
)


def render() -> None:
    """Render the Time Analysis page."""
    bookclub_processed_df = get_bookclub()

    # First show the time analysis with bar charts
    _create_time_analysis(bookclub_processed_df)

    # Then show the two main charts side by side
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📚 Goodreads vs Club Ratings")
        st.write(
            "Points above the diagonal line indicate books we rated higher than Goodreads users."
        )
        fig = create_rating_scatter(bookclub_processed_df)
        st.plotly_chart(fig, width="stretch", key="overview_scatter")

    with col2:
        st.subheader("📈 Rating Trends Over Time")
        st.write("The orange line shows a 7-book moving average of club ratings.")
        _create_rating_trends_chart(bookclub_processed_df)


def _create_time_analysis(df: pl.DataFrame) -> None:
    """Create time-based analysis.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.
    """
    st.subheader("📅 Reading Journey Over Time")

    col1, col2 = st.columns(2)

    with col1:
        # Books per year
        yearly_counts = books_per_year(df)
        fig_yearly = create_books_per_year_bar(yearly_counts)
        st.plotly_chart(fig_yearly, width="stretch")

    with col2:
        # Publication decades with outlined bars
        decade_counts = books_per_decade(df)
        fig_decades = create_books_per_decade_bar(decade_counts)
        st.plotly_chart(fig_decades, width="stretch")


def _create_rating_trends_chart(df: pl.DataFrame) -> None:
    """Create rating trends over time chart.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.
    """
    # Get trend data from analysis
    trend_data = rating_trend(df)
    fig_trend = create_rating_trend_chart(trend_data)
    st.plotly_chart(fig_trend, width="stretch")
