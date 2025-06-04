"""Utilitiy functions for the scifi project."""

from pathlib import Path
from typing import Literal

import numpy as np
import polars as pl


def get_reviewer_mapping() -> dict[str, str]:
    """Return the mapping from file paths to reviewer names.

    Returns
    -------
    dict[str, str]
        A dictionary mapping file paths to reviewer names.
    """
    return {
        "data/goodreads/clean/koen_goodreads_library_export.csv": "Koen_v_W",
        "data/goodreads/clean/thomas_goodreads_library_export.csv": "Thomas",
        "data/goodreads/clean/koen_m_goodreads_library_export.csv": "Koen_M",
        "data/goodreads/clean/Thomas is een worstje_clean.csv": "Robert",
        "data/goodreads/clean/goodreads_library_export-PHT_clean.csv": "Peter",
        "data/goodreads/clean/goodreads_library_export-thirsa.csv": "Thirsa",
    }


def read_combine_goodreads(goodreads_dir: Path) -> pl.DataFrame:
    """Read and combine all Goodreads CSVs into a Polars DataFrame.

    The title and author columns are stripped of whitespace.

    Parameters
    ----------
    goodreads_dir : Path
        The directory containing the Goodreads CSVs.

    Returns
    -------
    pl.DataFrame
        The Goodreads data.
    """
    columns = {
        "Title": "title",
        "Author": "author",
        "My Rating": "rating",
        "Average Rating": "average_goodreads_rating",
        "Original Publication Year": "original_publication_year",
        "Number of Pages": "number_of_pages",
    }
    q = (
        pl.scan_csv(goodreads_dir, include_file_paths="path")
        .filter(pl.col("Exclusive Shelf") == "read")
        .select([*columns.keys(), "path"])
        .rename(columns)
        .with_columns(
            pl.col("title").str.strip_chars(),
            pl.col("author").str.strip_chars(),
        )
        .filter(pl.col("rating") > 0)
    )
    return q.collect()


def read_bookclub(bookclub_path: Path) -> pl.DataFrame:
    """Read the Bookclub CSV into a Polars DataFrame.

    The date column is converted to a date, and the title and author columns
    are stripped of whitespace.

    Parameters
    ----------
    bookclub_path : Path
        Path to the Bookclub CSV.

    Returns
    -------
    pl.DataFrame
        The Bookclub data.
    """
    columns = {
        "Nummer": "index",
        "Datum": "date",
        "Boek": "title",
        "Auteur": "author",
        "Wie heeft gekozen?": "blame",
        "Locatie": "location",
    }
    q = (
        pl.scan_csv(bookclub_path)
        .select(columns.keys())
        .rename(columns)
        .with_columns(
            pl.col("date").str.to_date("%m/%d/%Y").cast(pl.Datetime),
            pl.col("title").str.strip_chars(),
            pl.col("author").str.strip_chars(),
        )
    )
    return q.collect()


def pivot_goodreads_data(
    goodreads_df: pl.DataFrame,
    reviewer_mapping: dict[str, str],
) -> pl.DataFrame:
    """Pivot the Goodreads data, grouping by book, and calculating average ratings.

    Parameters
    ----------
    goodreads_df : pl.DataFrame
        The Goodreads data.
    reviewer_mapping : dict[str, str]
        Dictionary mapping file paths to reviewer names.

    Returns
    -------
    pl.DataFrame
        The pivoted Goodreads data.
    """
    index_cols = ["title", "author", "original_publication_year"]
    return (
        goodreads_df.with_columns(
            [
                pl.mean("average_goodreads_rating").over(index_cols),
                pl.mean("number_of_pages").over(index_cols),
            ],
        )
        .pivot(
            "path",
            index=[*index_cols, "average_goodreads_rating", "number_of_pages"],
            values="rating",
            aggregate_function="mean",
        )
        .rename(reviewer_mapping)
        .with_columns(
            pl.mean_horizontal(*list(reviewer_mapping.values())).alias("average_bookclub_rating"),
            pl.col("average_goodreads_rating"),
            pl.col("number_of_pages"),
        )
    )


def match_dataframes(
    bookclub_df: pl.DataFrame,
    goodreads_pivot_df: pl.DataFrame,
    on: str,
    how: Literal["inner", "left", "right", "full", "semi", "anti", "cross", "outer"],
) -> pl.DataFrame:
    """Match the Bookclub and Goodreads DataFrames on a column.

    The match column is converted to lowercase before matching.
    After the match, the match column is dropped.

    Parameters
    ----------
    bookclub_df : pl.DataFrame
        The Bookclub DataFrame.
    goodreads_pivot_df : pl.DataFrame
        The Goodreads DataFrame.
    on : str
        The column to match on.
    how : Literal["inner", "left", "right", "full", "semi", "anti", "cross", "outer"]
        The type of join to perform.

    Returns
    -------
    pl.DataFrame
        The matched DataFrame.
    """
    return (
        bookclub_df.with_columns(pl.col(on).str.to_lowercase().alias("temp_match_column"))
        .join(
            goodreads_pivot_df.with_columns(
                pl.col(on).str.to_lowercase().alias("temp_match_column"),
            ),
            on="temp_match_column",
            how=how,
        )
        .drop("temp_match_column")
    )


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
