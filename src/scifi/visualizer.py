"""Visualization functions for the scifi project."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st


def rating_to_color(rating: float, alpha: float = 0.3) -> str:
    """Convert a rating to an RGBA color string.

    Parameters
    ----------
    rating : float
        The rating to convert, expected to be in the range 1-5.
    alpha : float, optional
        The alpha value for the color, by default 0.3

    Returns
    -------
    str
        The RGBA color string.
    """
    # Normalize rating from 1-5 to 0-1
    normalized = (rating - 1) / 4
    normalized = np.clip(normalized, 0, 1)

    # Interpolate between red and green
    red = int(255 * (1 - normalized))
    green = int(255 * normalized)
    blue = 0

    return f"rgba({red}, {green}, {blue}, {alpha})"


def create_voting_text(bookclub_members_list: list[str], row: dict[str, float]) -> str:
    """Create a summary of voting members and their ratings.

    Parameters
    ----------
    bookclub_members_list : list[str]
        List of member names who voted.
    row : dict[str, float]
        A dictionary containing member ratings.

    Returns
    -------
    str
        A formatted string listing the voting members and their ratings.
    """
    voters = []
    for member in bookclub_members_list:
        value = row.get(member)
        if value is not None and value != 0:
            voters.append(f"{member}: {value:.1f}")
    return "<br>".join(voters)


# --- Load Data ---
df = pl.read_csv("data/processed_data.csv", try_parse_dates=True)

# --- Clean/Prep ---
member_cols = ["Robert", "Dion", "Peter", "Thirsa", "Koen_v_W", "Koen_M", "Thomas", "Marloes"]

# Replace missing member ratings with None for correct matrix behavior
df = df.with_columns([pl.col(col).cast(pl.Float64) for col in member_cols])

# --- Member Rating Heatmap ---
rating_values = df.select(member_cols).to_numpy().T
fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=rating_values,
        x=[f"Book {i + 1}" for i in range(rating_values.shape[1])],
        y=member_cols,
        colorscale="RdBu",
        colorbar={"title": "Rating"},
    )
)
fig_heatmap.update_layout(title="🤝 Member Rating Heatmap")

# --- Member Alignment Matrix (Correlation) ---
matrix = df.select(member_cols).to_pandas().corr()
fig_corr = px.imshow(
    matrix, text_auto=True, color_continuous_scale="YlGnBu", title="💬 Member Alignment Matrix"
)

# --- Sorted Discrepancies: Club - Goodreads ---
df = df.with_columns(
    [(pl.col("average_bookclub_rating") - pl.col("average_goodreads_rating")).alias("rating_diff")]
)

sorted_diff = df.select(["title", "rating_diff"]).drop_nulls().sort("rating_diff")
fig_diff = px.bar(
    sorted_diff.to_pandas(),
    x="rating_diff",
    y="title",
    orientation="h",
    color="rating_diff",
    color_continuous_scale="RdBu",
    title="🎯 Club vs Goodreads: Sorted Discrepancies",
)
fig_diff.update_layout(yaxis_title="Book Title", xaxis_title="Club - Goodreads")

# --- Most and Least Polarizing Books ---
stds = df.select([pl.std(col).alias(col) for col in member_cols]).row(0)
# Filter out None values before calculating standard deviation
stds_filtered = [std for std in stds if std is not None]
df = df.with_columns(pl.lit(np.std(stds_filtered)).alias("rating_std"))

# Polarizing books via row-wise std
df = df.with_columns(
    [
        pl.concat_list(member_cols)
        .list.eval(pl.element().cast(pl.Float64))
        .list.std()
        .alias("rating_std")
    ]
)
polarizing = df.select(["title", "rating_std"]).drop_nulls().sort("rating_std", descending=True)

fig_polar = px.bar(
    polarizing.head(10).to_pandas(),
    x="rating_std",
    y="title",
    orientation="h",
    color="rating_std",
    color_continuous_scale="Agsunset",
    title="🤯 Most Polarizing Books",
)
fig_polar.update_layout(yaxis_title="Book Title", xaxis_title="Standard Deviation of Ratings")

# --- Streamlit App Layout ---
st.set_page_config(page_title="Book Club Dashboard", layout="wide")
st.title("📖 Book Club Insights")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.plotly_chart(fig_diff, use_container_width=True)
with col2:
    st.plotly_chart(fig_corr, use_container_width=True)
    st.plotly_chart(fig_polar, use_container_width=True)
