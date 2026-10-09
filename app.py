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


# Setup navigation
page = st.navigation(  # ty: ignore[call-non-callable]  # ty mistakes the function for the streamlit.navigation subpackage
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
st.title("🚀 Sci-Fi Book Club Analytics Dashboard")

# Run the selected page
page.run()

# Footer
st.markdown("---")
st.caption("📚 Built with ❤️ for the Sci-Fi Book Club | Powered by Streamlit, Plotly & Polars")
