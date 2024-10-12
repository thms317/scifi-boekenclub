"""File utilities for the scifi project."""

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
        "data/goodreads/koen_goodreads_library_export.csv": "Koen",
        "data/goodreads/thomas_goodreads_library_export.csv": "Thomas",
        "data/goodreads/koen_m_goodreads_library_export.csv": "Koen_M",
        "data/goodreads/Thomas is een worstje_clean.csv": "Robert",
        "data/goodreads/goodreads_library_export-PHT_clean.csv": "Peter",
    }


def read_goodreads(path_goodreads_dir: Path) -> pl.DataFrame:
    """Read the Goodreads CSVs into a Polars DataFrame.

    The title and author columns are stripped of whitespace.

    Parameters
    ----------
    path_goodreads_dir : Path
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
        pl.scan_csv(path_goodreads_dir, include_file_paths="path")
        .filter(pl.col("Exclusive Shelf") == "read")
        .select([*columns.keys(), "path"])
        .rename(columns)
        .with_columns(
            pl.col("title").str.strip_chars(),
            pl.col("author").str.strip_chars(),
        )
    )
    return q.collect()


def read_bookclub(path_bookclub: Path) -> pl.DataFrame:
    """Read the Bookclub CSV into a Polars DataFrame.

    The date column is converted to a date, and the title and author columns
    are stripped of whitespace.

    Parameters
    ----------
    path_bookclub : Path
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
        pl.scan_csv(path_bookclub)
        .select(columns.keys())
        .rename(columns)
        .with_columns(
            pl.col("date").str.to_date("%m/%d/%Y").cast(pl.Datetime),  # redundant?
            pl.col("title").str.strip_chars(),
            pl.col("author").str.strip_chars(),
        )
    )
    return q.collect()


def pivot_goodreads_data(
    df_goodreads: pl.DataFrame, reviewer_mapping: dict[str, str]
) -> pl.DataFrame:
    """Pivot the Goodreads data, grouping by book, and calculating ratings.

    Parameters
    ----------
    df_goodreads : pl.DataFrame
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
        df_goodreads.with_columns(
            [
                pl.mean("average_goodreads_rating").over(index_cols),
                pl.mean("number_of_pages").over(index_cols),
            ]
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
    df_bookclub: pl.DataFrame,
    df_pivot: pl.DataFrame,
    on: str,
    how: Literal["inner", "left", "right", "full", "semi", "anti", "cross", "outer"],
) -> pl.DataFrame:
    """Match the Bookclub and Goodreads DataFrames on a column.

    The match column is converted to lowercase before matching.
    After the match, the match column is dropped.

    Parameters
    ----------
    df_bookclub : pl.DataFrame
        The Bookclub DataFrame.
    df_pivot : pl.DataFrame
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
        df_bookclub.with_columns(pl.col(on).str.to_lowercase().alias("temp_match_column"))
        .join(
            df_pivot.with_columns(pl.col(on).str.to_lowercase().alias("temp_match_column")),
            on="temp_match_column",
            how=how,
        )
        .drop("temp_match_column")
    )


# def select_unmatched(df_bookclub: pl.DataFrame, df_scifi: pl.DataFrame) -> pl.DataFrame:
#     """Select the rows in the Bookclub DataFrame that do not have a match in the Goodreads DataFrame.

#     Parameters
#     ----------
#     df_bookclub : pl.DataFrame
#         The Bookclub DataFrame.
#     df_scifi : pl.DataFrame
#         The matched DataFrame.

#     Returns
#     -------
#     pl.DataFrame
#         The unmatched rows.
#     """
#     return df_bookclub.filter(
#         pl.col("title").is_in(
#             df_scifi.filter(pl.col("average_goodreads_rating").is_null())
#             .select("title")
#             .to_series()
#         )
#     )
