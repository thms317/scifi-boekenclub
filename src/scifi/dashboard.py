"""
🚀 Sci-Fi Book Club Analytics Dashboard

This dashboard provides deep insights into your book club's reading patterns and preferences.
Key features:
- Overview scatter plot with trendline and 1-5 axes range
- Member correlation analysis with clickable shared book exploration
- Time-series analysis with decade publication views
- Book deep dive with ranking explanations

To run: streamlit run dashboard.py

Built with ❤️ using Streamlit, Plotly, and Polars
"""

from datetime import date

import pandas as pd
import polars as pl
import streamlit as st

from scifi.analysis import (
    current_meeting,
    member_correlations,
    rank_books,
    rating_trend,
    suggester_stats,
)
from scifi.data_processor import load_dashboard_data
from scifi.members import BookClubMembers
from scifi.visualizer import (
    create_author_bar_chart,
    create_books_per_decade_bar,
    create_books_per_year_bar,
    create_club_vs_goodreads_discrepancies,
    create_correlation_heatmap,
    create_member_average_bar,
    create_member_count_bar,
    create_member_radar,
    create_member_rating_heatmap,
    create_polarizing_books_analysis,
    create_rating_comparison_bar,
    create_rating_scatter,
    create_rating_trend_chart,
    create_suggester_box_plot,
)

# Page configuration
st.set_page_config(
    page_title="Sci-Fi Book Club Analytics",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for beautiful styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .main-header .rocket-emoji {
        -webkit-text-fill-color: initial;
        color: #667eea;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.2rem;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .metric-card h2 {
        margin: 0.2rem 0 0 0;
        font-size: 1.8rem;
        font-weight: bold;
    }
    .book-detail-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pl.DataFrame, list[str]]:
    """Load and preprocess the bookclub data using live data processing."""
    try:
        with st.spinner("🔄 Processing book club data from sources..."):
            # Run the data processing pipeline
            bookclub_processed_df = load_dashboard_data()

    except FileNotFoundError as e:
        st.error(f"📁 Data files not found: {e}")
        st.info("💡 Make sure your data files are in the correct directories:")
        st.code("""
        data/
        ├── goodreads/
        │   └── clean/
        │       └── [member CSV files]
        └── bookclub/
            ├── bookclub.csv
            ├── manual_ratings.csv (optional)
            └── authors.csv
        """)
        st.stop()

    except (RuntimeError, ValueError, OSError) as e:
        st.error(f"❌ Error processing data: {e}")
        st.info("💡 Check the data file formats and try again.")
        st.stop()

    bookclub_members_list = BookClubMembers.get_member_names()

    return bookclub_processed_df, bookclub_members_list


def create_current_book_banner(bookclub_processed_df: pl.DataFrame) -> None:
    """Create a compact banner showing the current/next book with key stats"""
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


def create_overview_metrics(bookclub_processed_df: pl.DataFrame, members: list[str]) -> None:
    """Create overview metrics cards"""
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
            <div class="metric-card">
                <h3>{title}</h3>
                <h2>{value}</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )


def create_selected_book_analysis(
    selected_book: pd.Series,
    df: pl.DataFrame,
    members: list[str],
) -> pd.Series:
    """Create detailed analysis for a selected book (triggered by scatter plot click)"""
    # st.markdown("### 🎯 Selected Book Deep Dive")

    # Book header with enhanced styling
    st.markdown(
        f"""
    <div class="book-detail-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📖 {selected_book["title"]}</h1>
                <h2>✍️ by {selected_book["author"]}</h2>
                <p><strong>📅 Read on:</strong> {pd.to_datetime(selected_book["date"]).strftime("%B %d, %Y")}</p>
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

        # Get book ranking using the analysis function
        ranked = rank_books(df)
        book_index = int(selected_book["index"])
        book_rank = ranked.filter(pl.col("index") == book_index).to_pandas()

        if not book_rank.empty and pd.notna(book_rank.iloc[0]["rank"]):
            # Book is rated
            rank_value = int(book_rank.iloc[0]["rank"])
            top_percent = int(book_rank.iloc[0]["top_percent"])
            out_of_rated = int(book_rank.iloc[0]["out_of_rated"])

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

    with col2:
        # Rating comparisons
        st.subheader("📊 Rating Analysis")

        # Club vs Goodreads comparison
        book_data = selected_book.to_dict()
        fig_comp = create_rating_comparison_bar(book_data)
        st.plotly_chart(fig_comp, use_container_width=True)

    with col3:
        # Member ratings radar chart
        st.subheader("👥 Member Ratings")
        member_ratings_dict = {member: selected_book[member] for member in members}

        fig_radar = create_member_radar(members, member_ratings_dict, selected_book["title"])
        if fig_radar.data:  # Check if figure has data
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("No member ratings available for this book")

    return selected_book


def create_member_comparison(df: pl.DataFrame, members: list[str]) -> None:
    """Create member rating comparison"""
    st.subheader("👥 Member Rating Patterns")

    # Calculate member statistics
    stats_df = (
        df.select(members)
        .unpivot(variable_name="Member", value_name="rating")
        .drop_nulls("rating")
        .group_by("Member", maintain_order=True)
        .agg(
            pl.len().alias("Count"),
            pl.col("rating").mean().alias("Average"),
            pl.col("rating").std().fill_null(0.0).alias("Std Dev"),
            pl.col("rating").min().alias("Min"),
            pl.col("rating").max().alias("Max"),
        )
    )

    # Create clean comparison charts
    col1, col2 = st.columns(2)

    with col1:
        # Rating counts
        fig_counts = create_member_count_bar(stats_df)
        st.plotly_chart(fig_counts, use_container_width=True)

    with col2:
        # Average ratings
        fig_avg = create_member_average_bar(stats_df)
        st.plotly_chart(fig_avg, use_container_width=True)


def create_time_analysis(df: pl.DataFrame) -> None:
    """Create time-based analysis"""
    st.subheader("📅 Reading Journey Over Time")

    col1, col2 = st.columns(2)

    with col1:
        # Books per year
        yearly_counts = (
            df.group_by(pl.col("date").dt.year().alias("year")).len("count").sort("year")
        )
        fig_yearly = create_books_per_year_bar(yearly_counts)
        st.plotly_chart(fig_yearly, use_container_width=True)

    with col2:
        # Publication decades with outlined bars
        decade_counts = (
            df.drop_nulls("original_publication_year")
            .group_by(decade=(pl.col("original_publication_year") // 10 * 10).cast(pl.UInt32))
            .len("count")
            .with_columns(decade_label=pl.col("decade").cast(pl.Utf8) + "s")
            .sort("decade")
        )
        fig_decades = create_books_per_decade_bar(decade_counts)
        st.plotly_chart(fig_decades, use_container_width=True)


def create_rating_trends_chart(df: pl.DataFrame) -> None:
    """Create rating trends over time chart (separate from time analysis)"""
    # Get trend data from analysis
    trend_data = rating_trend(df)
    fig_trend = create_rating_trend_chart(trend_data)
    st.plotly_chart(fig_trend, use_container_width=True)


def create_suggester_analysis(df: pl.DataFrame) -> None:
    """Create jitter box plot showing ratings by book suggester"""
    st.subheader("🎯 Ratings by Book Suggester")
    st.write(
        "Distribution of average club ratings for books suggested by members (3+ books or active members)"
    )

    # Get active member names from BookClubMembers
    active_member_names = [member.name for member in BookClubMembers.get_active_members()]

    # Calculate average ratings per suggester using analysis function
    stats_result = suggester_stats(df, active_member_names)

    if stats_result is None or len(stats_result) == 0:
        st.warning("No members meet the criteria (3+ books or active members).")
        return

    # Create the jitter box plot
    fig = create_suggester_box_plot(df, stats_result)

    # Create layout with violin plot and stats side by side
    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Simple stats display
        st.subheader("📈 Suggester Statistics")
        stats_df = stats_result.to_pandas()
        st.dataframe(
            stats_df[["suggested_by", "book_count", "avg_rating"]].round(2),
            use_container_width=True,
            hide_index=True,
            column_config={
                "suggested_by": "Suggester",
                "book_count": "Books",
                "avg_rating": "Avg Rating",
            },
        )


def create_author_analysis(df: pl.DataFrame) -> None:
    """Create charts of book counts and club ratings by author background"""
    st.subheader("✍️ Who Are We Reading?")
    st.write(
        "Author background for every book we read, one row per author in "
        "data/bookclub/authors.csv. LGBTQ+ only counts what is public; ethnicity is the "
        "club's judgement from public biographies."
    )

    dimensions = {
        "Gender": "gender",
        "Country": "country",
        "Religion": "religion",
        "LGBTQ+": "lgbtq",
        "Ethnicity": "ethnicity",
    }

    dimension = st.radio("Group authors by:", list(dimensions), horizontal=True)
    group_col = dimensions[dimension]

    stats_result = (
        df.drop_nulls("average_bookclub_rating")
        .group_by(pl.col(group_col).alias("group"))
        .agg(
            pl.len().alias("book_count"),
            pl.col("average_bookclub_rating").mean().alias("avg_rating"),
        )
        .sort("avg_rating", descending=True)
    )

    if len(stats_result) == 0:
        st.info(f"No data available for {dimension}.")
        return

    col1, col2 = st.columns(2)
    book_count_max = float(stats_result["book_count"].max())
    with col1:
        st.markdown("**📚 Books read**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_result,
                "book_count",
                "Number of books",
                x_max=book_count_max * 1.15,
                decimals=0,
            ),
            use_container_width=True,
        )
    with col2:
        st.markdown("**⭐ Average club rating**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_result, "avg_rating", "Average club rating (1-5)", x_max=5.6, decimals=2
            ),
            use_container_width=True,
        )
    st.caption(
        "Groups with only one or two books say little about taste; hover for counts. "
        "'onbekend' means unknown, not a default."
    )

    st.markdown("---")
    st.subheader("📋 Author Details per Book")
    st.dataframe(
        df.sort("date", descending=True)
        .select(
            "title",
            "author",
            "date",
            *dimensions.values(),
            "average_bookclub_rating",
        )
        .to_pandas()
        .round({"average_bookclub_rating": 2}),
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title", width="large"),
            "author": st.column_config.TextColumn("Author", width="medium"),
            "date": st.column_config.DateColumn("Read on", format="MMM DD, YYYY"),
            **{col: label for label, col in dimensions.items()},
            "average_bookclub_rating": st.column_config.NumberColumn("Club", format="%.2f"),
        },
    )


def create_advanced_analytics(df: pl.DataFrame, members: list[str]) -> None:
    """Create advanced analytics section"""
    # CORRELATION ANALYSIS SECTION
    st.markdown("### 📊 Correlation Analysis")
    st.write("How similar are member tastes?")

    # Get member correlations using analysis function
    correlations = member_correlations(df, members)

    if correlations is None or len(correlations) == 0:
        st.warning("Not enough members with 5+ ratings to create correlation analysis.")
        return

    # Create enhanced heatmap
    fig = create_correlation_heatmap(correlations)

    # Display correlation plot
    st.plotly_chart(fig, use_container_width=True, key="correlation_heatmap")

    # Section 1: Most Polarizing Books
    st.markdown("---")
    st.subheader("🤯 Most Polarizing Books")
    st.write("Books with the highest rating standard deviation - where members disagreed the most.")

    try:
        fig_polarizing = create_polarizing_books_analysis(df, members)
        st.plotly_chart(fig_polarizing, use_container_width=True)
    except (ValueError, KeyError, AttributeError) as e:
        st.error(f"Error creating polarizing books chart: {e}")

    # Section 2: Club vs Goodreads Discrepancies
    st.markdown("---")
    st.subheader("🎯 Club vs Goodreads Discrepancies")
    st.write("Books where our club ratings differ most from the general Goodreads community.")

    try:
        fig_discrepancies = create_club_vs_goodreads_discrepancies(df)
        st.plotly_chart(fig_discrepancies, use_container_width=True)
    except (ValueError, KeyError, AttributeError) as e:
        st.error(f"Error creating discrepancies chart: {e}")


def main() -> None:
    """Run Streamlit dashboard"""
    # Main header
    st.markdown(
        '<h1 class="main-header"><span class="rocket-emoji">🚀</span> Sci-Fi Book Club Analytics Dashboard</h1>',
        unsafe_allow_html=True,
    )

    # Load data
    bookclub_processed_df, members = load_data()

    # Sidebar
    st.sidebar.markdown("## 🎛️ Dashboard Controls")
    st.sidebar.markdown("Navigate through different sections to explore your book club data!")

    # Page selection
    page = st.sidebar.radio(
        "Choose Analysis:",
        [
            "📊 Overview",
            "👥 Member Insights",
            "📅 Time Analysis",
            "✍️ Author Insights",
            "🔬 Advanced Analytics",
        ],
    )

    # Main content based on selection
    if page == "📊 Overview":
        # Add header at the top
        create_current_book_banner(bookclub_processed_df)
        create_overview_metrics(bookclub_processed_df, members)

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
            selected_book_data = (
                bookclub_processed_df.filter(pl.col("index") == selected_book_index)
                .to_pandas()
                .iloc[0]
            )
            create_selected_book_analysis(selected_book_data, bookclub_processed_df, members)

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
        ).to_pandas()

        # Rename columns for better display
        ranking_df = ranking_df.rename(
            columns={
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

        # Drop the index column
        ranking_df = ranking_df.drop(columns=["index", "top_percent", "out_of_rated"])

        # Convert date column to proper datetime for sorting
        ranking_df["Read on"] = pd.to_datetime(ranking_df["Read on"])

        # Round ratings and pages
        ranking_df["Goodreads Rating"] = ranking_df["Goodreads Rating"].round(2)
        ranking_df["Club Rating"] = ranking_df["Club Rating"].round(2)
        ranking_df["Pages"] = ranking_df["Pages"].round(0)

        # Display sortable table
        st.dataframe(
            ranking_df,
            use_container_width=True,
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

    elif page == "👥 Member Insights":
        # Add member rating heatmap at the top of Member Insights page
        try:
            fig_heatmap = create_member_rating_heatmap(bookclub_processed_df, members)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        except (ValueError, KeyError, AttributeError) as e:
            st.error(f"Error creating member rating heatmap: {e}")

        create_member_comparison(bookclub_processed_df, members)

        # Add suggester violin plot
        st.markdown("---")
        create_suggester_analysis(bookclub_processed_df)

    elif page == "📅 Time Analysis":
        # First show the time analysis with bar charts
        create_time_analysis(bookclub_processed_df)

        # Then show the two main charts side by side
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📚 Goodreads vs Club Ratings")
            st.write(
                "Points above the diagonal line indicate books we rated higher than Goodreads users."
            )
            fig = create_rating_scatter(bookclub_processed_df)
            st.plotly_chart(fig, use_container_width=True, key="overview_scatter")

        with col2:
            st.subheader("📈 Rating Trends Over Time")
            st.write("The orange line shows a 7-book moving average of club ratings.")
            create_rating_trends_chart(bookclub_processed_df)

    elif page == "✍️ Author Insights":
        create_author_analysis(bookclub_processed_df)

    elif page == "🔬 Advanced Analytics":
        create_advanced_analytics(bookclub_processed_df, members)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 2rem;'>
            📚 Built with ❤️ for the Sci-Fi Book Club |
            Powered by Streamlit, Plotly & Polars
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
