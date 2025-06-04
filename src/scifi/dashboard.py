"""
🚀 Comprehensive Sci-Fi Book Club Analytics Dashboard

This dashboard provides deep insights into your book club's reading patterns and preferences.
Key features:
- Fixed overview scatter plot with trendline and 1-5 axes range
- Member correlation analysis with clickable shared book exploration
- Time-series analysis with decade publication views
- Book deep dive with ranking explanations
- Beautiful, modern UI with uniform metric cards

To run: streamlit run dashboard.py
Make sure bookclub_processed.csv is in the data/ directory!

Built with ❤️ using Streamlit, Plotly, and Polars
"""

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
import polars as pl
import streamlit as st

from scifi.utils import get_reviewer_mapping

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
    """Load and preprocess the bookclub data"""
    try:
        # Read from the specified data directory
        bookclub_processed_df = pl.read_csv("data/bookclub_processed.csv")
    except:  # noqa: E722
        # If file not found, show instructions
        st.error("📁 Please upload your 'bookclub_processed.csv' file to the data/ directory.")
        st.info("💡 Place the CSV file in the data/ folder and refresh the page.")
        st.stop()

    bookclub_members_list = list(get_reviewer_mapping().values())

    # Data preprocessing
    bookclub_processed_df = bookclub_processed_df.with_columns(
        [
            # Handle date parsing more flexibly
            pl.when(pl.col("date").is_not_null())
            .then(pl.col("date").str.strptime(pl.Date, format="%Y-%m-%dT%H:%M:%S%.f", strict=False))
            .otherwise(None)
            .alias("date_parsed"),
            # Ensure proper data types
            pl.col("original_publication_year").cast(pl.Int64, strict=False),
            pl.col("average_goodreads_rating").cast(pl.Float64, strict=False),
            pl.col("average_bookclub_rating").cast(pl.Float64, strict=False),
            # Handle member ratings
            *[pl.col(member).cast(pl.Float64, strict=False) for member in bookclub_members_list],
        ],
    )

    # Handle missing dates by using a default or removing rows
    bookclub_processed_df = bookclub_processed_df.filter(pl.col("date_parsed").is_not_null())

    return bookclub_processed_df, bookclub_members_list


def create_overview_metrics(bookclub_processed_df: pl.DataFrame, members: list[str]) -> None:
    """Create overview metrics cards"""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_books = len(bookclub_processed_df)
    avg_goodreads = bookclub_processed_df["average_goodreads_rating"].mean()
    avg_bookclub = bookclub_processed_df["average_bookclub_rating"].mean()
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
        ("⭐ Goodreads Avg", f"{avg_goodreads:.2f}", col2),  # type: ignore[str-bytes-safe]
        ("🎯 Club Avg", f"{avg_bookclub:.2f}", col3),  # type: ignore[str-bytes-safe]
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


def create_rating_scatter(bookclub_processed_df: pl.DataFrame, members: list[str]) -> go.Figure:
    """Create fixed scatter plot with trendline for overview"""
    st.subheader("📊 Goodreads vs Club Ratings")
    st.write("✨ **Hover over to see detailed analysis!**")

    # Fixed scatter plot settings
    x_axis = "average_bookclub_rating"
    y_axis = "average_goodreads_rating"
    color_by = "original_publication_year"
    size_by = "average_goodreads_rating"

    # Prepare data for plotting
    bookclub_processed_df_pandas = bookclub_processed_df.to_pandas()

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
        hover_data=["title", "author", "blame", "date"],
        title="📚 Goodreads Rating vs Club Rating",
        template="plotly_dark",
        size_max=20,
    )

    # Add scatter traces to the main figure
    for trace in scatter_fig.data:
        fig.add_trace(trace)

    # Fixed axes 1-5 for both rating axes
    fig.update_layout(
        height=700,
        title_font_size=24,
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
        },
        xaxis={"range": [1, 5], "title": "Club Rating"},
        yaxis={"range": [1, 5], "title": "Goodreads Rating"},
    )

    # Enhanced hover template
    fig.update_traces(
        marker={"line": {"width": 1, "color": "white"}, "opacity": 0.8},
        hovertemplate="<b>%{customdata[0]}</b><br>"
        "Author: %{customdata[1]}<br>"
        "Suggested by: %{customdata[2]}<br>"
        "Club Rating: %{x}<br>"
        "Goodreads Rating: %{y}<br>"
        "<extra></extra>",
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True, key="overview_scatter")

    # Book selection for detailed analysis
    st.markdown("---")
    st.subheader("🔍 Select a Book for Detailed Analysis")
    book_titles = bookclub_processed_df_pandas["title"].to_list()
    selected_book_title = st.selectbox("Choose a book:", book_titles, key="overview_book_selector")

    if selected_book_title:
        selected_book_data = (
            bookclub_processed_df.filter(pl.col("title") == selected_book_title).to_pandas().iloc[0]
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
            "blame",
            "original_publication_year",
            "average_goodreads_rating",
            "average_bookclub_rating",
        ],
    ).to_pandas()

    # Add ranking column
    ranking_df = ranking_df.sort_values("average_bookclub_rating", ascending=False).reset_index(
        drop=True,
    )
    ranking_df.insert(0, "Rank", range(1, len(ranking_df) + 1))

    # Rename columns for better display
    ranking_df.columns = [
        "Rank",
        "Title",
        "Author",
        "Suggested By",
        "Published",
        "Goodreads Rating",
        "Club Rating",
    ]

    # Round ratings
    ranking_df["Goodreads Rating"] = ranking_df["Goodreads Rating"].round(2)
    ranking_df["Club Rating"] = ranking_df["Club Rating"].round(2)

    # Display sortable table
    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Author": st.column_config.TextColumn("Author", width="medium"),
            "Suggested By": st.column_config.TextColumn("Suggested By", width="small"),
            "Published": st.column_config.NumberColumn("Published", width="small"),
            "Goodreads Rating": st.column_config.NumberColumn(
                "Goodreads",
                format="%.2f",
                width="small",
            ),
            "Club Rating": st.column_config.NumberColumn("Club", format="%.2f", width="small"),
        },
    )

    return fig


def create_selected_book_analysis(
    selected_book: pd.Series,  # type: ignore[type-arg]
    df: pl.DataFrame,
    members: list[str],
) -> pd.Series:  # type: ignore[type-arg]
    """Create detailed analysis for a selected book (triggered by scatter plot click)"""
    st.markdown("### 🎯 Selected Book Deep Dive")

    # Book header with enhanced styling
    st.markdown(
        f"""
    <div class="book-detail-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📖 {selected_book["title"]}</h1>
                <h2>✍️ by {selected_book["author"]}</h2>
                <p><strong>📅 Read on:</strong> {selected_book["date_parsed"]}</p>
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
                },
                showlegend=False,
                template="plotly_dark",
                height=350,
                margin={"l": 0, "r": 0, "t": 30, "b": 0},
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("No member ratings available for this book")

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

        # Show difference
        diff = selected_book["average_bookclub_rating"] - selected_book["average_goodreads_rating"]
        if diff > 0:
            st.success(f"📈 We rated it {diff:.2f} points higher than Goodreads!")
        elif diff < 0:
            st.error(f"📉 We rated it {abs(diff):.2f} points lower than Goodreads")
        else:
            st.info("🎯 Perfect match with Goodreads rating!")

    with col3:
        # Book ranking and statistics
        st.subheader("📈 Book Rankings")

        # Position in overall rankings - more informative display
        all_ratings = df["average_bookclub_rating"].sort(descending=True)
        book_position = None
        for i, rating in enumerate(all_ratings):
            if abs(rating - selected_book["average_bookclub_rating"]) < 0.001:
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

            # Ranking breakdown
            if percentile >= 90:
                st.success("🏆 **Exceptional!** This is one of our highest-rated books!")
            elif percentile >= 75:
                st.info("⭐ **Great choice!** Well above average rating.")
            elif percentile >= 50:
                st.warning("📚 **Solid book.** Above median rating.")
            elif percentile >= 25:
                st.warning("📖 **Mixed reception.** Below average rating.")
            else:
                st.error("😬 **Tough crowd.** This one didn't land well with us.")

            # Additional context
            books_above = book_position - 1
            books_below = len(df) - book_position
            st.caption(f"📈 {books_above} books rated higher • {books_below} books rated lower")

        else:
            st.warning("Could not determine ranking for this book.")

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
            st.success(f"📈 Above average for its era! ({avg_era_rating:.2f})")  # type: ignore[str-bytes-safe]
        else:
            st.info(f"📊 Era average: {avg_era_rating:.2f}")  # type: ignore[str-bytes-safe]

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

    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Summary Stats", "🔍 Individual Book Ratings"])

    with tab1:
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

        # Show member activity summary table
        st.subheader("📋 Member Activity Summary")

        # Create a nice summary table
        summary_data = []
        for member in members:
            ratings = df[member].drop_nulls()
            member_books = df.filter(pl.col(member).is_not_null())

            if len(ratings) > 0:
                # Get favorite book (highest rated)
                favorite_book = member_books.filter(pl.col(member) == ratings.max())[
                    "title"
                ].to_list()[0]

                summary_data.append(
                    {
                        "Member": member,
                        "Books Rated": len(ratings),
                        "Average Rating": f"{ratings.mean():.2f}",  # type: ignore[str-bytes-safe]
                        "Favorite Book": str(favorite_book),
                    },
                )
            else:
                summary_data.append(
                    {
                        "Member": member,
                        "Books Rated": 0,
                        "Average Rating": "N/A",
                        "Favorite Book": "N/A",
                    },
                )

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        # Individual book ratings scatter plot with violin plot background
        st.subheader("🔍 Individual Book Ratings by Member")
        st.write(
            "Scatter points show individual book ratings with violin plot distributions in the background",
        )

        # Create combined plot
        fig_individual = go.Figure()

        df_pandas = df.to_pandas()
        colors = ["lightblue", "lightcoral", "lightgreen", "orange", "purple", "pink"]

        # First, add violin plots as background (more transparent)
        for i, member in enumerate(members):
            member_ratings = df[member].drop_nulls().to_list()
            if member_ratings and len(member_ratings) >= 3:  # Need at least 3 ratings for violin
                fig_individual.add_trace(
                    go.Violin(
                        x=[i] * len(ratings),
                        y=member_ratings,
                        name=f"{member} Distribution",
                        line_color=colors[i % len(colors)],
                        fillcolor=colors[i % len(colors)],
                        opacity=0.3,  # Make transparent for background
                        side="both",
                        width=0.6,
                        points=False,  # Don't show individual points on violin
                        box_visible=False,  # Don't show box plot
                        meanline_visible=False,
                        showlegend=False,  # Don't clutter legend
                    ),
                )

        # Then, add scatter points on top
        for i, member in enumerate(members):
            member_books_mask = df_pandas[member].notna()
            member_books_df = df_pandas[member_books_mask]
            if len(member_books_df) > 0:
                # Add some horizontal spread manually to avoid overlap
                rng = np.random.default_rng()
                x_positions = [i + rng.uniform(-0.15, 0.15) for _ in range(len(member_books_df))]

                fig_individual.add_trace(
                    go.Scatter(
                        x=x_positions,
                        y=member_books_df[member],
                        mode="markers",
                        name=member,
                        marker={
                            "color": colors[i % len(colors)],
                            "size": 8,
                            "opacity": 0.8,  # More opaque than violin
                            "line": {"width": 1, "color": "white"},
                        },
                        text=member_books_df["title"],
                        hovertemplate="<b>%{text}</b><br>"
                        f"{member}: %{{y}}<br>"
                        "Author: %{customdata[0]}<br>"
                        "Year: %{customdata[1]}<br>"
                        "<extra></extra>",
                        customdata=member_books_df[["author", "original_publication_year"]].values,
                    ),
                )

        fig_individual.update_layout(
            title="Individual Book Ratings with Distribution Background",
            xaxis={
                "tickvals": list(range(len(members))),
                "ticktext": members,
                "title": "Member",
            },
            yaxis_title="Rating",
            yaxis={"range": [0.5, 5.5]},
            template="plotly_dark",
            height=600,
            showlegend=True,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        st.plotly_chart(fig_individual, use_container_width=True)


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
                    "line": {"color": "darkgreen", "width": 2},  # Add outline
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

    # Rating trend over time (with extended y-range)
    st.subheader("📈 Rating Trends Over Time")

    # Create rolling average for smoother trend
    df_pandas["rating_7ma"] = (
        df_pandas["average_bookclub_rating"].rolling(window=7, min_periods=1).mean()
    )

    fig_trend = go.Figure()

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

    # Trend line
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
        title="Club Rating Trend Over Time",
        xaxis_title="Date",
        yaxis_title="Rating",
        yaxis={"range": [0.5, 5.5]},  # Extended range so dots don't fall off
        template="plotly_dark",
        height=500,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")
    st.write("**Reading Trends and Patterns Over Time**")

    # Calculate yearly trends
    yearly_data = (
        df_pandas.groupby("year")
        .agg(
            {
                "average_bookclub_rating": "mean",
                "average_goodreads_rating": "mean",
                "title": "count",
            },
        )
        .reset_index()
    )
    yearly_data.columns = ["year", "club_rating", "goodreads_rating", "book_count"]

    col1, col2 = st.columns(2)

    with col1:
        # Rating trends
        fig_trend_yearly = go.Figure()
        fig_trend_yearly.add_trace(
            go.Scatter(
                x=yearly_data["year"],
                y=yearly_data["club_rating"],
                name="Club Average",
                line={"color": "cyan", "width": 3},
                mode="lines+markers",
            ),
        )
        fig_trend_yearly.add_trace(
            go.Scatter(
                x=yearly_data["year"],
                y=yearly_data["goodreads_rating"],
                name="Goodreads Average",
                line={"color": "orange", "width": 3},
                mode="lines+markers",
            ),
        )
        fig_trend_yearly.update_layout(
            title="Average Ratings by Year",
            yaxis={"range": [1, 5]},
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_trend_yearly, use_container_width=True)

    with col2:
        # Books per year trend
        fig_count_trend = go.Figure()
        fig_count_trend.add_trace(
            go.Bar(
                x=yearly_data["year"],
                y=yearly_data["book_count"],
                marker_color="lightgreen",
                text=yearly_data["book_count"],
                textposition="auto",
            ),
        )
        fig_count_trend.update_layout(
            title="Books Read Per Year Trend",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig_count_trend, use_container_width=True)


def create_book_selector(df: pl.DataFrame, members: list[str]) -> None:
    """Create interactive book selector with detailed view"""
    st.subheader("🔍 Book Deep Dive")

    # Book selector
    book_titles = df["title"].to_list()
    selected_book_title = st.selectbox("Select a book for detailed analysis:", book_titles)

    # Get selected book data
    selected_book = df.filter(pl.col("title") == selected_book_title).to_pandas().iloc[0]

    # Create detailed book view
    st.markdown(
        f"""
    <div class="book-detail-card">
        <h2>📖 {selected_book["title"]}</h2>
        <h3>✍️ by {selected_book["author"]}</h3>
        <div style="display: flex; justify-content: space-between; margin: 1rem 0;">
            <div><strong>Published:</strong> {selected_book["original_publication_year"]}</div>
            <div><strong>Suggested by:</strong> {selected_book["blame"]}</div>
            <div><strong>Goodreads:</strong> ⭐ {selected_book["average_goodreads_rating"]:.2f}</div>
            <div><strong>Club Average:</strong> 🎯 {selected_book["average_bookclub_rating"]:.2f}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Member ratings visualization for selected book
    member_ratings = []
    for member in members:
        rating = selected_book[member]
        if not pd.isna(rating):
            member_ratings.append({"Member": member, "Rating": rating})

    if member_ratings:
        pl.DataFrame(member_ratings)

        # Create radar chart for member ratings
        fig = go.Figure()

        ratings_list = [r["Rating"] for r in member_ratings]
        members_list = [r["Member"] for r in member_ratings]

        fig.add_trace(
            go.Scatterpolar(
                r=[*ratings_list, ratings_list[0]],  # Close the radar
                theta=[*members_list, members_list[0]],
                fill="toself",
                name=selected_book["title"],
                line_color="rgb(255, 195, 0)",
            ),
        )

        fig.update_layout(
            polar={
                "radialaxis": {
                    "visible": True,
                    "range": [0, 5],
                },
            },
            showlegend=True,
            title=f"Member Ratings for '{selected_book['title']}'",
            template="plotly_dark",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Comparison with club averages
        st.subheader("📊 How does this book compare?")

        col1, col2 = st.columns(2)

        with col1:
            # Rating comparison
            fig_comp = go.Figure()
            fig_comp.add_trace(
                go.Bar(
                    x=["Goodreads", "Our Club"],
                    y=[
                        selected_book["average_goodreads_rating"],
                        selected_book["average_bookclub_rating"],
                    ],
                    marker_color=["lightblue", "lightcoral"],
                ),
            )
            fig_comp.update_layout(
                title="Rating Comparison",
                yaxis_title="Rating",
                template="plotly_dark",
                height=400,
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with col2:
            # Position in overall rankings - more informative display
            all_ratings = df["average_bookclub_rating"].sort(descending=True)
            book_position = None
            for i, rating in enumerate(all_ratings):
                if abs(rating - selected_book["average_bookclub_rating"]) < 0.001:
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

                # Ranking breakdown
                if percentile >= 90:
                    st.success("🏆 **Exceptional!** This is one of our highest-rated books!")
                elif percentile >= 75:
                    st.info("⭐ **Great choice!** Well above average rating.")
                elif percentile >= 50:
                    st.warning("📚 **Solid book.** Above median rating.")
                elif percentile >= 25:
                    st.warning("📖 **Mixed reception.** Below average rating.")
                else:
                    st.error("😬 **Tough crowd.** This one didn't land well with us.")

                # Additional context
                books_above = book_position - 1
                books_below = len(df) - book_position
                st.caption(f"📈 {books_above} books rated higher • {books_below} books rated lower")

            else:
                st.warning("Could not determine ranking for this book.")


def create_advanced_analytics(df: pl.DataFrame, members: list[str]) -> None:
    """Create advanced analytics section"""
    # CORRELATION ANALYSIS SECTION
    st.markdown("### 📊 Correlation Analysis")

    # Create correlation matrix with book details
    correlation_data = []
    correlation_matrix = np.zeros((len(members), len(members)))
    correlation_books = {}  # Store books for each pair

    for i, member1 in enumerate(members):
        for j, member2 in enumerate(members):
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

    # Create enhanced heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix,
            x=members,
            y=members,
            colorscale="RdBu",
            zmid=0,
            text=np.round(correlation_matrix, 3),
            texttemplate="%{text}",
            textfont={"size": 14},
            hoverongaps=False,
            customdata=np.array(
                [
                    [f"{members[i]}-{members[j]}" for j in range(len(members))]
                    for i in range(len(members))
                ],
            ),
        ),
    )

    fig.update_layout(
        title="Member Rating Correlations (Dark Blue = Similar Taste)",
        template="plotly_dark",
        height=500,
        xaxis_title="Member",
        yaxis_title="Member",
    )

    # Display correlation plot with click detection
    st.plotly_chart(fig, use_container_width=True, key="correlation_heatmap")

    # Alternative: Use selectbox for member pair selection instead of click detection
    st.markdown("**Select Member Pair to See Shared Books:**")
    col1, col2 = st.columns(2)
    with col1:
        member1_select = st.selectbox("First Member:", members, key="corr_member1")
    with col2:
        member2_select = st.selectbox(
            "Second Member:",
            [m for m in members if m != member1_select],
            key="corr_member2",
        )

    # Show shared books for selected pair
    if member1_select != member2_select:
        pair_key = (
            f"{member1_select}-{member2_select}"
            if f"{member1_select}-{member2_select}" in correlation_books
            else f"{member2_select}-{member1_select}"
        )

        if pair_key in correlation_books:
            st.markdown("---")
            st.subheader(f"📚 Shared Books: {member1_select} & {member2_select}")

            shared_books_df = correlation_books[pair_key]

            # Display the shared books nicely
            for _, book in shared_books_df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{book['title']}** by {book['author']}")
                with col2:
                    st.metric(member1_select, f"{book[member1_select]:.1f}")
                with col3:
                    st.metric(member2_select, f"{book[member2_select]:.1f}")
                with col4:
                    diff = book[member1_select] - book[member2_select]
                    st.metric("Diff", f"{diff:+.1f}")

            # Show correlation for this pair
            member1_idx = members.index(member1_select)
            member2_idx = members.index(member2_select)
            corr_value = correlation_matrix[member1_idx][member2_idx]

            if corr_value > 0.7:
                st.success(f"🔥 Very similar taste! Correlation: {corr_value:.3f}")
            elif corr_value > 0.4:
                st.info(f"👍 Similar taste. Correlation: {corr_value:.3f}")
            elif corr_value > 0:
                st.warning(f"😐 Somewhat similar. Correlation: {corr_value:.3f}")
            else:
                st.error(f"👎 Different tastes. Correlation: {corr_value:.3f}")
        else:
            st.info(
                f"No shared books with enough ratings between {member1_select} and {member2_select}.",
            )


def main() -> None:
    """Run Streamlit dashboard"""
    # Main header
    st.markdown(
        '<h1 class="main-header">🚀 Sci-Fi Book Club Analytics Dashboard</h1>',
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
            "🔍 Book Explorer",
            "🔬 Advanced Analytics",
        ],
    )

    # Main content based on selection
    if page == "📊 Overview":
        create_overview_metrics(bookclub_processed_df, members)
        st.markdown("---")
        create_rating_scatter(bookclub_processed_df, members)

    elif page == "👥 Member Insights":
        create_member_comparison(bookclub_processed_df, members)

    elif page == "📅 Time Analysis":
        create_time_analysis(bookclub_processed_df)

    elif page == "🔍 Book Explorer":
        create_book_selector(bookclub_processed_df, members)

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
