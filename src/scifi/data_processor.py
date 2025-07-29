"""Data processing pipeline for the sci-fi book club data.

This module consolidates all data processing logic from the aggregating notebook
into a single, reusable pipeline. It handles reading, cleaning, combining, and
matching data from multiple sources.
"""

from pathlib import Path

import polars as pl

from scifi.utils import (
    get_reviewer_mapping,
    match_dataframes,
    merge_manual_ratings,
    pivot_goodreads_data,
    read_bookclub,
    read_manual_ratings,
)


def load_and_combine_goodreads_data(goodreads_dir: Path) -> pl.DataFrame:
    """Load and combine all Goodreads CSV files with improved error handling.

    This is an enhanced version of read_combine_goodreads that handles
    non-numeric rating values properly.

    Parameters
    ----------
    goodreads_dir : Path
        The directory containing the Goodreads CSVs.

    Returns
    -------
    pl.DataFrame
        The combined and cleaned Goodreads data.

    Raises
    ------
    FileNotFoundError
        If the goodreads directory doesn't exist or contains no CSV files.
    RuntimeError
        If there's an error processing the Goodreads data.
    """
    if not goodreads_dir.exists():
        msg = f"Goodreads directory not found: {goodreads_dir}"
        raise FileNotFoundError(msg)

    csv_files = list(goodreads_dir.glob("*.csv"))
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

    try:
        q = (
            pl.scan_csv(goodreads_dir, include_file_paths="path")
            .filter(pl.col("Exclusive Shelf") == "read")
            .select([*columns.keys(), "path"])
            .rename(columns)
            .with_columns(
                pl.col("title").str.strip_chars(),
                pl.col("author").str.strip_chars(),
                # Convert rating to numeric, handling non-numeric values
                pl.col("rating").cast(pl.Float64, strict=False),
                pl.col("average_goodreads_rating").cast(pl.Float64, strict=False),
                pl.col("original_publication_year").cast(pl.Int64, strict=False),
                pl.col("number_of_pages").cast(pl.Int64, strict=False),
            )
            # Filter for valid ratings (> 0 and not null)
            .filter(pl.col("rating").is_not_null() & (pl.col("rating") > 0))
        )

        return q.collect()
    except Exception as e:
        msg = f"Error processing Goodreads data: {e}"
        raise RuntimeError(msg) from e


def load_bookclub_data(bookclub_path: Path) -> pl.DataFrame:
    """Load bookclub meeting data with error handling.

    Parameters
    ----------
    bookclub_path : Path
        Path to the bookclub CSV file.

    Returns
    -------
    pl.DataFrame
        The bookclub meeting data.

    Raises
    ------
    FileNotFoundError
        If the bookclub file doesn't exist.
    RuntimeError
        If there's an error loading the bookclub data.
    """
    if not bookclub_path.exists():
        msg = f"Bookclub file not found: {bookclub_path}"
        raise FileNotFoundError(msg)

    try:
        return read_bookclub(bookclub_path)
    except Exception as e:
        msg = f"Error loading bookclub data: {e}"
        raise RuntimeError(msg) from e


def match_and_merge_data(
    bookclub_df: pl.DataFrame,
    goodreads_pivot_df: pl.DataFrame,
    manual_ratings_path: Path | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Match bookclub data with Goodreads data and merge manual ratings.

    Parameters
    ----------
    bookclub_df : pl.DataFrame
        The bookclub meeting data.
    goodreads_pivot_df : pl.DataFrame
        The pivoted Goodreads data with member columns.
    manual_ratings_path : Path | None, optional
        Path to manual ratings file, by default None.

    Returns
    -------
    tuple[pl.DataFrame, pl.DataFrame]
        A tuple of (matched_data, unmatched_data).
    """
    # Match bookclub data with Goodreads data (inner join)
    bookclub_processed_df = match_dataframes(
        bookclub_df=bookclub_df,
        goodreads_pivot_df=goodreads_pivot_df,
        on="title",
        how="inner",
    )

    # Find unmatched records (anti join)
    unmatched_df = match_dataframes(
        bookclub_df=bookclub_df,
        goodreads_pivot_df=goodreads_pivot_df,
        on="title",
        how="anti",
    )

    # Merge manual ratings if provided
    if manual_ratings_path and manual_ratings_path.exists():
        try:
            manual_ratings_df = read_manual_ratings(manual_ratings_path)
            bookclub_processed_df = merge_manual_ratings(
                bookclub_processed_df=bookclub_processed_df,
                manual_ratings_df=manual_ratings_df,
                on="title",
            )
        except (ValueError, FileNotFoundError):
            # Manual ratings merge failed, continue without them
            pass

    return bookclub_processed_df, unmatched_df


def process_bookclub_data(
    goodreads_dir: Path | str | None = None,
    bookclub_path: Path | str | None = None,
    manual_ratings_path: Path | str | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Process all book club data from raw sources.

    This is the main orchestration function that runs the entire data processing
    pipeline from raw CSV files to analysis-ready DataFrames.

    Parameters
    ----------
    goodreads_dir : Path | str | None, optional
        Directory containing Goodreads CSV files, by default "data/goodreads/clean".
    bookclub_path : Path | str | None, optional
        Path to bookclub CSV file, by default "data/bookclub/bookclub.csv".
    manual_ratings_path : Path | str | None, optional
        Path to manual ratings CSV file, by default "data/bookclub/manual_ratings.csv".

    Returns
    -------
    tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]
        A tuple of (processed_bookclub_data, unmatched_books, combined_goodreads_data).

    Raises
    ------
    RuntimeError
        If data processing fails.
    """
    # Set default paths
    goodreads_dir = Path("data/goodreads/clean") if goodreads_dir is None else Path(goodreads_dir)

    if bookclub_path is None:
        bookclub_path = Path("data/bookclub/bookclub.csv")
    else:
        bookclub_path = Path(bookclub_path)

    if manual_ratings_path is None:
        manual_ratings_path = Path("data/bookclub/manual_ratings.csv")
    else:
        manual_ratings_path = Path(manual_ratings_path)

    try:
        # Step 1: Load and combine Goodreads data
        goodreads_df = load_and_combine_goodreads_data(goodreads_dir)

        # Step 2: Pivot Goodreads data by reviewer
        goodreads_pivot_df = pivot_goodreads_data(
            goodreads_df=goodreads_df,
            reviewer_mapping=get_reviewer_mapping(),
        )

        # Step 3: Load bookclub data
        bookclub_df = load_bookclub_data(bookclub_path)

        # Step 4: Match and merge data
        bookclub_processed_df, unmatched_df = match_and_merge_data(
            bookclub_df=bookclub_df,
            goodreads_pivot_df=goodreads_pivot_df,
            manual_ratings_path=manual_ratings_path,
        )

        # Step 5: Sort by date
        bookclub_processed_df = bookclub_processed_df.sort("date")

        return bookclub_processed_df, unmatched_df, goodreads_df

    except Exception as e:
        msg = f"Data processing pipeline failed: {e}"
        raise RuntimeError(msg) from e


def save_processed_data(
    bookclub_processed_df: pl.DataFrame,
    unmatched_df: pl.DataFrame,
    goodreads_df: pl.DataFrame,
    output_dir: Path | str = "data",
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
        Directory to save output files, by default "data".
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

    if len(unmatched_df) > 0:
        print("\nUnmatched books:")
        print(unmatched_df.select(["title", "author", "suggested_by"]))
