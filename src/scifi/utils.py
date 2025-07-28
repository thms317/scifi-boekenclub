"""Utility functions for the scifi project."""

from pathlib import Path
from typing import Literal

import polars as pl


def get_reviewer_mapping() -> dict[str, str]:
    """Return the mapping from file paths to reviewer names.

    Returns
    -------
    dict[str, str]
        A dictionary mapping file paths to reviewer names.
    """
    return {
        "data/goodreads/clean/dion_goodreads_library_export.csv": "Dion",
        "data/goodreads/clean/goodreads_library_export-PHT_clean.csv": "Peter",
        "data/goodreads/clean/goodreads_library_export-thirsa.csv": "Thirsa",
        "data/goodreads/clean/koen_goodreads_library_export.csv": "Koen_v_W",
        "data/goodreads/clean/koen_m_goodreads_library_export.csv": "Koen_M",
        # "data/goodreads/clean/laurynas_goodreads_library_export.csv": "Laurynas",
        "data/goodreads/clean/Thomas is een worstje_clean.csv": "Robert",
        "data/goodreads/clean/thomas_goodreads_library_export.csv": "Thomas",
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
        "Wie heeft gekozen?": "suggested_by",
        "Locatie": "location",
    }
    q = (
        pl.scan_csv(bookclub_path)
        .select(columns.keys())
        .rename(columns)
        .with_columns(
            pl.col("date").str.to_date("%m/%d/%Y"),
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


def read_manual_ratings(manual_ratings_path: Path) -> pl.DataFrame:
    """Read the manual ratings CSV into a Polars DataFrame.

    The title and author columns are stripped of whitespace.
    Rating columns are cast to float to preserve numeric types.

    Parameters
    ----------
    manual_ratings_path : Path
        Path to the manual ratings CSV.

    Returns
    -------
    pl.DataFrame
        The manual ratings data.
    """
    return pl.read_csv(manual_ratings_path).with_columns(
        pl.col("title").str.strip_chars(),
        pl.col("author").str.strip_chars(),
        pl.exclude(["title", "author"]).cast(pl.Float64, strict=False),
    )


def merge_manual_ratings(
    bookclub_processed_df: pl.DataFrame,
    manual_ratings_df: pl.DataFrame,
    on: str = "title",
) -> pl.DataFrame:
    """Merge manual ratings into the processed bookclub data.

    Empty/null values in manual ratings will not overwrite existing ratings
    in the bookclub processed data. Only non-null manual ratings will be used.

    Parameters
    ----------
    bookclub_processed_df : pl.DataFrame
        The processed bookclub DataFrame.
    manual_ratings_df : pl.DataFrame
        The manual ratings DataFrame.
    on : str, optional
        The column to join on, by default "title"

    Returns
    -------
    pl.DataFrame
        The joined DataFrame where manual ratings supplement existing ratings
        without overwriting them when manual ratings are empty/null.
    """
    # Get the member columns
    bookclub_members_list = [
        col for col in manual_ratings_df.columns if col not in ["title", "author"]
    ]
    # Join the DataFrames on the match column (use a temporary column to prevent column duplication)
    joined_df = (
        bookclub_processed_df.with_columns(pl.col(on).str.to_lowercase().alias("temp_match_column"))
        .join(
            manual_ratings_df.with_columns(
                pl.col(on).str.to_lowercase().alias("temp_match_column")
            ).select(["temp_match_column", *bookclub_members_list]),
            on="temp_match_column",
            how="left",
            suffix="_manual",
        )
        .drop("temp_match_column")
    )
    # Use manual rating only if there is no existing rating
    coalesce_exprs = []
    for col in bookclub_members_list:
        manual_col = f"{col}_manual"
        if col in bookclub_processed_df.columns and manual_col in joined_df.columns:
            # Use coalesce to prefer existing ratings over manual ratings when both exist
            coalesce_exprs.append(pl.coalesce([pl.col(col), pl.col(manual_col)]).alias(col))
        elif manual_col in joined_df.columns:
            # If original column doesn't exist, just rename the manual column
            coalesce_exprs.append(pl.col(manual_col).alias(col))
    # Apply the coalescing and drop the manual columns
    if coalesce_exprs:
        manual_cols_to_drop = [
            f"{col}_manual" for col in bookclub_members_list if f"{col}_manual" in joined_df.columns
        ]
        return joined_df.with_columns(coalesce_exprs).drop(manual_cols_to_drop)
    return joined_df


def get_active_book_suggesters(
    bookclub_df: pl.DataFrame,
    min_suggestions: int = 2,
) -> pl.DataFrame:
    """Get book suggesters who are active in the bookclub.

    Returns suggesters who either:
    1. Have suggested more than the minimum number of books, OR
    2. Are in the reviewer mapping (even if they've suggested fewer books)

    Parameters
    ----------
    bookclub_df : pl.DataFrame
        The bookclub DataFrame containing suggestion data.
    min_suggestions : int, optional
        Minimum number of suggestions to be considered active, by default 2

    Returns
    -------
    pl.DataFrame
        DataFrame with suggester names and their suggestion counts,
        sorted by count in descending order.
    """
    reviewer_mapping = get_reviewer_mapping()
    mapped_reviewer_names = list(reviewer_mapping.values())
    return (
        bookclub_df.group_by("suggested_by")
        .agg(pl.count("title").alias("count"))
        .filter(
            pl.col("suggested_by").is_not_null()
            & (
                (pl.col("count") > min_suggestions)
                | pl.col("suggested_by").is_in(mapped_reviewer_names)
            )
        )
        .sort("count", descending=True)
    )
