"""Characterization tests for the Streamlit dashboard application."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    "page_option",
    [
        "📊 Overview",
        "👥 Member Insights",
        "📅 Time Analysis",
        "✍️ Author Insights",
        "🔬 Advanced Analytics",
    ],
)
def test_dashboard_pages_render(page_option: str) -> None:
    """Test that all dashboard pages render without exceptions.

    For each sidebar radio option, creates a fresh AppTest instance,
    sets the radio value, reruns the app, and asserts that no exception occurred.

    Parameters
    ----------
    page_option : str
        The page option to select from the sidebar radio.

    """
    dashboard_path = Path(__file__).parents[1] / "src" / "scifi" / "dashboard.py"
    app = AppTest.from_file(str(dashboard_path))
    app.run(timeout=30)
    app.sidebar.radio[0].set_value(page_option).run(timeout=30)
    assert not app.exception
