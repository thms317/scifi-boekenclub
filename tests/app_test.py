"""Tests for the multipage Streamlit application."""

from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from scifi.paths import ROOT_DIR


def test_app_renders() -> None:
    """Test that app.py renders the default page without exception.

    This is a smoke test that verifies the app can start and the default
    Overview page renders without errors.
    """
    app = AppTest.from_file(str(ROOT_DIR / "app.py"), default_timeout=30)
    app.run(timeout=30)
    assert not app.exception


@pytest.mark.parametrize(
    "module_name",
    ["overview", "member_insights", "time_analysis", "author_insights", "advanced_analytics"],
)
def test_page_renders(module_name: str) -> None:
    """Test that each page module renders without exception.

    Parameters
    ----------
    module_name : str
        The name of the page module to test (without the .py extension).
    """
    code = f"from scifi.ui import {module_name}\n{module_name}.render()"
    app = AppTest.from_string(code, default_timeout=30)
    app.run(timeout=30)
    assert not app.exception


def test_book_selector_changes_content() -> None:
    """Test that selecting a different book in the overview changes the book card text."""
    app = AppTest.from_file(str(ROOT_DIR / "app.py"), default_timeout=30)
    app.run(timeout=30)

    # Get the initial book card text
    initial_text = " ".join(str(e) for e in app.elements if "book-detail-card" in str(e))

    # Change the book selector to a different book
    if app.selectbox:
        # Get the available options
        selectbox = app.selectbox[0]
        options = selectbox.options
        if len(options) > 1:
            # Set to a different book
            selectbox.set_value(options[1]).run(timeout=30)

            # Get the new book card text
            new_text = " ".join(str(e) for e in app.elements if "book-detail-card" in str(e))

            # Verify that the text has changed (unless by chance it's the same book)
            # This is a weak check but works for the common case
            assert initial_text != new_text or len(options) <= 1


def test_data_error_handling() -> None:
    """Test that missing data files are handled gracefully.

    This test patches load_dashboard_data to raise FileNotFoundError
    and verifies that get_bookclub() shows an error message and stops.
    """
    st_cache_code = """
import streamlit as st
st.cache_data.clear()
from scifi.ui.data import get_bookclub
try:
    get_bookclub()
except SystemExit:
    pass
"""

    with patch("scifi.data_processor.load_dashboard_data") as mock_load:
        mock_load.side_effect = FileNotFoundError("x")
        app = AppTest.from_string(st_cache_code, default_timeout=30)
        app.run(timeout=30)

        # Check that an error message was displayed
        error_elements = [
            e
            for e in app.elements
            if hasattr(e, "value") and "Data files not found" in str(e.value)
        ]
        assert len(error_elements) > 0, "Expected error message about missing data files"


def test_shim_renders() -> None:
    """Test that the dashboard.py shim still works.

    This ensures backwards compatibility with the old entry point.
    """
    dashboard_path = ROOT_DIR / "src" / "scifi" / "dashboard.py"
    app = AppTest.from_file(str(dashboard_path), default_timeout=30)
    app.run(timeout=30)
    assert not app.exception
