"""Advanced Analytics page of the Sci-Fi Book Club Analytics Dashboard."""

import streamlit as st

from scifi.analysis import member_correlations
from scifi.members import BookClubMembers
from scifi.pipeline import process_bookclub_data
from scifi.visualizer import (
    create_club_vs_goodreads_discrepancies,
    create_correlation_heatmap,
    create_polarizing_books_analysis,
)


def render() -> None:
    """Render the Advanced Analytics page."""
    bookclub_processed_df = process_bookclub_data()
    members = BookClubMembers.get_member_names()

    st.subheader("📊 Correlation Analysis")
    st.write("How similar are member tastes?")

    correlations = member_correlations(bookclub_processed_df, members)
    if correlations.is_empty():
        st.warning("Not enough members with 5+ ratings to create correlation analysis.")
    else:
        st.plotly_chart(create_correlation_heatmap(correlations))

    st.markdown("---")
    st.subheader("🤯 Most Polarizing Books")
    st.write("Books with the highest rating standard deviation - where members disagreed the most.")

    fig_polarizing = create_polarizing_books_analysis(bookclub_processed_df, members)
    st.plotly_chart(fig_polarizing)

    st.markdown("---")
    st.subheader("🎯 Club vs Goodreads Discrepancies")
    st.write("Books where our club ratings differ most from the general Goodreads community.")

    fig_discrepancies = create_club_vs_goodreads_discrepancies(bookclub_processed_df)
    st.plotly_chart(fig_discrepancies)
