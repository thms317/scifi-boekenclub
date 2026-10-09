"""Visualization functions for the scifi project."""

from collections.abc import Mapping

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
    normalized = min(max((rating - 1) / 4, 0), 1)

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
    # Reverse the members so the first one in member_cols is at the top
    reversed_member_cols = member_cols[::-1]
    book_titles = df["title"].to_list()

    # One row per member, one column per book; None where the member didn't rate the book
    rating_values = [df[member].to_list() for member in reversed_member_cols]

    # Create custom hover text that handles null values
    hover_text = [
        [
            f"<b>{member}</b><br>Book: {book_title}<br>"
            + ("No rating" if rating is None else f"Rating: {rating:.1f}")
            for book_title, rating in zip(book_titles, ratings, strict=True)
        ]
        for member, ratings in zip(reversed_member_cols, rating_values, strict=True)
    ]

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
        xaxis={
            "visible": False,  # Hide x-axis completely
        },
        yaxis={
            "dtick": 1,
            "tickfont": {"size": 10},
            "showgrid": True,
            "gridwidth": 2,
        },  # Grid lines
        height=max(150, len(reversed_member_cols) * 20),  # Even smaller height per member
        margin={"l": 0, "r": 0, "t": 20, "b": 0},  # Add small top padding
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
    sorted_diff = (
        df.select(
            "title",
            rating_diff=pl.col("average_bookclub_rating") - pl.col("average_goodreads_rating"),
        )
        .drop_nulls()
        .sort("rating_diff")
    )
    fig_diff = px.bar(
        sorted_diff,
        x="rating_diff",
        y="title",
        orientation="h",
        color="rating_diff",
        color_continuous_scale="RdBu",
        title="🎯 Club vs Goodreads: Sorted Discrepancies",
    )
    fig_diff.update_layout(yaxis_title="Book Title", xaxis_title="Club - Goodreads", height=800)
    # Update hover template to show 3 decimal places
    fig_diff.update_traces(hovertemplate="<b>%{y}</b><br>Discrepancy: %{x:.3f}<br><extra></extra>")
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
    polarizing = (
        df.select("title", rating_std=pl.concat_list(member_cols).list.std())
        .drop_nulls()
        .sort("rating_std", descending=True)
    )

    fig_polar = px.bar(
        polarizing.head(10),
        x="rating_std",
        y="title",
        orientation="h",
        color="rating_std",
        color_continuous_scale="Agsunset",
        title="🤯 Most Polarizing Books",
    )
    fig_polar.update_layout(
        yaxis_title="Book Title",
        xaxis_title="Standard Deviation of Ratings",
        yaxis={"categoryorder": "total ascending"},  # This will put highest values at top
    )
    # Update hover template to show 3 decimal places
    fig_polar.update_traces(
        hovertemplate="<b>%{y}</b><br>Rating Std Dev: %{x:.3f}<br><extra></extra>"
    )
    return fig_polar


def create_rating_scatter(df: pl.DataFrame) -> go.Figure:
    """Create scatter plot with trendline comparing Goodreads vs club ratings.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.

    Returns
    -------
    go.Figure
        A Plotly scatter figure with perfect agreement line.
    """
    # Prepare data for plotting - handle null values and filter out unrated books
    df_processed = df.with_columns(
        pl.col("original_publication_year").fill_null(0),
        pl.col("suggested_by").fill_null("Unknown"),
    ).filter(
        pl.col("average_bookclub_rating").is_not_null()
        & pl.col("average_goodreads_rating").is_not_null()
    )

    # Fixed axes 1-5 for both rating axes
    fig = px.scatter(
        df_processed,
        x="average_goodreads_rating",
        y="average_bookclub_rating",
        color="original_publication_year",
        size="average_goodreads_rating",
        hover_data=["title", "author", "suggested_by"],
        labels={
            "average_goodreads_rating": "Goodreads Rating",
            "average_bookclub_rating": "Club Rating",
            "original_publication_year": "Publication Year",
        },
        range_x=[1, 5],
        range_y=[1, 5],
        title="📚 Goodreads Rating vs Club Rating",
        size_max=20,
        height=525,
    )

    # Perfect agreement line (x=y from 1 to 5), behind the data
    fig.add_shape(
        type="line",
        x0=1,
        y0=1,
        x1=5,
        y1=5,
        line={"color": "black", "width": 2, "dash": "dash"},
        opacity=0.5,
        layer="below",
    )

    # Enhanced hover template - handle null values
    fig.update_traces(
        marker={"line": {"width": 1, "color": "white"}, "opacity": 0.8},
        hovertemplate="<b>%{customdata[0]}</b><br>"
        "Author: %{customdata[1]}<br>"
        "Suggested by: %{customdata[2]}<br>"
        "Goodreads Rating: %{x:.1f}<br>"
        "Club Rating: %{y:.1f}<br>"
        "<extra></extra>",
    )

    return fig


def create_rating_comparison_bar(
    book_data: dict,
) -> go.Figure:
    """Create a bar chart comparing Goodreads vs club rating for a book.

    Parameters
    ----------
    book_data : dict
        A dictionary with book rating data.

    Returns
    -------
    go.Figure
        A Plotly bar figure comparing ratings.
    """
    ratings = [book_data["average_goodreads_rating"], book_data["average_bookclub_rating"]]

    # If both ratings are None, show empty state
    if all(rating is None for rating in ratings):
        return go.Figure().add_annotation(text="No ratings available for this book")

    fig_comp = go.Figure(
        go.Bar(
            x=["Goodreads", "Our Club"],
            y=ratings,
            marker_color=["#FF6B6B", "#4ECDC4"],
            text=["-" if rating is None else f"{rating:.2f}" for rating in ratings],
            textposition="auto",
        )
    )

    fig_comp.update_layout(
        title="Rating Comparison",
        yaxis_title="Rating (1-5)",
        yaxis={"range": [0, 5]},
        height=350,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
    )
    return fig_comp


def create_member_radar(
    members: list[str], member_ratings: Mapping[str, float | None], book_title: str
) -> go.Figure:
    """Create a radar chart showing member ratings for a book.

    Parameters
    ----------
    members : list[str]
        List of member names.
    member_ratings : Mapping[str, float | None]
        Dictionary mapping member names to ratings (or None).
    book_title : str
        The title of the book.

    Returns
    -------
    go.Figure
        A Plotly radar figure.
    """
    # Filter to members with ratings
    rated = [member for member in members if member_ratings.get(member) is not None]

    if not rated:
        # Return an empty figure; the page shows a message instead
        return go.Figure()

    # Repeat the first point to close the shape
    fig_radar = go.Figure(
        go.Scatterpolar(
            r=[member_ratings[member] for member in [*rated, rated[0]]],
            theta=[*rated, rated[0]],
            fill="toself",
            name=book_title[:20] + "...",
            line_color="rgb(255, 195, 0)",
            fillcolor="rgba(255, 195, 0, 0.3)",
        )
    )

    fig_radar.update_layout(
        polar={
            "radialaxis": {"visible": True, "range": [0, 5]},
            "angularaxis": {"tickfont": {"size": 11}},
        },
        showlegend=False,
        height=400,
        margin={"l": 80, "r": 80, "t": 60, "b": 60},
    )
    return fig_radar


def create_member_count_bar(stats_df: pl.DataFrame) -> go.Figure:
    """Create a bar chart showing books rated by each member.

    Parameters
    ----------
    stats_df : pl.DataFrame
        DataFrame with member statistics including 'Member' and 'Count' columns.

    Returns
    -------
    go.Figure
        A Plotly bar figure.
    """
    return px.bar(
        stats_df,
        x="Member",
        y="Count",
        text_auto=True,
        color_discrete_sequence=["lightblue"],
        title="📊 Books Rated by Each Member",
        height=400,
    )


def create_member_average_bar(stats_df: pl.DataFrame) -> go.Figure:
    """Create a bar chart showing average rating by member.

    Parameters
    ----------
    stats_df : pl.DataFrame
        DataFrame with member statistics including 'Member' and 'Average' columns.

    Returns
    -------
    go.Figure
        A Plotly bar figure.
    """
    return px.bar(
        stats_df,
        x="Member",
        y="Average",
        text_auto=".2f",
        color_discrete_sequence=["lightcoral"],
        range_y=[0, 5],
        title="⭐ Average Rating by Member",
        height=400,
    )


def create_books_per_year_bar(yearly_df: pl.DataFrame) -> go.Figure:
    """Create a bar chart showing books read per year.

    Parameters
    ----------
    yearly_df : pl.DataFrame
        DataFrame with 'year' and 'count' columns.

    Returns
    -------
    go.Figure
        A Plotly bar figure.
    """
    return px.bar(
        yearly_df,
        x="year",
        y="count",
        text_auto=True,
        color_discrete_sequence=["skyblue"],
        labels={"year": "Year", "count": "Books"},
        title="📚 Books Read Per Year",
        height=400,
    )


def create_books_per_decade_bar(decade_df: pl.DataFrame) -> go.Figure:
    """Create a bar chart showing books by publication decade.

    Parameters
    ----------
    decade_df : pl.DataFrame
        DataFrame with 'decade_label' and 'count' columns.

    Returns
    -------
    go.Figure
        A Plotly bar figure.
    """
    return px.bar(
        decade_df,
        x="decade_label",
        y="count",
        text_auto=True,
        color_discrete_sequence=["lightgreen"],
        labels={"decade_label": "Publication Decade", "count": "Number of Books"},
        title="📖 Books by Publication Decade",
        height=400,
    ).update_traces(marker_line={"color": "darkgreen", "width": 2})


def create_rating_trend_chart(trend_df: pl.DataFrame) -> go.Figure:
    """Create a chart showing rating trends over time with rolling average.

    Parameters
    ----------
    trend_df : pl.DataFrame
        DataFrame with 'date', 'title', 'average_bookclub_rating', 'rolling_avg', and 'trend' columns.

    Returns
    -------
    go.Figure
        A Plotly figure with trend data.
    """
    fig_trend = go.Figure()

    # Linear trendline (background layer)
    valid_trend = trend_df.filter(pl.col("trend").is_not_null())
    if len(valid_trend) > 1:
        fig_trend.add_trace(
            go.Scatter(
                x=valid_trend["date"].to_list(),
                y=valid_trend["trend"].to_list(),
                mode="lines",
                name="Linear Trend",
                line={"color": "grey", "width": 1, "dash": "dash"},
            ),
        )

    # Individual points (rating_trend only returns books with ratings)
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["date"].to_list(),
            y=trend_df["average_bookclub_rating"].to_list(),
            mode="markers",
            name="Individual Ratings",
            marker={"color": "lightblue", "size": 6, "opacity": 0.6},
            hovertemplate="<b>%{customdata}</b><br>Rating: %{y}<br>Date: %{x}<extra></extra>",
            customdata=trend_df["title"].to_list(),
        ),
    )

    # 7-book moving average (foreground layer)
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["date"].to_list(),
            y=trend_df["rolling_avg"].to_list(),
            mode="lines",
            name="7-Book Moving Average",
            line={"color": "orange", "width": 3},
        ),
    )

    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Rating",
        yaxis={"range": [1, 5]},
        height=500,
        showlegend=False,
    )
    return fig_trend


def create_suggester_box_plot(df: pl.DataFrame, suggester_stats_df: pl.DataFrame) -> go.Figure:
    """Create a box plot showing rating distributions by book suggester.

    Parameters
    ----------
    df : pl.DataFrame
        The processed book club data.
    suggester_stats_df : pl.DataFrame
        DataFrame with suggester statistics.

    Returns
    -------
    go.Figure
        A Plotly box plot figure.
    """
    # Create the jitter box plot, one box per suggester (meeting criteria)
    fig = go.Figure()

    for suggester in suggester_stats_df["suggested_by"].to_list():
        suggester_books = df.filter(pl.col("suggested_by") == suggester)

        # Add stylized box plot with subtle design
        fig.add_trace(
            go.Box(
                x=[suggester] * len(suggester_books),
                y=suggester_books["average_bookclub_rating"].to_list(),
                name=suggester,
                boxpoints="all",  # Show all points with jitter
                jitter=0.4,  # Slightly more jitter for better spread
                pointpos=0,  # Center the points
                marker={
                    "size": 5,
                    "opacity": 0.6,
                },
                fillcolor="rgba(240, 240, 240, 0.3)",  # Very light gray fill
                boxmean=True,  # Show mean as well as median
                customdata=suggester_books.select("title", "author").rows(),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Author: %{customdata[1]}<br>"
                    "Rating: %{y:.2f}<br>"
                    f"Suggested by: {suggester}<br>"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.update_layout(
        xaxis_title="Book Suggester",
        yaxis_title="Average Club Rating",
        yaxis={
            "range": [1, 5],
            "gridwidth": 1,
        },
        xaxis={
            "tickangle": -45,
            "tickfont": {"size": 11},
        },
        height=600,
        margin={"l": 60, "r": 20, "t": 20, "b": 80},  # Better spacing
    )

    return fig


def create_author_bar_chart(
    stats_df: pl.DataFrame, value_col: str, x_title: str, x_max: float, decimals: int
) -> go.Figure:
    """Create a horizontal bar chart of one author statistic per group.

    Parameters
    ----------
    stats_df : pl.DataFrame
        DataFrame with author group statistics.
    value_col : str
        Name of the column to plot on x-axis.
    x_title : str
        Title for the x-axis.
    x_max : float
        Maximum value for x-axis range.
    decimals : int
        Number of decimal places for labels.

    Returns
    -------
    go.Figure
        A Plotly bar figure.
    """
    # Groups without ratings (e.g. only an unrated book) get a label instead of NaN
    value_col_list = stats_df[value_col].to_list()
    avg_rating_list = stats_df["avg_rating"].to_list()

    labels = [
        f"{value:.{decimals}f}" if value is not None else "no ratings" for value in value_col_list
    ]
    rating_labels = [
        f"{value:.2f}" if value is not None else "no ratings" for value in avg_rating_list
    ]

    fig = go.Figure(
        go.Bar(
            x=value_col_list,
            y=stats_df["group"].to_list(),
            orientation="h",
            customdata=list(zip(stats_df["book_count"].to_list(), rating_labels, strict=False)),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Books: %{customdata[0]}<br>"
                "Avg club rating: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
            text=labels,
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.update_layout(
        xaxis_title=x_title,
        yaxis={"autorange": "reversed", "tickfont": {"size": 11}},
        # Leave headroom so the value labels outside the bars are not clipped
        xaxis={"range": [0, x_max]},
        height=max(250, 40 * len(stats_df) + 80),
        margin={"l": 20, "r": 20, "t": 20, "b": 50},
        showlegend=False,
    )
    return fig


def create_correlation_heatmap(correlations_df: pl.DataFrame) -> go.Figure:
    """Create a heatmap showing correlation between member ratings.

    Parameters
    ----------
    correlations_df : pl.DataFrame
        Long-format correlation data with member_1, member_2, and correlation columns.

    Returns
    -------
    go.Figure
        A Plotly heatmap figure.
    """
    # Look up each pair both ways; pairs without a correlation count as 0
    pair_corr: dict[tuple[str, str], float] = {}
    for member_1, member_2, corr in correlations_df.select(
        "member_1", "member_2", "correlation"
    ).iter_rows():
        pair_corr[member_1, member_2] = pair_corr[member_2, member_1] = corr or 0.0
    active_members = sorted({member for pair in pair_corr for member in pair})

    # Reverse the rows so the diagonal starts top-left
    reversed_members = active_members[::-1]
    reversed_matrix = [
        [1.0 if row == col else pair_corr.get((row, col), 0.0) for col in active_members]
        for row in reversed_members
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=reversed_matrix,
            x=active_members,
            y=reversed_members,
            colorscale="RdYlGn",  # Red-Yellow-Green: Red=0, Yellow=0.5, Green=1
            zmin=-0.25,
            zmax=1,
            text=[[round(value, 3) for value in row] for row in reversed_matrix],
            texttemplate="%{text}",
            hoverongaps=False,
            hovertemplate="<b>%{y} vs %{x}</b><br>Correlation: %{z:.3f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=600,
        width=600,
        xaxis_title="Member",
        yaxis_title="Member",
        xaxis={"side": "bottom"},
    )

    return fig
