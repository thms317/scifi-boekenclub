"""Advanced Analytics page of the Sci-Fi Book Club Analytics Dashboard."""

import streamlit as st

from scifi.analysis import member_correlations
from scifi.data_processor import load_dashboard_data
from scifi.members import BookClubMembers
from scifi.visualizer import (
    create_club_vs_goodreads_discrepancies,
    create_correlation_heatmap,
    create_polarizing_books_analysis,
)


def render() -> None:
    """Render the Advanced Analytics page."""
    bookclub_processed_df = load_dashboard_data()
    members = BookClubMembers.get_member_names()

    # CORRELATION ANALYSIS SECTION
    st.markdown("### 📊 Correlation Analysis")
    st.write("How similar are member tastes?")

    # Get member correlations using analysis function
    correlations = member_correlations(bookclub_processed_df, members)

    if correlations is None:
        st.warning("Not enough members with 5+ ratings to create correlation analysis.")
    else:
        # Create enhanced heatmap
        fig = create_correlation_heatmap(correlations)

        # Display correlation plot
        st.plotly_chart(fig, key="correlation_heatmap")

    # Section 1: Most Polarizing Books
    st.markdown("---")
    st.subheader("🤯 Most Polarizing Books")
    st.write("Books with the highest rating standard deviation - where members disagreed the most.")

    fig_polarizing = create_polarizing_books_analysis(bookclub_processed_df, members)
    st.plotly_chart(fig_polarizing)

    # Section 2: Club vs Goodreads Discrepancies
    st.markdown("---")
    st.subheader("🎯 Club vs Goodreads Discrepancies")
    st.write("Books where our club ratings differ most from the general Goodreads community.")

    fig_discrepancies = create_club_vs_goodreads_discrepancies(bookclub_processed_df)
    st.plotly_chart(fig_discrepancies)
