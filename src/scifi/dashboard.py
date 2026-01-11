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
from scipy import stats

from scifi.data_processor import process_bookclub_data
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
            bookclub_processed_df, _unmatched_df, _goodreads_df = process_bookclub_data(
                goodreads_dir="data/goodreads/clean",
                bookclub_path="data/bookclub/bookclub.csv",
                manual_ratings_path="data/bookclub/manual_ratings.csv",
            )

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
            └── manual_ratings.csv (optional)
        """)
        st.stop()

    except (RuntimeError, ValueError, OSError) as e:
        st.error(f"❌ Error processing data: {e}")
        st.info("💡 Check the data file formats and try again.")
        st.stop()

    bookclub_members_list = BookClubMembers.get_member_names()

    # Data preprocessing for dashboard display
    bookclub_processed_df = bookclub_processed_df.with_columns(
        [
            # Date is already parsed by data processor, just create alias for compatibility
            pl.col("date").alias("date_parsed"),
            # Data types are already handled by data processor, but ensure float types for calculations
            *[
                pl.col(member).cast(pl.Float64, strict=False)
                for member in bookclub_members_list
                if member in bookclub_processed_df.columns
            ],
        ],
    )

    # Handle missing dates by using a default or removing rows
    bookclub_processed_df = bookclub_processed_df.filter(pl.col("date_parsed").is_not_null())

    return bookclub_processed_df, bookclub_members_list


def create_current_book_banner(bookclub_processed_df: pl.DataFrame) -> None:
    """Create a compact banner showing the current/next book with key stats"""
    today = date.today()

    # Convert polars dates to pandas for easier date handling
    df_pandas = bookclub_processed_df.to_pandas()
    df_pandas["date_parsed"] = pd.to_datetime(df_pandas["date_parsed"], errors="coerce").dt.date

    # Find current book (next future date or most recent if no future dates)
    future_books = df_pandas[df_pandas["date_parsed"] >= today].sort_values(
        "date_parsed", ascending=True
    )

    if len(future_books) > 0:
        current_book = future_books.iloc[0]
        days_diff = (current_book["date_parsed"] - today).days
        is_upcoming = True
    else:
        # No future books, show most recent
        current_book = df_pandas.sort_values("date_parsed").iloc[-1]
        days_diff = (today - current_book["date_parsed"]).days
        is_upcoming = False

    # Get book details
    title = str(current_book["title"])
    author = str(current_book["author"])
    date_formatted = current_book["date_parsed"].strftime("%b %d")

    # Handle ratings and book details
    # Get publication year and pages
    pub_year = current_book.get("original_publication_year")
    year_display = f"{int(pub_year)}" if pd.notna(pub_year) and pub_year > 0 else "N/A"

    pages = current_book.get("number_of_pages")
    pages_display = f"{int(pages)}" if pd.notna(pages) and pages > 0 else "N/A"

    # Create countdown text
    if is_upcoming:
        if days_diff == 0:
            countdown_text = f"{date_formatted} (TODAY)"
        elif days_diff == 1:
            countdown_text = f"{date_formatted} (TOMORROW)"
        else:
            countdown_text = f"{date_formatted} ({days_diff} days left)"
    else:
        countdown_text = f"{date_formatted} ({days_diff} days ago)"

    # Styled current book banner
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
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📖 Current Book</div>
            <div style="font-size: 1.3rem;">
                <strong>{title}</strong> by <em>{author}</em> <span style="font-size: 1.0rem;">({year_display} | {pages_display} pages)</span>
            </div>
        </div>
        <div style="font-size: 1.2rem; text-align: right;">
            Next Bookclub Meeting 📅<br><span style="font-size: 1.2rem;">{countdown_text}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def create_overview_metrics(bookclub_processed_df: pl.DataFrame, members: list[str]) -> None:
    """Create overview metrics cards"""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_books = len(bookclub_processed_df)
    avg_goodreads = float(bookclub_processed_df["average_goodreads_rating"].mean() or 0.0)
    avg_bookclub = float(bookclub_processed_df["average_bookclub_rating"].mean() or 0.0)
    most_active = max(members, key=lambda m: bookclub_processed_df[m].count())

    # Calculate bookclub duration
    bookclub_processed_df_pandas = bookclub_processed_df.to_pandas()
    first_date = bookclub_processed_df_pandas["date_parsed"].min()
    last_date = bookclub_processed_df_pandas["date_parsed"].max()
    duration = last_date - first_date
    years = duration.days // 365
    months = (duration.days % 365) // 30
    duration_text = f"{years}y {months}m" if years > 0 else f"{months}m"

    metrics = [
        ("📚 Total Books", total_books, col1),
        ("⭐ Goodreads Avg", f"{avg_goodreads:.2f}", col2),
        ("🎯 Club Avg", f"{avg_bookclub:.2f}", col3),
        ("👑 Most Active", str(most_active), col4),
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
        bookclub_processed_df_pandas["date_parsed"]
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
                <p><strong>📅 Read on:</strong> {pd.to_datetime(selected_book["date_parsed"]).strftime("%B %d, %Y")}</p>
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

        # Position in overall rankings - more informative display
        all_ratings = df["average_bookclub_rating"].drop_nulls().sort(descending=True)
        book_position = None
        for i, rating in enumerate(all_ratings):
            if (
                rating is not None
                and abs(rating - selected_book["average_bookclub_rating"]) < 0.001
            ):
                book_position = i + 1
                break

        if book_position:
            # Calculate percentile for better understanding
            percentile = ((len(df) - book_position + 1) / len(df)) * 100

            # Create informative ranking display

            # Big ranking number
            st.markdown(
                f"""
            <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;">
                <h1 style="font-size: 4rem; margin: 0; color: white;">#{book_position}</h1>
                <h3 style="margin: 0.5rem 0; color: white;">out of {len(df)} books</h3>
                <h4 style="margin: 0; opacity: 0.9; color: white;">Top {int(percentile)}% of club ratings</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

        else:
            st.warning("Could not determine ranking for this book.")

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
    member_stats = []
    for member in members:
        ratings = df[member].drop_nulls()
        if len(ratings) > 0:
            member_stats.append(
                {
                    "Member": member,
                    "Count": len(ratings),
                    "Average": ratings.mean(),
                    "Std Dev": ratings.std(),
                    "Min": ratings.min(),
                    "Max": ratings.max(),
                },
            )

    stats_df = pl.DataFrame(member_stats)

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

    df_pandas = df.to_pandas()
    df_pandas["year"] = df_pandas["date_parsed"].dt.year
    df_pandas["month"] = df_pandas["date_parsed"].dt.month

    # Sort by date for cleaner trends
    df_pandas = df_pandas.sort_values("date_parsed")

    col1, col2 = st.columns(2)

    with col1:
        # Books per year
        yearly_counts = df_pandas.groupby("year").size().reset_index(name="count")

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
        df_pandas["decade"] = (df_pandas["original_publication_year"] // 10) * 10
        decade_counts = df_pandas.groupby("decade").size().reset_index(name="count")
        decade_counts["decade_label"] = decade_counts["decade"].astype(str) + "s"

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
    df_pandas = df.to_pandas()
    df_pandas["date_parsed"] = pd.to_datetime(df_pandas["date_parsed"], errors="coerce").dt.date

    # Create rolling average for smoother trend
    df_pandas["rating_7ma"] = (
        df_pandas["average_bookclub_rating"].rolling(window=7, min_periods=1).mean()
    )

    # Calculate linear trendline
    # Convert dates to numeric for linear regression
    df_pandas["date_numeric"] = pd.to_numeric(pd.to_datetime(df_pandas["date_parsed"]))
    valid_ratings = df_pandas.dropna(subset=["average_bookclub_rating"])

    if len(valid_ratings) > 1:
        slope, intercept, _r_value, _p_value, _std_err = stats.linregress(
            valid_ratings["date_numeric"], valid_ratings["average_bookclub_rating"]
        )
        # Create trendline values
        trendline_y = slope * valid_ratings["date_numeric"] + intercept

    fig_trend = go.Figure()

    # Linear trendline (background layer)
    if len(valid_ratings) > 1:
        fig_trend.add_trace(
            go.Scatter(
                x=valid_ratings["date_parsed"],
                y=trendline_y,
                mode="lines",
                name="Linear Trend",
                line={"color": "grey", "width": 1, "dash": "dash"},
            ),
        )

    # Individual points
    fig_trend.add_trace(
        go.Scatter(
            x=df_pandas["date_parsed"],
            y=df_pandas["average_bookclub_rating"],
            mode="markers",
            name="Individual Ratings",
            marker={"color": "lightblue", "size": 6, "opacity": 0.6},
            hovertemplate="<b>%{customdata}</b><br>Rating: %{y}<br>Date: %{x}<extra></extra>",
            customdata=df_pandas["title"],
        ),
    )

    # 7-book moving average (foreground layer)
    fig_trend.add_trace(
        go.Scatter(
            x=df_pandas["date_parsed"],
            y=df_pandas["rating_7ma"],
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

    # Calculate average ratings per suggester for ordering, with combined filtering logic
    suggester_stats = (
        df.group_by(suggester_col)
        .agg(
            [
                pl.col("average_bookclub_rating").mean().alias("avg_rating"),
                pl.col("average_bookclub_rating").count().alias("book_count"),
            ]
        )
        .filter(
            # Show if: (3+ books) OR (active member with any books)
            (pl.col("book_count") >= 3) | (pl.col(suggester_col).is_in(active_member_names))
        )
        .sort("avg_rating", descending=True)
        .to_pandas()
    )

    if len(suggester_stats) == 0:
        st.warning("No members meet the criteria (3+ books or active members).")
        return

    # Create ordered list of suggesters (meeting criteria)
    ordered_suggesters = suggester_stats[suggester_col].tolist()

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
            suggester_stats[[suggester_col, "book_count", "avg_rating"]].round(2),
            use_container_width=True,
            hide_index=True,
            column_config={
                suggester_col: "Suggester",
                "book_count": "Books",
                "avg_rating": "Avg Rating",
            },
        )


def create_advanced_analytics(df: pl.DataFrame, members: list[str]) -> None:
    """Create advanced analytics section"""
    # CORRELATION ANALYSIS SECTION
    st.markdown("### 📊 Correlation Analysis")
    st.write("How similar are member tastes?")

    # Filter to active members with 5+ ratings
    active_members = []
    for member in members:
        rating_count = df[member].drop_nulls().len()
        if rating_count >= 5:
            active_members.append(member)

    if len(active_members) < 2:
        st.warning("Not enough members with 5+ ratings to create correlation analysis.")
        return

    # Create correlation matrix with book details
    correlation_data = []
    correlation_matrix = np.zeros((len(active_members), len(active_members)))
    correlation_books = {}  # Store books for each pair

    for i, member1 in enumerate(active_members):
        for j, member2 in enumerate(active_members):
            if i == j:
                correlation_matrix[i][j] = 1.0
            elif i < j:  # Only calculate upper triangle
                # Get books rated by both members
                both_rated = df.filter(
                    (pl.col(member1).is_not_null()) & (pl.col(member2).is_not_null()),
                )

                if len(both_rated) >= 3:  # Need at least 3 books for meaningful correlation
                    ratings1 = both_rated[member1].to_list()
                    ratings2 = both_rated[member2].to_list()

                    if len(set(ratings1)) > 1 and len(set(ratings2)) > 1:  # Need variance
                        corr = np.corrcoef(ratings1, ratings2)[0, 1]
                        correlation_matrix[i][j] = corr
                        correlation_matrix[j][i] = corr  # Mirror

                        # Store books for this pair
                        pair_key = f"{member1}-{member2}"
                        correlation_books[pair_key] = both_rated[
                            ["title", "author", member1, member2]
                        ].to_pandas()

                        # Store detailed info
                        correlation_data.append(
                            {
                                "Member1": member1,
                                "Member2": member2,
                                "Correlation": corr,
                                "Shared_Books": len(both_rated),
                            },
                        )
                    else:
                        correlation_matrix[i][j] = 0
                        correlation_matrix[j][i] = 0
                else:
                    correlation_matrix[i][j] = 0
                    correlation_matrix[j][i] = 0

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
        bookclub_processed_df_pandas["date_parsed"] = pd.to_datetime(
            bookclub_processed_df_pandas["date_parsed"], errors="coerce"
        ).dt.date

        # Filter to only past books (exclude current/upcoming books)
        today = date.today()
        past_books = bookclub_processed_df_pandas[
            bookclub_processed_df_pandas["date_parsed"] < today
        ]

        if len(past_books) > 0:
            # Sort past books by date (most recent first) and get titles
            book_titles = past_books.sort_values("date_parsed", ascending=False)["title"].tolist()
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

        # Create ranking dataframe
        ranking_df = bookclub_processed_df.select(
            [
                "title",
                "author",
                "original_publication_year",
                "number_of_pages",
                "suggested_by",
                "date_parsed",
                "average_goodreads_rating",
                "average_bookclub_rating",
            ],
        ).to_pandas()

        # Add ranking column
        ranking_df = ranking_df.sort_values("average_bookclub_rating", ascending=False).reset_index(
            drop=True,
        )
        ranking_df.insert(0, "Rank", range(1, len(ranking_df) + 1))

        # Convert date column to proper datetime for sorting
        ranking_df["date_parsed"] = pd.to_datetime(ranking_df["date_parsed"])

        # Rename columns for better display
        ranking_df = ranking_df.set_axis(
            [
                "Rank",
                "Title",
                "Author",
                "Year",
                "Pages",
                "Suggested By",
                "Read on",
                "Goodreads Rating",
                "Club Rating",
            ],
            axis=1,
        )

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
            st.write("The orange line shows a 7-book (+/- 1 year) moving average of club ratings.")
            create_rating_trends_chart(bookclub_processed_df)

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
