"""Visualization functions for the scifi project."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl

from .members import BookClubMembers


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
    # Get ordered member names starting with Thirsa (index 0)
    all_members = BookClubMembers.get_all_members()
    ordered_member_names = [member.name for member in sorted(all_members, key=lambda x: x.index)]

    # Filter to only include members that are in member_cols and reverse order for display
    ordered_member_cols = [name for name in ordered_member_names if name in member_cols]
    reversed_member_cols = list(reversed(ordered_member_cols))  # Reverse so Thirsa is at top

    # Ensure member columns are cast to Float64 for proper matrix behavior
    df_processed = df.with_columns([pl.col(col).cast(pl.Float64) for col in reversed_member_cols])

    # Get book titles for hover text
    book_titles = df_processed.select("title").to_series().to_list()

    rating_values = df_processed.select(reversed_member_cols).to_numpy().T

    # Create custom hover text that handles null values
    hover_text = []
    for i, member in enumerate(reversed_member_cols):
        member_row = []
        for j, book_title in enumerate(book_titles):
            rating = rating_values[i, j]
            if np.isnan(rating):
                member_row.append(f"<b>{member}</b><br>Book: {book_title}<br>No rating")
            else:
                member_row.append(f"<b>{member}</b><br>Book: {book_title}<br>Rating: {rating:.1f}")
        hover_text.append(member_row)

    fig = go.Figure(
        data=go.Heatmap(
            z=rating_values,
            x=book_titles,
            y=reversed_member_cols,
            colorscale=[
                [0, "#d9f2d9"],
                [0.25, "#a8dba8"],
                [0.5, "#74c476"],
                [0.75, "#31a354"],
                [1, "#006d2c"],
            ],  # Darker light green for visibility
            showscale=False,  # Remove colorbar legend
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_text,
            zmin=1,  # Set minimum value to 1 to exclude nulls from color mapping
            zmax=5,  # Set maximum value to 5
        )
    )

    fig.update_layout(
        xaxis_title="",  # Remove x-axis label
        xaxis={
            "showticklabels": False,
            "showgrid": True,
            "gridcolor": "white",
            "gridwidth": 2,
        },  # Grid lines
        yaxis={
            "dtick": 1,
            "tickfont": {"size": 10},
            "showgrid": True,
            "gridcolor": "white",
            "gridwidth": 2,
        },  # Grid lines
        height=max(300, len(reversed_member_cols) * 40),  # Reduce height per member
        plot_bgcolor="white",
    )

    return fig


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
