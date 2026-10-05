"""Time Analysis page of the Sci-Fi Book Club Analytics Dashboard."""

import polars as pl
import streamlit as st

from scifi.analysis import rating_trend
from scifi.data_processor import load_dashboard_data
from scifi.visualizer import (
    create_books_per_decade_bar,
    create_books_per_year_bar,
    create_rating_scatter,
    create_rating_trend_chart,
)


def render() -> None:
    """Render the Time Analysis page."""
    bookclub_processed_df = load_dashboard_data()

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
        fig_trend = create_rating_trend_chart(rating_trend(bookclub_processed_df))
        st.plotly_chart(fig_trend, width="stretch")


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
        yearly_counts = (
            df.group_by(pl.col("date").dt.year().alias("year")).len("count").sort("year")
        )
        fig_yearly = create_books_per_year_bar(yearly_counts)
        st.plotly_chart(fig_yearly, width="stretch")

    with col2:
        # Publication decades with outlined bars
        decade_counts = (
            df.drop_nulls("original_publication_year")
            .group_by(decade=(pl.col("original_publication_year") // 10 * 10).cast(pl.UInt32))
            .len("count")
            .with_columns(decade_label=pl.col("decade").cast(pl.Utf8) + "s")
            .sort("decade")
        )
        fig_decades = create_books_per_decade_bar(decade_counts)
        st.plotly_chart(fig_decades, width="stretch")
