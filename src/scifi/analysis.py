"""Polars computations behind the dashboard."""

from datetime import date
from itertools import combinations

import polars as pl


def current_meeting(df: pl.DataFrame, today: date) -> pl.DataFrame:
    """Return the books of the first meeting on or after today, else of the last meeting."""
    meeting_date = df.filter(pl.col("date") >= today)["date"].min() or df["date"].max()
    return df.filter(pl.col("date") == meeting_date).sort("index")


def rank_books(df: pl.DataFrame) -> pl.DataFrame:
    """Rank the books by club rating; unrated books get no rank and come last."""
    rank = pl.col("average_bookclub_rating").rank(method="min", descending=True).cast(pl.UInt32)
    num_rated = pl.col("average_bookclub_rating").count().cast(pl.UInt32)
    return df.select(
        "index",
        "title",
        "author",
        "average_bookclub_rating",
        rank.alias("rank"),
        ((rank * 100 + num_rated - 1) // num_rated).cast(pl.UInt8).alias("top_percent"),
        num_rated.alias("out_of_rated"),
    ).sort(["rank", "index"], nulls_last=True)


def rating_trend(df: pl.DataFrame, window: int = 7) -> pl.DataFrame:
    """Return the rated books with a rolling average and a least-squares trend line."""
    rating = pl.col("average_bookclub_rating")
    days = pl.col("date").dt.epoch("d")
    slope = pl.cov(days, rating) / days.var()
    return (
        df.filter(rating.is_not_null())
        .sort("date")
        .select(
            "date",
            "title",
            "average_bookclub_rating",
            rating.rolling_mean(window_size=window, min_samples=1).alias("rolling_avg"),
            (rating.mean() + slope * (days - days.mean())).alias("trend"),
        )
    )


def member_correlations(
    df: pl.DataFrame, members: list[str], min_ratings: int = 5, min_shared: int = 3
) -> pl.DataFrame | None:
    """Correlate each pair of active members over the books both rated."""
    active = [m for m in members if df[m].count() >= min_ratings]
    rows = []
    for m1, m2 in combinations(active, 2):
        both = df.select(m1, m2).drop_nulls()
        if len(both) >= min_shared and both[m1].n_unique() > 1 and both[m2].n_unique() > 1:
            corr = both.select(pl.corr(m1, m2)).item()
            rows.append(
                {"member_1": m1, "member_2": m2, "correlation": corr, "shared_books": len(both)}
            )
    return pl.DataFrame(rows) if rows else None


def suggester_stats(
    df: pl.DataFrame, active_members: list[str], min_books: int = 3
) -> pl.DataFrame:
    """Count and average the rated books per active member or frequent suggester."""
    return (
        df.filter(pl.col("average_bookclub_rating").is_not_null())
        .group_by("suggested_by")
        .agg(
            pl.len().alias("book_count"),
            pl.col("average_bookclub_rating").mean().alias("avg_rating"),
        )
        .filter(
            pl.col("suggested_by").is_not_null()
            & ((pl.col("book_count") >= min_books) | pl.col("suggested_by").is_in(active_members))
        )
        .sort("avg_rating", descending=True)
    )
