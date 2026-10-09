"""Author Insights page of the Sci-Fi Book Club Analytics Dashboard."""

import polars as pl
import streamlit as st

from scifi.data_processor import load_dashboard_data
from scifi.visualizer import create_author_bar_chart


def render() -> None:
    """Render the Author Insights page."""
    bookclub_processed_df = load_dashboard_data()

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

    stats_result = (
        bookclub_processed_df.drop_nulls("average_bookclub_rating")
        .group_by(pl.col(group_col).alias("group"))
        .agg(
            pl.len().alias("book_count"),
            pl.col("average_bookclub_rating").mean().alias("avg_rating"),
        )
        .sort("avg_rating", descending=True)
    )

    if len(stats_result) == 0:
        st.info(f"No data available for {dimension}.")
        return

    col1, col2 = st.columns(2)
    book_count_max = float(stats_result["book_count"].max())
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
        )
    with col2:
        st.markdown("**⭐ Average club rating**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_result, "avg_rating", "Average club rating (1-5)", x_max=5.6, decimals=2
            ),
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
        "average_bookclub_rating",
    )
    st.dataframe(
        author_details,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title", width="large"),
            "author": st.column_config.TextColumn("Author", width="medium"),
            "date": st.column_config.DateColumn("Read on", format="MMM DD, YYYY"),
            **{col: label for label, col in dimensions.items()},
            "average_bookclub_rating": st.column_config.NumberColumn("Club", format="%.2f"),
        },
    )
