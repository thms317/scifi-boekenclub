"""Author Insights page of the Sci-Fi Book Club Analytics Dashboard."""

import polars as pl
import streamlit as st

from scifi.analysis import author_stats
from scifi.ui.data import get_bookclub
from scifi.visualizer import create_author_bar_chart


def render() -> None:
    """Render the Author Insights page."""
    bookclub_processed_df = get_bookclub()

    st.subheader("✍️ Who Are We Reading?")
    st.write(
        "Author background for every book we read, one row per author in "
        "data/bookclub/authors.csv. LGBTQ+ only counts what is public; ethnicity is the "
        "club's judgement from public biographies."
    )

    dimensions = {
        "Gender": "gender",
        "Country": "country",
        "Religion": "religion",
        "LGBTQ+": "lgbtq",
        "Ethnicity": "ethnicity",
    }

    dimension = st.radio("Group authors by:", list(dimensions), horizontal=True)
    group_col = dimensions[dimension]

    stats_result = author_stats(bookclub_processed_df, group_col)

    if stats_result is None or len(stats_result) == 0:
        st.info(f"No data available for {dimension}.")
        return

    col1, col2 = st.columns(2)
    book_count_max = float(stats_result.select(pl.col("book_count").max()).item())
    with col1:
        st.markdown("**📚 Books read**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_result,
                "book_count",
                "Number of books",
                x_max=book_count_max * 1.15,
                decimals=0,
            ),
            width="stretch",
        )
    with col2:
        st.markdown("**⭐ Average club rating**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_result, "avg_rating", "Average club rating (1-5)", x_max=5.6, decimals=2
            ),
            width="stretch",
        )
    st.caption(
        "Groups with only one or two books say little about taste; hover for counts. "
        "'onbekend' means unknown, not a default."
    )

    st.markdown("---")
    st.subheader("📋 Author Details per Book")
    author_details = bookclub_processed_df.sort("date", descending=True).select(
        "title",
        "author",
        "date",
        *dimensions.values(),
        pl.col("average_bookclub_rating").round(2),
    )
    st.dataframe(
        author_details,
        width="stretch",
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title", width="large"),
            "author": st.column_config.TextColumn("Author", width="medium"),
            "date": st.column_config.DateColumn("Read on", format="MMM DD, YYYY"),
            **{col: label for label, col in dimensions.items()},
            "average_bookclub_rating": st.column_config.NumberColumn("Club", format="%.2f"),
        },
    )
