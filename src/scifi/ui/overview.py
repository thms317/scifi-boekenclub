"""Overview page of the Sci-Fi Book Club Analytics Dashboard."""

from datetime import date

import polars as pl
import streamlit as st

from scifi.analysis import current_meeting, rank_books
from scifi.data_processor import load_dashboard_data
from scifi.members import BookClubMembers
from scifi.visualizer import (
    create_member_radar,
    create_rating_comparison_bar,
)


def render() -> None:
    """Render the Overview page."""
    bookclub_processed_df = load_dashboard_data()
    members = BookClubMembers.get_member_names()

    # Add header
    _create_current_book_banner(bookclub_processed_df)
    _create_overview_metrics(bookclub_processed_df, members)

    # Book selection for detailed analysis
    st.markdown("---")
    st.subheader("🔍 Select a Book for Detailed Analysis")

    # Past books, newest first, and a title for each index
    today = date.today()
    book_indices = (
        bookclub_processed_df.filter(pl.col("date") < today)
        .sort("date", descending=True)["index"]
        .to_list()
    )
    book_index_to_title = dict(bookclub_processed_df.select("index", "title").iter_rows())

    selected_book_index = st.selectbox(
        "Choose a book:",
        options=book_indices,
        format_func=lambda idx: book_index_to_title.get(idx, f"Book {idx}"),
        key="overview_book_selector",
    )

    if selected_book_index is not None:
        selected_book_row = bookclub_processed_df.filter(
            pl.col("index") == selected_book_index
        ).row(0, named=True)
        _create_selected_book_analysis(selected_book_row, bookclub_processed_df, members)

    # Overall ranking table
    st.markdown("---")
    st.subheader("📋 Overall Book Rankings")
    st.write("**All books ranked by club average rating** (sortable by any column)")

    # Ranking with the other book columns; column_config sets the labels and number formats
    ranking_df = rank_books(bookclub_processed_df).join(
        bookclub_processed_df.select(
            "index",
            "original_publication_year",
            "number_of_pages",
            "suggested_by",
            "date",
            "average_goodreads_rating",
        ),
        on="index",
    )

    # Display sortable table
    st.dataframe(
        ranking_df.drop("index", "top_percent", "out_of_rated"),
        width="stretch",
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "author": st.column_config.TextColumn("Author", width="medium"),
            "original_publication_year": st.column_config.NumberColumn("Year", width="small"),
            "number_of_pages": st.column_config.NumberColumn("Pages", format="%.0f", width="small"),
            "suggested_by": st.column_config.TextColumn("Suggested By", width="small"),
            "date": st.column_config.DateColumn("Read on", format="MMM DD, YYYY", width="medium"),
            "average_goodreads_rating": st.column_config.NumberColumn(
                "Goodreads", format="%.2f", width="small"
            ),
            "average_bookclub_rating": st.column_config.NumberColumn(
                "Club", format="%.2f", width="small"
            ),
        },
    )


def _create_current_book_banner(bookclub_processed_df: pl.DataFrame) -> None:
    """Create a compact banner showing the current/next book with key stats.

    Parameters
    ----------
    bookclub_processed_df : pl.DataFrame
        The processed book club data.
    """
    today = date.today()
    meeting = current_meeting(bookclub_processed_df, today)
    meeting_date = meeting["date"][0]
    days = (meeting_date - today).days
    when = {0: "TODAY", 1: "TOMORROW"}.get(
        days, f"{days} days left" if days > 0 else f"{-days} days ago"
    )
    countdown_text = f"{meeting_date:%b %d} ({when})"
    status = "Next Bookclub Meeting" if days >= 0 else "Last Bookclub Meeting"

    # Display each book in the meeting
    for book in meeting.iter_rows(named=True):
        year, pages = book["original_publication_year"], book["number_of_pages"]
        year_display = f"{int(year)}" if year else "N/A"
        pages_display = f"{int(pages)}" if pages else "N/A"

        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1rem 2rem;
                    border-radius: 10px;
                    color: white;
                    margin: 1rem 0;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;">
            <div>
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📖 Book</div>
                <div style="font-size: 1.3rem;">
                    <strong>{book["title"]}</strong> by <em>{book["author"]}</em> <span style="font-size: 1.0rem;">({year_display} | {pages_display} pages)</span>
                </div>
            </div>
            <div style="font-size: 1.2rem; text-align: right;">
                {status} 📅<br><span style="font-size: 1.2rem;">{countdown_text}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def _create_overview_metrics(bookclub_processed_df: pl.DataFrame, members: list[str]) -> None:
    """Create overview metrics cards.

    Parameters
    ----------
    bookclub_processed_df : pl.DataFrame
        The processed book club data.
    members : list[str]
        List of member names.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    goodreads_avg, club_avg, first, last = bookclub_processed_df.select(
        pl.col("average_goodreads_rating").mean(),
        pl.col("average_bookclub_rating").mean(),
        pl.col("date").min().alias("first"),
        pl.col("date").max().alias("last"),
    ).row(0)
    years, days = divmod((last - first).days, 365)

    metrics = [
        ("📚 Total Books", len(bookclub_processed_df), col1),
        ("⭐ Goodreads Avg", f"{goodreads_avg:.2f}", col2),
        ("🎯 Club Avg", f"{club_avg:.2f}", col3),
        ("👑 Most Active", max(members, key=lambda m: bookclub_processed_df[m].count()), col4),
        ("⏰ Duration", f"{years}y {days // 30}m" if years else f"{days // 30}m", col5),
    ]

    for title, value, col in metrics:
        with col:
            st.markdown(
                f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                    margin: 0.2rem;
                    height: 100px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h3 style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{title}</h3>
                <h2 style="margin: 0.2rem 0 0 0; font-size: 1.8rem; font-weight: bold;">{value}</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )


def _create_selected_book_analysis(
    selected_book: dict,
    df: pl.DataFrame,
    members: list[str],
) -> None:
    """Create detailed analysis for a selected book.

    Parameters
    ----------
    selected_book : dict
        Dictionary row from the book club data.
    df : pl.DataFrame
        The processed book club data.
    members : list[str]
        List of member names.
    """
    # Book header with enhanced styling
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📖 {selected_book["title"]}</h1>
                <h2>✍️ by {selected_book["author"]}</h2>
                <p><strong>📅 Read on:</strong> {selected_book["date"]}</p>
                <p><strong>🏠 Location:</strong> {selected_book["location"]}</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 3em;">⭐</div>
                <div style="font-size: 1.5em;">{selected_book["average_bookclub_rating"]:.2f}</div>
                <div>Club Rating</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Create three columns for different analyses
    col1, col2, col3 = st.columns(3)

    with col1:
        # Book ranking and statistics
        st.subheader("📈 Book Rankings")

        # rank_books keeps every book, so the selected book is always there
        rank = rank_books(df).filter(pl.col("index") == selected_book["index"]).row(0, named=True)

        if rank["rank"] is None:
            st.info("This book has not been rated yet.")
        else:
            # Create informative ranking display
            st.markdown(
                f"""
            <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
                <h1 style="font-size: 4rem; margin: 0; color: white;">#{rank["rank"]}</h1>
                <h3 style="margin: 0.5rem 0; color: white;">out of {rank["out_of_rated"]} rated books</h3>
                <h4 style="margin: 0; opacity: 0.9; color: white;">Top {rank["top_percent"]}% of club ratings</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        # Rating comparisons
        st.subheader("📊 Rating Analysis")

        # Club vs Goodreads comparison
        fig_comp = create_rating_comparison_bar(selected_book)
        st.plotly_chart(fig_comp, width="stretch")

    with col3:
        # Member ratings radar chart
        st.subheader("👥 Member Ratings")
        member_ratings_dict = {member: selected_book.get(member) for member in members}

        fig_radar = create_member_radar(members, member_ratings_dict, selected_book["title"])
        if fig_radar.data:  # Check if figure has data
            st.plotly_chart(fig_radar, width="stretch")
        else:
            st.info("No member ratings available for this book")
