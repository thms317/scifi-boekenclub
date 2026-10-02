"""
🚀 Sci-Fi Book Club Analytics Dashboard

This dashboard provides deep insights into your book club's reading patterns and preferences.
Key features:
- Overview scatter plot with trendline and 1-5 axes range
- Member correlation analysis with clickable shared book exploration
- Time-series analysis with decade publication views
- Book deep dive with ranking explanations

To run: streamlit run app.py

Built with ❤️ using Streamlit, Plotly, and Polars
"""

import streamlit as st

from scifi.ui import advanced_analytics, author_insights, member_insights, overview, time_analysis

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

# Setup navigation
page = st.navigation(
    [
        st.Page(overview.render, title="Overview", icon="📊", default=True),
        st.Page(
            member_insights.render, title="Member Insights", icon="👥", url_path="member-insights"
        ),
        st.Page(time_analysis.render, title="Time Analysis", icon="📅", url_path="time-analysis"),
        st.Page(
            author_insights.render, title="Author Insights", icon="✍️", url_path="author-insights"
        ),
        st.Page(
            advanced_analytics.render,
            title="Advanced Analytics",
            icon="🔬",
            url_path="advanced-analytics",
        ),
    ]
)

# Main header
st.markdown(
    '<h1 class="main-header"><span class="rocket-emoji">🚀</span> Sci-Fi Book Club Analytics Dashboard</h1>',
    unsafe_allow_html=True,
)

# Run the selected page
page.run()

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
