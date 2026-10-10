"""Pipeline from the raw CSV files to the processed book club DataFrame."""

from pathlib import Path

import polars as pl
import polars.selectors as cs

from scifi.members import BookClubMember, BookClubMembers
from scifi.paths import AUTHORS_PATH, BOOKCLUB_PATH, GOODREADS_DIR, MANUAL_RATINGS_PATH

# Book club and Goodreads titles are matched case-insensitively
TITLE_KEY = pl.col("title").str.to_lowercase()


def read_combine_goodreads(goodreads_dir: Path) -> pl.DataFrame:
    """Read and combine all Goodreads CSVs into a Polars DataFrame.

    Books on every shelf are kept, so to-read entries still provide book data.
    Files are combined by column name, so an export without a column (e.g.
    "Average Rating") gets nulls for it instead of failing. Non-numeric values
    become null, and so do 0 ratings (not rated).

    Parameters
    ----------
    goodreads_dir : Path
        The directory containing the Goodreads CSVs.

    Returns
    -------
    pl.DataFrame
        The Goodreads data, one row per book per export.

    Raises
    ------
    FileNotFoundError
        If the directory contains no CSV files.
    """
    csv_files = sorted(goodreads_dir.glob("*.csv"))
    if not csv_files:
        msg = f"No CSV files found in: {goodreads_dir}"
        raise FileNotFoundError(msg)
    columns = {
        "Title": "title",
        "Author": "author",
        "My Rating": "rating",
        "Average Rating": "average_goodreads_rating",
        "Original Publication Year": "original_publication_year",
        "Number of Pages": "number_of_pages",
    }
    q = (
        pl.concat(
            [pl.scan_csv(f).with_columns(pl.lit(f.name).alias("file_name")) for f in csv_files],
            how="diagonal_relaxed",
        )
        .select([*columns.keys(), "file_name"])
        .rename(columns)
        .with_columns(
            pl.col("title").str.strip_chars().str.replace_all(r"\s+", " "),
            pl.col("author").str.strip_chars().str.replace_all(r"\s+", " "),
            pl.col("rating").cast(pl.Float64, strict=False),
            pl.col("average_goodreads_rating").cast(pl.Float64, strict=False),
            pl.col("original_publication_year").cast(pl.Int64, strict=False),
            pl.col("number_of_pages").cast(pl.Int64, strict=False),
        )
        .with_columns(
            pl.when(pl.col("rating") > 0).then(pl.col("rating")).otherwise(None).alias("rating"),
        )
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


def pivot_goodreads_data(goodreads_df: pl.DataFrame, members: list[BookClubMember]) -> pl.DataFrame:
    """Pivot the Goodreads data to one row per book with a rating column per member.

    Every member gets a Float64 column: all null for a member without an
    export, or whose export has no rows.

    Parameters
    ----------
    goodreads_df : pl.DataFrame
        The Goodreads data, one row per book per export.
    members : list[BookClubMember]
        The members whose ratings become columns.

    Returns
    -------
    pl.DataFrame
        The pivoted Goodreads data.
    """
    index_cols = ["title", "author"]
    pivot_df = (
        goodreads_df.with_columns(
            pl.mean("average_goodreads_rating").over(index_cols),
            pl.mean("number_of_pages").over(index_cols),
            # Editions can list a different original year; the earliest is the original
            pl.min("original_publication_year").over(index_cols),
        )
        .pivot(
            "file_name",
            index=[
                *index_cols,
                "original_publication_year",
                "average_goodreads_rating",
                "number_of_pages",
            ],
            values="rating",
            aggregate_function="mean",
        )
        # An export that is not in goodreads_dir has no column to rename
        .rename(
            {member.file_name: member.name for member in members if member.file_name is not None},
            strict=False,
        )
    )
    return pivot_df.with_columns(
        pl.lit(None, pl.Float64).alias(member.name)
        for member in members
        if member.name not in pivot_df.columns
    )


def merge_manual_ratings(df: pl.DataFrame, manual_ratings_df: pl.DataFrame) -> pl.DataFrame:
    """Override ratings with the manual ratings where they are given.

    Every manual column except title and author must exist in `df`. A manual
    value wins over the existing one; an empty manual value keeps it.

    Parameters
    ----------
    df : pl.DataFrame
        The book club data with a column per member.
    manual_ratings_df : pl.DataFrame
        The manual ratings, one row per book.

    Returns
    -------
    pl.DataFrame
        The book club data with the manual ratings applied.
    """
    overrides = manual_ratings_df.drop("title", "author").columns
    return (
        df.join(
            manual_ratings_df.drop("author"),
            on=TITLE_KEY,
            how="left",
            suffix="_manual",
            maintain_order="left",
        )
        .with_columns(pl.coalesce(f"{col}_manual", col).alias(col) for col in overrides)
        .drop(cs.ends_with("_manual"))
    )


def process_bookclub_data(
    goodreads_dir: Path = GOODREADS_DIR,
    bookclub_path: Path = BOOKCLUB_PATH,
    manual_ratings_path: Path = MANUAL_RATINGS_PATH,
    authors_path: Path = AUTHORS_PATH,
) -> pl.DataFrame:
    """Process all book club data from the raw CSV files.

    Every book club book is kept. Goodreads data is matched on the title,
    manual ratings win over Goodreads ratings, and the club average is the
    mean over the member ratings.

    Parameters
    ----------
    goodreads_dir : Path, optional
        Directory containing the Goodreads export CSVs, by default GOODREADS_DIR.
    bookclub_path : Path, optional
        Path to the book club CSV, by default BOOKCLUB_PATH.
    manual_ratings_path : Path, optional
        Path to the manual ratings CSV, by default MANUAL_RATINGS_PATH.
    authors_path : Path, optional
        Path to the authors CSV (one row per author), by default AUTHORS_PATH.

    Returns
    -------
    pl.DataFrame
        One row per book club book, sorted by date and index: the book club
        columns, the Goodreads columns, a Float64 column per member, the club
        average, and the author columns.
    """
    members = BookClubMembers.get_member_names()
    goodreads_df = pivot_goodreads_data(
        read_combine_goodreads(goodreads_dir), BookClubMembers.get_all_members()
    )
    authors_df = pl.read_csv(authors_path)
    bookclub_df = merge_manual_ratings(
        # The left join keeps every book club book; the book club author is the canonical one
        read_bookclub(bookclub_path)
        .join(goodreads_df.drop("author"), on=TITLE_KEY, how="left", maintain_order="left")
        .drop("title_right"),
        read_manual_ratings(manual_ratings_path),
    ).join(authors_df, on="author", how="left")
    # The column order is the schema contract: book club, Goodreads, members, club average, authors
    return bookclub_df.select(
        "index",
        "date",
        "title",
        "author",
        "suggested_by",
        "location",
        "original_publication_year",
        "average_goodreads_rating",
        "number_of_pages",
        *members,
        pl.mean_horizontal(*members).alias("average_bookclub_rating"),
        *authors_df.drop("author").columns,
    ).sort("date", "index")
