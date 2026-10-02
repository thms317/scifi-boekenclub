"""Data processing pipeline for the sci-fi book club data.

This module consolidates all data processing logic from the aggregating notebook
into a single, reusable pipeline. It handles reading, cleaning, combining, and
matching data from multiple sources.
"""

from pathlib import Path

import polars as pl

from scifi.members import BookClubMembers
from scifi.paths import AUTHORS_PATH, BOOKCLUB_PATH, DATA_DIR, GOODREADS_DIR, MANUAL_RATINGS_PATH
from scifi.utils import (
    match_dataframes,
    merge_manual_ratings,
    pivot_goodreads_data,
    read_bookclub,
    read_combine_goodreads,
    read_manual_ratings,
)


def process_bookclub_data(
    goodreads_dir: Path | str = GOODREADS_DIR,
    bookclub_path: Path | str = BOOKCLUB_PATH,
    manual_ratings_path: Path | str = MANUAL_RATINGS_PATH,
    authors_path: Path | str = AUTHORS_PATH,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Process all book club data from raw sources.

    This is the main orchestration function that runs the entire data processing
    pipeline from raw CSV files to analysis-ready DataFrames.

    Parameters
    ----------
    goodreads_dir : Path | str, optional
        Directory containing Goodreads CSV files, by default GOODREADS_DIR.
    bookclub_path : Path | str, optional
        Path to bookclub CSV file, by default BOOKCLUB_PATH.
    manual_ratings_path : Path | str, optional
        Path to manual ratings CSV file, by default MANUAL_RATINGS_PATH.
    authors_path : Path | str, optional
        Path to authors CSV file (one row per author), by default AUTHORS_PATH.

    Returns
    -------
    tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]
        A tuple of (processed_bookclub_data, unmatched_books, combined_goodreads_data).
    """
    goodreads_df = read_combine_goodreads(Path(goodreads_dir))
    goodreads_pivot_df = pivot_goodreads_data(
        goodreads_df=goodreads_df,
        reviewer_mapping=BookClubMembers.get_reviewer_mapping(),
    )
    bookclub_df = read_bookclub(Path(bookclub_path))
    # Left join keeps every book club book; the anti join lists the books without a match
    matched_df = match_dataframes(bookclub_df, goodreads_pivot_df, on="title", how="left")
    unmatched_df = match_dataframes(bookclub_df, goodreads_pivot_df, on="title", how="anti")
    bookclub_processed_df = merge_manual_ratings(
        bookclub_processed_df=matched_df,
        manual_ratings_df=read_manual_ratings(Path(manual_ratings_path)),
        on="title",
    )

    # Get all member names in registry order
    all_member_names = BookClubMembers.get_member_names()

    # Ensure all members have a Float64 column, even if null
    member_exprs = [
        pl.col(member_name).cast(pl.Float64)
        if member_name in bookclub_processed_df.columns
        else pl.lit(None, dtype=pl.Float64).alias(member_name)
        for member_name in all_member_names
    ]
    bookclub_processed_df = bookclub_processed_df.with_columns(member_exprs)

    # Calculate average over the member ratings
    bookclub_processed_df = bookclub_processed_df.with_columns(
        pl.mean_horizontal(*all_member_names).alias("average_bookclub_rating")
    )

    # Join with authors data
    authors_df = pl.read_csv(authors_path)
    bookclub_processed_df = bookclub_processed_df.join(authors_df, on="author", how="left")

    # Reorder columns to match the expected schema:
    # 1. bookclub columns: index, date, title, author, suggested_by, location
    # 2. Goodreads columns: original_publication_year, average_goodreads_rating, number_of_pages
    # 3. member columns in registry order (all Float64)
    # 4. average_bookclub_rating
    # 5. author columns (from authors.csv)

    bookclub_cols = ["index", "date", "title", "author", "suggested_by", "location"]
    goodreads_cols = ["original_publication_year", "average_goodreads_rating", "number_of_pages"]
    author_cols = [col for col in authors_df.columns if col != "author"]

    final_column_order = (
        bookclub_cols
        + goodreads_cols
        + all_member_names
        + ["average_bookclub_rating"]
        + author_cols
    )

    bookclub_processed_df = bookclub_processed_df.select(final_column_order).sort(["date", "index"])

    return bookclub_processed_df, unmatched_df, goodreads_df


def load_dashboard_data(
    goodreads_dir: Path | str = GOODREADS_DIR,
    bookclub_path: Path | str = BOOKCLUB_PATH,
    manual_ratings_path: Path | str = MANUAL_RATINGS_PATH,
    authors_path: Path | str = AUTHORS_PATH,
) -> pl.DataFrame:
    """Load the processed book club data for dashboard display.

    Runs the pipeline and filters to keep only rows where date is not null.

    Parameters
    ----------
    goodreads_dir : Path | str, optional
        Directory containing Goodreads CSV files, by default GOODREADS_DIR.
    bookclub_path : Path | str, optional
        Path to bookclub CSV file, by default BOOKCLUB_PATH.
    manual_ratings_path : Path | str, optional
        Path to manual ratings CSV file, by default MANUAL_RATINGS_PATH.
    authors_path : Path | str, optional
        Path to authors CSV file (one row per author), by default AUTHORS_PATH.

    Returns
    -------
    pl.DataFrame
        The processed bookclub data with only rows where date is not null.
    """
    bookclub_processed_df, _, _ = process_bookclub_data(
        goodreads_dir=goodreads_dir,
        bookclub_path=bookclub_path,
        manual_ratings_path=manual_ratings_path,
        authors_path=authors_path,
    )
    return bookclub_processed_df.filter(pl.col("date").is_not_null())


def save_processed_data(
    bookclub_processed_df: pl.DataFrame,
    unmatched_df: pl.DataFrame,
    goodreads_df: pl.DataFrame,
    output_dir: Path | str = DATA_DIR,
) -> None:
    """Save processed data to CSV files.

    Parameters
    ----------
    bookclub_processed_df : pl.DataFrame
        The processed bookclub data.
    unmatched_df : pl.DataFrame
        The unmatched books data.
    goodreads_df : pl.DataFrame
        The combined Goodreads data.
    output_dir : Path | str, optional
        Directory to save output files, by default DATA_DIR.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    # Save main processed data
    processed_path = output_dir / "processed_data.csv"
    processed_path.parent.mkdir(exist_ok=True)
    bookclub_processed_df.write_csv(processed_path)
    # Save unmatched data
    unmatched_path = output_dir / "goodreads" / "goodreads_unmatched.csv"
    unmatched_path.parent.mkdir(exist_ok=True)
    unmatched_df.write_csv(unmatched_path)
    # Save combined Goodreads data
    combined_path = output_dir / "goodreads" / "goodreads_combined.csv"
    goodreads_df.write_csv(combined_path)


if __name__ == "__main__":
    # Run the processing pipeline
    processed_df, unmatched_df, goodreads_df = process_bookclub_data()
    # Save the results
    save_processed_data(processed_df, unmatched_df, goodreads_df)
    print("\nProcessing complete!")
    print(f"Processed books: {len(processed_df)}")
    print(f"Unmatched books: {len(unmatched_df)}")
    print(f"Total Goodreads entries: {len(goodreads_df)}")
    # Display unmatched books
    if len(unmatched_df) > 0:
        print("\nUnmatched books:")
        print(unmatched_df.select(["title", "author", "suggested_by"]))
