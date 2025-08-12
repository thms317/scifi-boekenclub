"""
Legacy visualization components removed from the main dashboard.

This module contains additional insights and visualization elements that were
part of the dashboard but were moved here to reduce complexity.
"""

import pandas as pd
import polars as pl
import streamlit as st


def create_additional_book_insights(
    selected_book: pd.Series,
    df: pl.DataFrame,
    members: list[str],
) -> None:
    """Create additional insights section for a selected book."""
    # Additional insights section
    st.markdown("### 🔍 Additional Insights")

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        # Publication era analysis
        st.subheader("📅 Publication Era Context")

        pub_year = selected_book["original_publication_year"]

        # Categorize by era
        if pub_year < 1960:
            era = "Golden Age (pre-1960)"
            era_emoji = "🏛️"
        elif pub_year < 1980:
            era = "New Wave (1960s-70s)"
            era_emoji = "🌊"
        elif pub_year < 2000:
            era = "Cyberpunk Era (1980s-90s)"
            era_emoji = "🤖"
        else:
            era = "Modern Sci-Fi (2000+)"
            era_emoji = "🚀"

        st.write(f"{era_emoji} **Era:** {era}")
        st.write(f"📅 **Published:** {pub_year}")

        # Compare with other books from same era
        era_books = df.filter(
            pl.col("original_publication_year").is_between(pub_year - 10, pub_year + 10),
        )
        avg_era_rating = era_books["average_bookclub_rating"].mean()

        if selected_book["average_bookclub_rating"] > avg_era_rating:
            st.success(f"📈 Above average for its era! ({avg_era_rating:.2f})")
        else:
            st.info(f"📊 Era average: {avg_era_rating:.2f}")

    with insight_col2:
        # Book statistics
        st.subheader("📊 Book Statistics")

        # How many members rated this book
        member_ratings_count = sum(1 for member in members if not pd.isna(selected_book[member]))
        st.write(f"👥 **Members who rated:** {member_ratings_count}/{len(members)}")

        # Rating spread
        ratings = [
            selected_book[member] for member in members if not pd.isna(selected_book[member])
        ]
        if ratings:
            rating_spread = max(ratings) - min(ratings)
            st.write(f"📏 **Rating spread:** {rating_spread:.1f} points")

            if rating_spread < 1:
                st.success("🎯 High consensus!")
            elif rating_spread < 2:
                st.info("👍 Good agreement")
            else:
                st.warning("🤷 Mixed opinions")


def get_era_info(pub_year: int) -> tuple[str, str]:
    """Get era information for a given publication year.

    Parameters
    ----------
    pub_year : int
        Publication year

    Returns
    -------
    tuple[str, str]
        Tuple of (era_name, era_emoji)
    """
    if pub_year < 1960:
        return "Golden Age (pre-1960)", "🏛️"
    if pub_year < 1980:
        return "New Wave (1960s-70s)", "🌊"
    if pub_year < 2000:
        return "Cyberpunk Era (1980s-90s)", "🤖"
    return "Modern Sci-Fi (2000+)", "🚀"


def calculate_era_comparison(
    book_year: int,
    book_rating: float,
    df: pl.DataFrame,
) -> tuple[float, bool]:
    """Calculate how a book compares to others in its era.

    Parameters
    ----------
    book_year : int
        Publication year of the book
    book_rating : float
        Club rating of the book
    df : pl.DataFrame
        DataFrame containing all books

    Returns
    -------
    tuple[float, bool]
        Tuple of (era_average_rating, is_above_average)
    """
    era_books = df.filter(
        pl.col("original_publication_year").is_between(book_year - 10, book_year + 10),
    )
    avg_era_rating = era_books["average_bookclub_rating"].mean()

    # Handle potential None from mean() operation
    if avg_era_rating is None:
        avg_era_rating = 0.0
        is_above_average = False
    else:
        is_above_average = book_rating > avg_era_rating

    return avg_era_rating, is_above_average


def calculate_rating_consensus(ratings: list[float]) -> tuple[float, str]:
    """Calculate rating consensus information.

    Parameters
    ----------
    ratings : list[float]
        List of member ratings for a book

    Returns
    -------
    tuple[float, str]
        Tuple of (rating_spread, consensus_level)
    """
    if not ratings:
        return 0.0, "No ratings"

    rating_spread = max(ratings) - min(ratings)

    if rating_spread < 1:
        consensus_level = "High consensus"
    elif rating_spread < 2:
        consensus_level = "Good agreement"
    else:
        consensus_level = "Mixed opinions"

    return rating_spread, consensus_level


def create_rating_comparison_section(selected_book: pd.Series) -> None:
    """Create rating comparison section showing Goodreads vs Club rating difference.

    This was moved from the main dashboard's Selected Book Deep Dive section.
    """
    # Show difference
    diff = selected_book["average_bookclub_rating"] - selected_book["average_goodreads_rating"]
    if diff > 0:
        st.success(f"📈 We rated it {diff:.2f} points higher than Goodreads!")
    elif diff < 0:
        st.error(f"📉 We rated it {abs(diff):.2f} points lower than Goodreads")
    else:
        st.info("🎯 Perfect match with Goodreads rating!")
