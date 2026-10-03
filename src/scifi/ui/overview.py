"""Overview page of the Sci-Fi Book Club Analytics Dashboard."""

from datetime import date
from html import escape

import polars as pl
import streamlit as st

from scifi.analysis import (
    club_duration_label,
    countdown_label,
    current_meeting,
    overview_metrics,
    past_books,
    rank_books,
)
from scifi.members import BookClubMembers
from scifi.ui.data import get_bookclub
from scifi.visualizer import (
    create_member_radar,
    create_rating_comparison_bar,
)


def render() -> None:
    """Render the Overview page."""
    bookclub_processed_df = get_bookclub()
    members = BookClubMembers.get_member_names()

    # Add header
    _create_current_book_banner(bookclub_processed_df)
    _create_overview_metrics(bookclub_processed_df, members)

    # Book selection for detailed analysis
    st.markdown("---")
    st.subheader("🔍 Select a Book for Detailed Analysis")

    # Get past books sorted by date (newest first)
    today = date.today()
    past_books_df = past_books(bookclub_processed_df, today)

    # Create list of indices and title mapping
    book_indices = past_books_df["index"].to_list()
    book_index_to_title = dict(
        zip(
            bookclub_processed_df["index"].to_list(),
            bookclub_processed_df["title"].to_list(),
            strict=False,
        )
    )

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

    # Create ranking dataframe using analysis function
    ranked = rank_books(bookclub_processed_df)

    # Join with original data to get other columns
    ranking_df = ranked.join(
        bookclub_processed_df.select(
            [
                "index",
                "original_publication_year",
                "number_of_pages",
                "suggested_by",
                "date",
                "average_goodreads_rating",
            ]
        ),
        on="index",
    )

    # Rename columns for better display
    ranking_df_display = ranking_df.rename(
        {
            "rank": "Rank",
            "title": "Title",
            "author": "Author",
            "original_publication_year": "Year",
            "number_of_pages": "Pages",
            "suggested_by": "Suggested By",
            "date": "Read on",
            "average_goodreads_rating": "Goodreads Rating",
            "average_bookclub_rating": "Club Rating",
        }
    )

    # Drop unnecessary columns
    ranking_df_display = ranking_df_display.drop(["index", "top_percent", "out_of_rated"])

    # Round ratings and pages
    ranking_df_display = ranking_df_display.with_columns(
        pl.col("Goodreads Rating").round(2),
        pl.col("Club Rating").round(2),
        pl.col("Pages").round(0),
    )

    # Display sortable table
    st.dataframe(
        ranking_df_display,
        width="stretch",
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Author": st.column_config.TextColumn("Author", width="medium"),
            "Year": st.column_config.NumberColumn("Year", width="small"),
            "Pages": st.column_config.NumberColumn("Pages", format="%.0f", width="small"),
            "Suggested By": st.column_config.TextColumn("Suggested By", width="small"),
            "Read on": st.column_config.DateColumn(
                "Read on", format="MMM DD, YYYY", width="medium"
            ),
            "Goodreads Rating": st.column_config.NumberColumn(
                "Goodreads",
                format="%.2f",
                width="small",
            ),
            "Club Rating": st.column_config.NumberColumn("Club", format="%.2f", width="small"),
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

    if not meeting or not meeting.books:
        st.info("No books scheduled yet.")
        return

    # Display meeting info in a container with border
    with st.container(border=True):
        col_left, col_right = st.columns([2, 1])

        # Display each book in the meeting
        with col_left:
            for i, book in enumerate(meeting.books):
                if i > 0:
                    st.divider()
                st.markdown(f"**📖 {book.title}** by *{book.author}*")
                year_display = f"{book.year}" if book.year else "N/A"
                pages_display = f"{book.pages}" if book.pages else "N/A"
                st.caption(f"{year_display} | {pages_display} pages")

        with col_right:
            countdown_text = countdown_label(meeting.date, today)
            status = "Next Bookclub Meeting" if meeting.is_upcoming else "Last Bookclub Meeting"
            st.markdown(f"**{status}** 📅")
            st.markdown(f"**{countdown_text}**")


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

    metrics_data = overview_metrics(bookclub_processed_df, members)
    duration_text = club_duration_label(metrics_data.first_date, metrics_data.last_date)

    metrics = [
        ("📚 Total Books", metrics_data.total_books, col1),
        ("⭐ Goodreads Avg", f"{metrics_data.goodreads_avg:.2f}", col2),
        ("🎯 Club Avg", f"{metrics_data.club_avg:.2f}", col3),
        ("👑 Most Active", str(metrics_data.most_active_member), col4),
        ("⏰ Duration", str(duration_text), col5),
    ]

    for title, value, col in metrics:
        with col:
            st.metric(label=title, value=value, border=True)


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
    # Book header with enhanced styling - escape CSV-derived values
    book_title = escape(str(selected_book["title"]))
    book_author = escape(str(selected_book["author"]))
    book_location = escape(str(selected_book.get("location", "N/A")))
    book_date = selected_book["date"].strftime("%B %d, %Y")

    # Format rating, handling None for unrated books
    rating_value = selected_book["average_bookclub_rating"]
    rating_display = f"{rating_value:.2f}" if rating_value is not None else "-"

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
                <h1>📖 {book_title}</h1>
                <h2>✍️ by {book_author}</h2>
                <p><strong>📅 Read on:</strong> {book_date}</p>
                <p><strong>🏠 Location:</strong> {book_location}</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 3em;">⭐</div>
                <div style="font-size: 1.5em;">{rating_display}</div>
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

        # Get book ranking using the analysis function
        ranked = rank_books(df)
        book_index = int(selected_book["index"])
        book_rank = ranked.filter(pl.col("index") == book_index)

        if len(book_rank) > 0:
            rank_row = book_rank.row(0, named=True)
            if rank_row["rank"] is not None:
                # Book is rated
                rank_value = int(rank_row["rank"])
                top_percent = int(rank_row["top_percent"])
                out_of_rated = int(rank_row["out_of_rated"])

                # Create informative ranking display
                st.markdown(
                    f"""
                <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
                    <h1 style="font-size: 4rem; margin: 0; color: white;">#{rank_value}</h1>
                    <h3 style="margin: 0.5rem 0; color: white;">out of {out_of_rated} rated books</h3>
                    <h4 style="margin: 0; opacity: 0.9; color: white;">Top {top_percent}% of club ratings</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                # Book is unrated
                st.info("This book has not been rated yet.")
        else:
            st.info("This book has not been rated yet.")

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
