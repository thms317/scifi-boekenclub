"""Smoke tests for the multipage Streamlit dashboard."""

from datetime import date
from unittest.mock import patch

import polars as pl
import pytest
from streamlit.testing.v1 import AppTest

from scifi.data_processor import load_dashboard_data

PAGES = ["overview", "member_insights", "time_analysis", "author_insights", "advanced_analytics"]


def book_card_text(at: AppTest) -> str:
    """Return the markdown of the selected-book detail card."""
    return "\n".join(m.value for m in at.markdown if "Read on" in m.value)


class TestDashboard:
    """Test class for the Streamlit dashboard."""

    def test_app_renders(self) -> None:
        """Test that app.py renders the default page without an exception."""
        at = AppTest.from_file("app.py", default_timeout=30).run()
        assert not at.exception

    def test_shim_renders(self) -> None:
        """Test that the old src/scifi/dashboard.py entrypoint still renders the app."""
        at = AppTest.from_file("src/scifi/dashboard.py", default_timeout=30).run()
        assert not at.exception

    @pytest.mark.parametrize("page", PAGES)
    def test_page_renders(self, page: str) -> None:
        """Test that every page renders without an exception on the real data."""
        at = AppTest.from_string(
            f"from scifi.ui import {page}\n{page}.render()", default_timeout=30
        )
        assert not at.run().exception

    def test_book_selection_changes_book_card(self) -> None:
        """Test that choosing another book shows that book in the detail card."""
        at = AppTest.from_string(
            "from scifi.ui import overview\noverview.render()", default_timeout=30
        )
        at.run()
        titles = at.selectbox(key="overview_book_selector").options
        assert titles[0] in book_card_text(at)
        # select_index passes the label to format_func, so set the option value (index) itself
        past = load_dashboard_data().filter(pl.col("date") < date.today())
        second_index = past.sort("date", descending=True)["index"][1]
        at.selectbox(key="overview_book_selector").set_value(second_index).run()
        assert titles[1] in book_card_text(at)
        assert titles[0] not in book_card_text(at)

    def test_unrated_books_dont_crash(self) -> None:
        """Test that selecting unrated past books doesn't crash the overview page."""
        at = AppTest.from_string(
            "from scifi.ui import overview\noverview.render()", default_timeout=30
        )
        at.run()

        # Find unrated past books
        unrated = load_dashboard_data().filter(
            (pl.col("date") < date.today()) & pl.col("average_bookclub_rating").is_null()
        )

        # Test each unrated book
        for unrated_index in unrated["index"].to_list():
            at.selectbox(key="overview_book_selector").set_value(unrated_index).run()
            assert not at.exception, f"Failed on unrated book with index {unrated_index}"

    def test_missing_data_shows_error(self) -> None:
        """Test that a missing data file shows a readable error instead of a traceback."""
        with patch("scifi.ui.data.load_dashboard_data", side_effect=FileNotFoundError("x.csv")):
            at = AppTest.from_string(
                "from scifi.ui.data import get_bookclub\nget_bookclub()", default_timeout=30
            ).run()
        assert not at.exception
        assert "Data files not found" in at.error[0].value
