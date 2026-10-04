"""Pure analysis functions for the Sci-Fi Book Club dashboard.

All functions take Polars DataFrames and return DataFrames, dataclasses, or strings.
No Streamlit or Pandas dependencies.
"""

from dataclasses import dataclass
from datetime import date

import polars as pl


@dataclass
class Book:
    """A single book in the club."""

    title: str
    author: str
    year: int | None
    pages: int | None


@dataclass
class Meeting:
    """A single book club meeting."""

    date: date
    books: list[Book]
    days: int
    is_upcoming: bool


@dataclass
class OverviewMetrics:
    """Overview metrics for the dashboard."""

    total_books: int
    goodreads_avg: float
    club_avg: float
    most_active_member: str
    first_date: date
    last_date: date


def current_meeting(df: pl.DataFrame, today: date) -> Meeting | None:
    """Get the current or next meeting with all its books.

    Returns the first meeting on or after today, else the last meeting.
    Includes all books on that date.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    today : date
        Today's date.

    Returns
    -------
    Meeting | None
        The meeting details, or None if the frame is empty.
    """
    if len(df) == 0:
        return None

    # Convert to date type if needed
    dates_df = df.select("date").unique().sort("date")
    if len(dates_df) == 0:
        return None

    meeting_dates = dates_df["date"].to_list()

    # Find the first meeting on or after today, or the last one
    future_dates = [d for d in meeting_dates if d >= today]
    meeting_date = future_dates[0] if future_dates else meeting_dates[-1]
    is_upcoming = meeting_date >= today
    days_diff = abs((meeting_date - today).days)

    # Get all books on this date
    books_on_date = df.filter(pl.col("date") == meeting_date).sort("index")
    books = [
        Book(
            title=row["title"],
            author=row["author"],
            year=int(row["original_publication_year"])
            if row["original_publication_year"]
            else None,
            pages=int(row["number_of_pages"]) if row["number_of_pages"] else None,
        )
        for row in books_on_date.to_dicts()
    ]

    return Meeting(date=meeting_date, books=books, days=days_diff, is_upcoming=is_upcoming)


def countdown_label(meeting_date: date, today: date) -> str:
    """Create a countdown label for a meeting date.

    Parameters
    ----------
    meeting_date : date
        The meeting date.
    today : date
        Today's date.

    Returns
    -------
    str
        A label like "Oct 14 (TODAY)", "(TOMORROW)", "(N days left)" or "(N days ago)".
    """
    date_formatted = meeting_date.strftime("%b %d")
    days_diff = (meeting_date - today).days

    if days_diff == 0:
        return f"{date_formatted} (TODAY)"
    if days_diff == 1:
        return f"{date_formatted} (TOMORROW)"
    if days_diff > 0:
        return f"{date_formatted} ({days_diff} days left)"
    return f"{date_formatted} ({-days_diff} days ago)"


def club_duration_label(first: date, last: date) -> str:
    """Create a human-readable duration label.

    Parameters
    ----------
    first : date
        The first date.
    last : date
        The last date.

    Returns
    -------
    str
        A label like "3y 4m" or "7m".
    """
    duration = last - first
    years = duration.days // 365
    months = (duration.days % 365) // 30
    return f"{years}y {months}m" if years > 0 else f"{months}m"


def overview_metrics(df: pl.DataFrame, members: list[str]) -> OverviewMetrics:
    """Compute overview metrics for the dashboard.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    members : list[str]
        The list of club member names.

    Returns
    -------
    OverviewMetrics
        The computed metrics.
    """
    total_books = len(df)
    avg_goodreads = float(df.select(pl.col("average_goodreads_rating").mean()).item() or 0.0)
    avg_bookclub = float(df.select(pl.col("average_bookclub_rating").mean()).item() or 0.0)
    most_active = max(members, key=lambda m: df[m].count()) if members else ""

    first_date = df.select(pl.col("date").min()).item()
    last_date = df.select(pl.col("date").max()).item()

    return OverviewMetrics(
        total_books=total_books,
        goodreads_avg=avg_goodreads,
        club_avg=avg_bookclub,
        most_active_member=most_active,
        first_date=first_date,
        last_date=last_date,
    )


def past_books(df: pl.DataFrame, today: date) -> pl.DataFrame:
    """Get books read before today, or all books if none are past.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    today : date
        Today's date.

    Returns
    -------
    pl.DataFrame
        Books from before today (newest first), or all books if none match.
    """
    past = df.filter(pl.col("date") < today).sort("date", descending=True)
    return past if len(past) > 0 else df.sort("index", descending=True)


def rank_books(df: pl.DataFrame) -> pl.DataFrame:
    """Rank all books by club average rating.

    Uses min-rank: tied ratings get the same rank, and the next rank skips.
    Unrated books appear last with empty rank.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: index, title, author, average_bookclub_rating, rank, top_percent, out_of_rated.
    """
    # Count rated books
    rated = df.filter(pl.col("average_bookclub_rating").is_not_null())
    num_rated = len(rated)

    if num_rated == 0:
        # No rated books: return all with empty rank
        return df.select(["index", "title", "author", "average_bookclub_rating"]).with_columns(
            [
                pl.lit(None, dtype=pl.UInt32).alias("rank"),
                pl.lit(None, dtype=pl.UInt8).alias("top_percent"),
                pl.lit(0, dtype=pl.UInt32).alias("out_of_rated"),
            ]
        )

    # Rank the rated books
    ranked = (
        rated.with_columns(
            pl.col("average_bookclub_rating")
            .rank(method="min", descending=True)
            .cast(pl.UInt32)
            .alias("rank")
        )
        .with_columns(
            top_percent=((pl.col("rank") * 100 + num_rated - 1) // num_rated).cast(pl.UInt8),
        )
        .select(["index", "title", "author", "average_bookclub_rating", "rank", "top_percent"])
    )

    # Add unrated books with null rank
    unrated = (
        df.filter(pl.col("average_bookclub_rating").is_null())
        .select(["index", "title", "author", "average_bookclub_rating"])
        .with_columns(
            [
                pl.lit(None, dtype=pl.UInt32).alias("rank"),
                pl.lit(None, dtype=pl.UInt8).alias("top_percent"),
            ]
        )
    )

    # Combine and sort by rank (nulls last)
    return (
        pl.concat([ranked, unrated], how="diagonal")
        .with_columns(pl.lit(num_rated, dtype=pl.UInt32).alias("out_of_rated"))
        .sort(["rank", "index"], nulls_last=True)
    )


def member_ratings_for_book(book: dict, members: list[str]) -> pl.DataFrame:
    """Get all ratings for a single book.

    Parameters
    ----------
    book : dict
        A single row from the processed data (as a dict).
    members : list[str]
        The list of club member names.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: member, rating. Only non-null ratings included.
    """
    ratings = []
    for member in members:
        rating = book.get(member)
        if rating is not None:
            ratings.append({"member": member, "rating": float(rating)})

    return (
        pl.DataFrame(ratings)
        if ratings
        else pl.DataFrame(schema={"member": pl.Utf8, "rating": pl.Float64})
    )


def member_stats(df: pl.DataFrame, members: list[str]) -> pl.DataFrame:
    """Compute rating statistics per member.

    Nulls are skipped in all aggregates.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    members : list[str]
        The list of club member names.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: member, count, average, std_dev, min, max.
    """
    return (
        df.select(members)
        .unpivot(variable_name="member", value_name="rating")
        .drop_nulls("rating")
        .group_by("member", maintain_order=True)
        .agg(
            pl.len().alias("count"),
            pl.col("rating").mean().alias("average"),
            pl.col("rating").std().fill_null(0.0).alias("std_dev"),
            pl.col("rating").min().alias("min"),
            pl.col("rating").max().alias("max"),
        )
    )


def books_per_year(df: pl.DataFrame) -> pl.DataFrame:
    """Count books read per year.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: year, count. Sorted by year.
    """
    return (
        df.select("date")
        .with_columns(pl.col("date").dt.year().alias("year"))
        .select("year")
        .group_by("year")
        .agg(pl.len().alias("count"))
        .sort("year")
    )


def books_per_decade(df: pl.DataFrame) -> pl.DataFrame:
    """Count books by publication decade.

    Filters out books with null publication year.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: decade, decade_label, count. Sorted by decade.
    """
    return (
        df.filter(pl.col("original_publication_year").is_not_null())
        .with_columns(
            decade=((pl.col("original_publication_year") // 10) * 10).cast(pl.UInt32),
        )
        .group_by("decade")
        .agg(pl.len().alias("count"))
        .with_columns(decade_label=pl.col("decade").cast(pl.Utf8) + "s")
        .sort("decade")
    )


def rating_trend(df: pl.DataFrame, window: int = 7) -> pl.DataFrame:
    """Compute rating trend with rolling average and trend line.

    The rolling mean counts rated books only.
    With fewer than 2 rated books, no trend is computed.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data. Must be sorted by date.
    window : int, optional
        Rolling window size, by default 7.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: date, title, average_bookclub_rating, rolling_avg, trend.
        trend is a float or None.
    """
    # Filter to rated books and sort
    rated = df.filter(pl.col("average_bookclub_rating").is_not_null()).sort("date")

    if len(rated) < 2:
        # Can't compute trend with fewer than 2 books
        return rated.select("date", "title", "average_bookclub_rating").with_columns(
            [
                pl.lit(None, dtype=pl.Float64).alias("rolling_avg"),
                pl.lit(None, dtype=pl.Float64).alias("trend"),
            ]
        )

    rating = pl.col("average_bookclub_rating")
    days = pl.col("date").dt.epoch("d")

    # Least-squares line through (days, rating): slope = cov / var
    slope = pl.cov(days, rating) / days.var()

    return rated.select(
        "date",
        "title",
        "average_bookclub_rating",
        rating.rolling_mean(window_size=window, min_samples=1).alias("rolling_avg"),
        (rating.mean() + slope * (days - days.mean())).alias("trend"),
    )


def suggester_stats(
    df: pl.DataFrame,
    active_members: list[str],
    min_books: int = 3,
) -> pl.DataFrame:
    """Get statistics on book suggesters.

    Includes suggesters who either:
    1. Have suggested 3+ rated books, OR
    2. Are in the active members list (even if fewer books)

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    active_members : list[str]
        List of active member names.
    min_books : int, optional
        Minimum number of rated books, by default 3.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: suggested_by, book_count, avg_rating.
        Sorted by avg_rating descending.
    """
    # Count rated books per suggester
    rated = df.filter(pl.col("average_bookclub_rating").is_not_null())

    return (
        rated.group_by("suggested_by")
        .agg(
            [
                pl.len().alias("book_count"),
                pl.col("average_bookclub_rating").mean().alias("avg_rating"),
            ]
        )
        .filter(
            (pl.col("suggested_by").is_not_null())
            & ((pl.col("book_count") >= min_books) | pl.col("suggested_by").is_in(active_members))
        )
        .sort("avg_rating", descending=True)
    )


# Author dimensions
AUTHOR_DIMENSIONS = {
    "Nationality": "author_nationality",
    "Gender": "author_gender",
    "Era": "author_era",
}


def author_stats(df: pl.DataFrame, group_col: str) -> pl.DataFrame:
    """Get statistics grouped by an author dimension.

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    group_col : str
        The column to group by (e.g., "author_nationality").

    Returns
    -------
    pl.DataFrame
        DataFrame with columns: group, book_count, avg_rating.
    """
    if group_col not in df.columns:
        return pl.DataFrame(
            schema={"group": pl.Utf8, "book_count": pl.UInt32, "avg_rating": pl.Float64}
        )

    rated = df.filter(pl.col("average_bookclub_rating").is_not_null())

    return (
        rated.group_by(group_col)
        .agg(
            [
                pl.len().alias("book_count"),
                pl.col("average_bookclub_rating").mean().alias("avg_rating"),
            ]
        )
        .rename({group_col: "group"})
        .sort("avg_rating", descending=True)
    )


def member_correlations(
    df: pl.DataFrame,
    members: list[str],
    min_ratings: int = 5,
    min_shared: int = 3,
) -> pl.DataFrame | None:
    """Compute pairwise correlations between members.

    Returns correlations for pairs with:
    - Both members have at least min_ratings total ratings
    - At least min_shared books rated by both
    - Both ratings have variance (not all the same value)

    Parameters
    ----------
    df : pl.DataFrame
        The processed bookclub data.
    members : list[str]
        The list of club member names.
    min_ratings : int, optional
        Minimum ratings per member, by default 5.
    min_shared : int, optional
        Minimum shared books, by default 3.

    Returns
    -------
    pl.DataFrame | None
        Long-format DataFrame with columns: member_1, member_2, correlation, shared_books.
        Returns None if no valid pairs exist.
    """
    # Filter to active members (those with min_ratings)
    active = []
    for member in members:
        rating_count = df[member].drop_nulls().len()
        if rating_count >= min_ratings:
            active.append(member)

    if len(active) < 2:
        return None

    correlations = []

    for i, m1 in enumerate(active):
        for _j, m2 in enumerate(active[i + 1 :], start=i + 1):
            # Get books rated by both
            both_rated = df.filter(
                (pl.col(m1).is_not_null()) & (pl.col(m2).is_not_null()),
            )

            if len(both_rated) < min_shared:
                continue

            # Check variance
            if both_rated[m1].n_unique() <= 1 or both_rated[m2].n_unique() <= 1:
                # No variance, skip this pair
                continue

            # Compute correlation
            corr = both_rated.select(pl.corr(m1, m2)).item()

            correlations.append(
                {
                    "member_1": m1,
                    "member_2": m2,
                    "correlation": corr,
                    "shared_books": len(both_rated),
                }
            )

    return pl.DataFrame(correlations) if correlations else None
