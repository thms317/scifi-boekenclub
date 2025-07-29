"""Visualization functions for the scifi project."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl


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


def create_member_rating_heatmap(df: pl.DataFrame, member_cols: list[str]) -> go.Figure:
    """Create a heatmap showing member ratings across all books.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data containing member rating columns.
    member_cols : list[str]
        List of column names representing club members.

    Returns
    -------
    go.Figure
        A Plotly heatmap figure showing member ratings.
    """
    # Ensure member columns are cast to Float64 for proper matrix behavior
    df_processed = df.with_columns([pl.col(col).cast(pl.Float64) for col in member_cols])

    rating_values = df_processed.select(member_cols).to_numpy().T
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
    return fig_heatmap


def create_member_alignment_matrix(df: pl.DataFrame, member_cols: list[str]) -> go.Figure:
    """Create a correlation matrix showing member rating alignment.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data containing member rating columns.
    member_cols : list[str]
        List of column names representing club members.

    Returns
    -------
    go.Figure
        A Plotly imshow figure showing member rating correlations.
    """
    matrix = df.select(member_cols).to_pandas().corr()
    return px.imshow(
        matrix, text_auto=True, color_continuous_scale="YlGnBu", title="💬 Member Alignment Matrix"
    )


def create_club_vs_goodreads_discrepancies(df: pl.DataFrame) -> go.Figure:
    """Create a horizontal bar chart showing club vs Goodreads rating differences.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data containing average_bookclub_rating and
        average_goodreads_rating columns.

    Returns
    -------
    go.Figure
        A Plotly bar chart showing rating discrepancies sorted from lowest to highest.
    """
    df_with_diff = df.with_columns(
        [
            (pl.col("average_bookclub_rating") - pl.col("average_goodreads_rating")).alias(
                "rating_diff"
            )
        ]
    )

    sorted_diff = df_with_diff.select(["title", "rating_diff"]).drop_nulls().sort("rating_diff")
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
    return fig_diff


def create_polarizing_books_analysis(df: pl.DataFrame, member_cols: list[str]) -> go.Figure:
    """Create a bar chart showing the most polarizing books by rating standard deviation.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data containing member rating columns.
    member_cols : list[str]
        List of column names representing club members.

    Returns
    -------
    go.Figure
        A Plotly bar chart showing the top 10 most polarizing books.
    """
    # Calculate row-wise standard deviation for each book
    df_with_std = df.with_columns(
        [
            pl.concat_list(member_cols)
            .list.eval(pl.element().cast(pl.Float64))
            .list.std()
            .alias("rating_std")
        ]
    )

    polarizing = (
        df_with_std.select(["title", "rating_std"]).drop_nulls().sort("rating_std", descending=True)
    )

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
    return fig_polar
