"""Member Insights page of the Sci-Fi Book Club Analytics Dashboard."""

import polars as pl
import streamlit as st

from scifi.analysis import suggester_stats
from scifi.members import BookClubMembers
from scifi.pipeline import process_bookclub_data
from scifi.visualizer import (
    create_member_average_bar,
    create_member_count_bar,
    create_member_rating_heatmap,
    create_suggester_box_plot,
)


def render() -> None:
    """Render the Member Insights page."""
    bookclub_processed_df = process_bookclub_data()
    members = BookClubMembers.get_member_names()

    # Add member rating heatmap at the top
    fig_heatmap = create_member_rating_heatmap(bookclub_processed_df, members)
    st.plotly_chart(fig_heatmap)

    _create_member_comparison(bookclub_processed_df, members)

    # Add suggester violin plot
    st.markdown("---")
    _create_suggester_analysis(bookclub_processed_df)


def _create_member_comparison(df: pl.DataFrame, members: list[str]) -> None:
    """Create member rating comparison.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.
    members : list[str]
        List of member names.
    """
    st.subheader("👥 Member Rating Patterns")

    # Calculate member statistics
    stats_df = (
        df.select(members)
        .unpivot(variable_name="Member", value_name="rating")
        .drop_nulls("rating")
        .group_by("Member", maintain_order=True)
        .agg(
            pl.len().alias("Count"),
            pl.col("rating").mean().alias("Average"),
        )
    )

    # Create clean comparison charts
    col1, col2 = st.columns(2)

    with col1:
        # Rating counts
        fig_counts = create_member_count_bar(stats_df)
        st.plotly_chart(fig_counts)

    with col2:
        # Average ratings
        fig_avg = create_member_average_bar(stats_df)
        st.plotly_chart(fig_avg)


def _create_suggester_analysis(df: pl.DataFrame) -> None:
    """Create jitter box plot showing ratings by book suggester.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.
    """
    st.subheader("🎯 Ratings by Book Suggester")
    st.write(
        "Distribution of average club ratings for books suggested by members "
        "(3+ books or active members)"
    )

    # Get active member names from BookClubMembers
    active_member_names = [member.name for member in BookClubMembers.get_active_members()]

    # Calculate average ratings per suggester using analysis function
    stats_result = suggester_stats(df, active_member_names)

    if stats_result.is_empty():
        st.warning("No members meet the criteria (3+ books or active members).")
        return

    # Create the jitter box plot
    fig = create_suggester_box_plot(df, stats_result)

    # Box plot and the stats table side by side
    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(fig)

    with col2:
        # Simple stats display
        st.subheader("📈 Suggester Statistics")
        st.dataframe(
            stats_result,
            hide_index=True,
            column_config={
                "suggested_by": "Suggester",
                "book_count": "Books",
                "avg_rating": st.column_config.NumberColumn("Avg Rating", format="%.2f"),
            },
        )
