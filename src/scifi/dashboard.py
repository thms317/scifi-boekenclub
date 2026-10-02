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

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st

from scifi.analysis import (
    author_stats,
    books_per_decade,
    books_per_year,
    club_duration_label,
    countdown_label,
    current_meeting,
    member_correlations,
    member_stats,
    overview_metrics,
    rank_books,
    rating_trend,
    suggester_stats,
)
from scifi.data_processor import load_dashboard_data
from scifi.members import BookClubMembers
from scifi.visualizer import (
    create_club_vs_goodreads_discrepancies,
    create_member_rating_heatmap,
    create_polarizing_books_analysis,
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

    if not meeting or not meeting.books:
        st.info("No books scheduled yet.")
        return

    # Display each book in the meeting
    for book in meeting.books:
        year_display = f"{book.year}" if book.year else "N/A"
        pages_display = f"{book.pages}" if book.pages else "N/A"
        countdown_text = countdown_label(meeting.date, today)
        status = "Next Bookclub Meeting" if meeting.is_upcoming else "Last Bookclub Meeting"

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
                    <strong>{book.title}</strong> by <em>{book.author}</em> <span style="font-size: 1.0rem;">({year_display} | {pages_display} pages)</span>
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
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>{title}</h3>
                <h2>{value}</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )


def create_rating_scatter(bookclub_processed_df: pl.DataFrame) -> go.Figure:
    """Create fixed scatter plot with trendline for overview"""
    # Fixed scatter plot settings - inverted axes
    x_axis = "average_goodreads_rating"
    y_axis = "average_bookclub_rating"
    color_by = "original_publication_year"
    size_by = "average_goodreads_rating"

    # Prepare data for plotting - handle null values and filter out unrated books
    bookclub_processed_df_pandas = (
        bookclub_processed_df.with_columns(
            [
                pl.col("original_publication_year").fill_null(0).alias("original_publication_year"),
                pl.col("suggested_by").fill_null("Unknown").alias("suggested_by"),
            ]
        )
        .filter(
            # Exclude books with no ratings
            pl.col("average_bookclub_rating").is_not_null()
            & pl.col("average_goodreads_rating").is_not_null()
        )
        .to_pandas()
    )

    # Format date for display
    bookclub_processed_df_pandas["date_formatted"] = pd.to_datetime(
        bookclub_processed_df_pandas["date"]
    ).dt.strftime("%B %d, %Y")

    # Add perfect correlation line (x=y from 1 to 5) - FIRST so it's behind data
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[1, 5],
            y=[1, 5],
            mode="lines",
            name="Perfect Agreement",
            line={"color": "black", "width": 2, "dash": "dash"},
            opacity=0.5,
            showlegend=False,  # Remove from legend
        ),
    )

    # Create scatter plot with fixed settings
    scatter_fig = px.scatter(
        bookclub_processed_df_pandas,
        x=x_axis,
        y=y_axis,
        color=color_by,
        size=size_by,
        hover_data=["title", "author", "suggested_by", "date_formatted"],
        title="📚 Goodreads Rating vs Club Rating",
        template="plotly_dark",
        size_max=20,
        labels={color_by: "Publication Year", x_axis: "Club Rating", y_axis: "Goodreads Rating"},
    )

    # Add scatter traces to the main figure
    for trace in scatter_fig.data:
        fig.add_trace(trace)

    # Fixed axes 1-5 for both rating axes
    fig.update_layout(
        height=525,  # Reduced by 25% from 700
        font={"size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.1)",
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "title": "Publication Year",
        },
        xaxis={"range": [1, 5], "title": "Goodreads Rating"},
        yaxis={"range": [1, 5], "title": "Club Rating"},
    )

    # Enhanced hover template - handle null values
    fig.update_traces(
        marker={"line": {"width": 1, "color": "white"}, "opacity": 0.8},
        hovertemplate="<b>%{customdata[0]}</b><br>"
        "Author: %{customdata[1]}<br>"
        "Suggested by: %{customdata[2]}<br>"
        "Goodreads Rating: %{x:.1f}<br>"
        "Club Rating: %{y:.1f}<br>"
        "<extra></extra>",
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True, key="overview_scatter")

    return fig


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
        fig_comp = go.Figure()
        fig_comp.add_trace(
            go.Bar(
                x=["Goodreads", "Our Club"],
                y=[
                    selected_book["average_goodreads_rating"],
                    selected_book["average_bookclub_rating"],
                ],
                marker_color=["#FF6B6B", "#4ECDC4"],
                text=[
                    f"{selected_book['average_goodreads_rating']:.2f}",
                    f"{selected_book['average_bookclub_rating']:.2f}",
                ],
                textposition="auto",
            ),
        )

        fig_comp.update_layout(
            title="Rating Comparison",
            yaxis_title="Rating (1-5)",
            yaxis={"range": [0, 5]},
            template="plotly_dark",
            height=350,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with col3:
        # Member ratings radar chart
        st.subheader("👥 Member Ratings")
        member_ratings_data = []
        for member in members:
            rating = selected_book[member]
            if pd.notna(rating):
                member_ratings_data.append(rating)
            else:
                member_ratings_data.append(None)

        # Filter out None values for radar chart
        valid_ratings = [
            (member, rating)
            for member, rating in zip(members, member_ratings_data, strict=False)
            if rating is not None
        ]

        if valid_ratings:
            members_with_ratings, ratings_values = zip(*valid_ratings, strict=False)

            fig_radar = go.Figure()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=[*list(ratings_values), ratings_values[0]],
                    theta=[*list(members_with_ratings), members_with_ratings[0]],
                    fill="toself",
                    name=selected_book["title"][:20] + "...",
                    line_color="rgb(255, 195, 0)",
                    fillcolor="rgba(255, 195, 0, 0.3)",
                ),
            )

            fig_radar.update_layout(
                polar={
                    "radialaxis": {"visible": True, "range": [0, 5]},
                    "angularaxis": {
                        "tickmode": "array",
                        "tickvals": list(range(len(members_with_ratings))),
                        "ticktext": list(members_with_ratings),
                    },
                },
                showlegend=False,
                template="plotly_dark",
                height=400,
                margin={"l": 60, "r": 60, "t": 60, "b": 60},
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("No member ratings available for this book")

    return selected_book


def create_member_comparison(df: pl.DataFrame, members: list[str]) -> None:
    """Create member rating comparison"""
    st.subheader("👥 Member Rating Patterns")

    # Calculate member statistics
    stats_df = member_stats(df, members)
    stats_df = stats_df.select(
        pl.col("member").alias("Member"),
        pl.col("count").alias("Count"),
        pl.col("average").alias("Average"),
        pl.col("std_dev").alias("Std Dev"),
        pl.col("min").alias("Min"),
        pl.col("max").alias("Max"),
    )

    # Create clean comparison charts
    col1, col2 = st.columns(2)

    with col1:
        # Rating counts
        fig_counts = go.Figure()
        fig_counts.add_trace(
            go.Bar(
                x=stats_df["Member"],
                y=stats_df["Count"],
                marker_color="lightblue",
                text=stats_df["Count"],
                textposition="auto",
            ),
        )
        fig_counts.update_layout(
            title="📊 Books Rated by Each Member",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_counts, use_container_width=True)

    with col2:
        # Average ratings
        fig_avg = go.Figure()
        fig_avg.add_trace(
            go.Bar(
                x=stats_df["Member"],
                y=stats_df["Average"],
                marker_color="lightcoral",
                text=[f"{avg:.2f}" for avg in stats_df["Average"]],
                textposition="auto",
            ),
        )
        fig_avg.update_layout(
            title="⭐ Average Rating by Member",
            yaxis={"range": [1, 5]},
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_avg, use_container_width=True)


def create_time_analysis(df: pl.DataFrame) -> None:
    """Create time-based analysis"""
    st.subheader("📅 Reading Journey Over Time")

    col1, col2 = st.columns(2)

    with col1:
        # Books per year
        yearly_counts = books_per_year(df).to_pandas()

        fig_yearly = go.Figure()
        fig_yearly.add_trace(
            go.Bar(
                x=yearly_counts["year"],
                y=yearly_counts["count"],
                marker_color="skyblue",
                text=yearly_counts["count"],
                textposition="auto",
            ),
        )
        fig_yearly.update_layout(
            title="📚 Books Read Per Year",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_yearly, use_container_width=True)

    with col2:
        # Publication decades with outlined bars
        decade_counts = books_per_decade(df).to_pandas()

        fig_decades = go.Figure()
        fig_decades.add_trace(
            go.Bar(
                x=decade_counts["decade_label"],
                y=decade_counts["count"],
                marker={
                    "color": "lightgreen",
                    "line": {"color": "darkgreen", "width": 2},
                },
                text=decade_counts["count"],
                textposition="auto",
            ),
        )
        fig_decades.update_layout(
            title="📖 Books by Publication Decade",
            xaxis_title="Publication Decade",
            yaxis_title="Number of Books",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_decades, use_container_width=True)


def create_rating_trends_chart(df: pl.DataFrame) -> None:
    """Create rating trends over time chart (separate from time analysis)"""
    # Get trend data from analysis
    trend_data = rating_trend(df).to_pandas()

    fig_trend = go.Figure()

    # Linear trendline (background layer)
    valid_trend = trend_data.dropna(subset=["trend"])
    if len(valid_trend) > 1:
        fig_trend.add_trace(
            go.Scatter(
                x=valid_trend["date"],
                y=valid_trend["trend"],
                mode="lines",
                name="Linear Trend",
                line={"color": "grey", "width": 1, "dash": "dash"},
            ),
        )

    # Individual points (all books with ratings)
    rated_data = trend_data.dropna(subset=["average_bookclub_rating"])
    fig_trend.add_trace(
        go.Scatter(
            x=rated_data["date"],
            y=rated_data["average_bookclub_rating"],
            mode="markers",
            name="Individual Ratings",
            marker={"color": "lightblue", "size": 6, "opacity": 0.6},
            hovertemplate="<b>%{customdata}</b><br>Rating: %{y}<br>Date: %{x}<extra></extra>",
            customdata=rated_data["title"],
        ),
    )

    # 7-book moving average (foreground layer)
    valid_ma = trend_data.dropna(subset=["rolling_avg"])
    fig_trend.add_trace(
        go.Scatter(
            x=valid_ma["date"],
            y=valid_ma["rolling_avg"],
            mode="lines",
            name="7-Book Moving Average",
            line={"color": "orange", "width": 3},
        ),
    )

    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Rating",
        yaxis={"range": [0.5, 5.5]},
        template="plotly_dark",
        height=500,
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)


def create_suggester_analysis(df: pl.DataFrame) -> None:
    """Create jitter box plot showing ratings by book suggester"""
    st.subheader("🎯 Ratings by Book Suggester")
    st.write(
        "Distribution of average club ratings for books suggested by members (3+ books or active members)"
    )

    # Handle both column name possibilities
    suggester_col = "suggested_by" if "suggested_by" in df.columns else "blame"

    # Get active member names from BookClubMembers
    active_member_names = [member.name for member in BookClubMembers.get_active_members()]

    # Calculate average ratings per suggester using analysis function
    stats_result = suggester_stats(df, active_member_names)

    if stats_result is None or len(stats_result) == 0:
        st.warning("No members meet the criteria (3+ books or active members).")
        return

    # Create ordered list of suggesters (meeting criteria)
    stats_df = stats_result.to_pandas()
    ordered_suggesters = stats_df["suggested_by"].tolist()

    # Convert main dataframe to pandas for box plot
    df_pandas = df.to_pandas()

    # Create the jitter box plot
    fig = go.Figure()

    for suggester in ordered_suggesters:
        suggester_books = df_pandas[df_pandas[suggester_col] == suggester]
        ratings = suggester_books["average_bookclub_rating"].tolist()

        # Add stylized box plot with subtle design
        fig.add_trace(
            go.Box(
                x=[suggester] * len(ratings),
                y=ratings,
                name=suggester,
                boxpoints="all",  # Show all points with jitter
                jitter=0.4,  # Slightly more jitter for better spread
                pointpos=0,  # Center the points
                marker={
                    "size": 5,
                    "opacity": 0.6,
                    "color": "#555555",  # Dark gray points
                    "line": {"width": 0.5, "color": "white"},  # Subtle white outline on points
                },
                line={"color": "#333333", "width": 1.5},  # Slightly thinner dark outline
                fillcolor="rgba(240, 240, 240, 0.3)",  # Very light gray fill
                boxmean=True,  # Show mean as well as median
                customdata=suggester_books[["title", "author"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Author: %{customdata[1]}<br>"
                    "Rating: %{y:.2f}<br>"
                    f"Suggested by: {suggester}<br>"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.update_layout(
        xaxis_title="Book Suggester",
        yaxis_title="Average Club Rating",
        yaxis={
            "range": [1, 5],
            "gridcolor": "rgba(128, 128, 128, 0.2)",  # Subtle grid lines
            "gridwidth": 1,
        },
        xaxis={
            "tickangle": -45,
            "tickfont": {"size": 11},
            "gridcolor": "rgba(128, 128, 128, 0.1)",  # Very subtle vertical grid
        },
        template="plotly_white",  # Clean white background
        height=600,
        plot_bgcolor="rgba(250, 250, 250, 0.8)",  # Very light background
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif", "size": 12, "color": "#333333"},
        margin={"l": 60, "r": 20, "t": 20, "b": 80},  # Better spacing
    )

    # Create layout with violin plot and stats side by side
    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Simple stats display
        st.subheader("📈 Suggester Statistics")
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


def create_author_bar_chart(
    stats_df: pd.DataFrame, value_col: str, x_title: str, x_max: float, decimals: int
) -> go.Figure:
    """Create a horizontal bar chart of one author statistic per group"""
    # Groups without ratings (e.g. only an unrated book) get a label instead of NaN
    labels = [
        f"{value:.{decimals}f}" if pd.notna(value) else "no ratings"
        for value in stats_df[value_col]
    ]
    rating_labels = [
        f"{value:.2f}" if pd.notna(value) else "no ratings" for value in stats_df["avg_rating"]
    ]
    fig = go.Figure(
        go.Bar(
            x=stats_df[value_col],
            y=stats_df["group"],
            orientation="h",
            marker={"color": "#555555", "line": {"width": 2, "color": "white"}},
            customdata=list(zip(stats_df["book_count"], rating_labels, strict=True)),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Books: %{customdata[0]}<br>"
                "Avg club rating: %{customdata[1]}<br>"
                "<extra></extra>"
            ),
            text=labels,
            textposition="outside",
            textfont={"color": "#333333"},
            cliponaxis=False,
        )
    )
    fig.update_layout(
        xaxis_title=x_title,
        yaxis={"autorange": "reversed", "tickfont": {"size": 11}},
        # Leave headroom so the value labels outside the bars are not clipped
        xaxis={"range": [0, x_max], "gridcolor": "rgba(128, 128, 128, 0.2)"},
        template="plotly_white",
        height=max(250, 40 * len(stats_df) + 80),
        plot_bgcolor="rgba(250, 250, 250, 0.8)",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif", "size": 12, "color": "#333333"},
        margin={"l": 20, "r": 20, "t": 20, "b": 50},
        showlegend=False,
    )
    return fig


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

    stats_result = author_stats(df, group_col)
    stats_df = stats_result.to_pandas() if stats_result is not None else None

    if stats_df is None or len(stats_df) == 0:
        st.info(f"No data available for {dimension}.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📚 Books read**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_df,
                "book_count",
                "Number of books",
                x_max=stats_df["book_count"].max() * 1.15,
                decimals=0,
            ),
            use_container_width=True,
        )
    with col2:
        st.markdown("**⭐ Average club rating**")
        st.plotly_chart(
            create_author_bar_chart(
                stats_df, "avg_rating", "Average club rating (1-5)", x_max=5.6, decimals=2
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

    # Build correlation matrix from long-format data
    corr_pd = correlations.to_pandas()
    active_members = sorted(set(corr_pd["member_1"].tolist() + corr_pd["member_2"].tolist()))

    # Create matrix
    correlation_matrix = np.eye(len(active_members))
    member_to_idx = {m: i for i, m in enumerate(active_members)}

    for row in corr_pd.to_dict("records"):
        i = member_to_idx[row["member_1"]]
        j = member_to_idx[row["member_2"]]
        corr = row["correlation"]
        correlation_matrix[i][j] = corr if not pd.isna(corr) else 0
        correlation_matrix[j][i] = corr if not pd.isna(corr) else 0

    # Create enhanced heatmap with better styling
    # Reverse matrix rows to match reversed y-axis labels (diagonal at top-left)
    reversed_matrix = np.flipud(correlation_matrix)

    fig = go.Figure(
        data=go.Heatmap(
            z=reversed_matrix,
            x=active_members,
            y=list(reversed(active_members)),  # Reverse y-axis so diagonal starts top-left
            colorscale="RdYlGn",  # Red-Yellow-Green: Red=0, Yellow=0.5, Green=1
            zmin=-0.25,
            zmax=1,
            text=np.round(reversed_matrix, 3),
            texttemplate="%{text}",
            textfont={"size": 12, "color": "black"},
            hoverongaps=False,
            hovertemplate="<b>%{y} vs %{x}</b><br>Correlation: %{z:.3f}<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=600,
        width=600,
        xaxis_title="Member",
        yaxis_title="Member",
        xaxis={"side": "bottom"},
        font={"size": 12},
    )

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
        fig_discrepancies.update_layout(height=800)  # Increase height for better readability
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
        # Convert to pandas for sorting and date filtering
        bookclub_processed_df_pandas = bookclub_processed_df.to_pandas()
        bookclub_processed_df_pandas["date"] = pd.to_datetime(
            bookclub_processed_df_pandas["date"], errors="coerce"
        ).dt.date

        # Filter to only past books (exclude current/upcoming books)
        today = date.today()
        past_books = bookclub_processed_df_pandas[bookclub_processed_df_pandas["date"] < today]

        if len(past_books) > 0:
            # Sort past books by date (most recent first) and get titles
            book_titles = past_books.sort_values("date", ascending=False)["title"].tolist()
        else:
            # Fallback to all books if no past books found
            book_titles = bookclub_processed_df_pandas.sort_index(ascending=False)["title"].tolist()

        selected_book_title = st.selectbox(
            "Choose a book:", book_titles, key="overview_book_selector"
        )

        if selected_book_title:
            selected_book_data = (
                bookclub_processed_df.filter(pl.col("title") == selected_book_title)
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
            create_rating_scatter(bookclub_processed_df)

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
