"""Data loading and caching for the Sci-Fi Book Club dashboard."""

import logging

import polars as pl
import streamlit as st

from scifi.data_processor import load_dashboard_data
from scifi.paths import input_files, source_fingerprint

logger = logging.getLogger(__name__)


@st.cache_data(show_spinner="🔄 Processing book club data from sources...")
def load_bookclub(_fingerprint: tuple[tuple[str, int, int], ...]) -> pl.DataFrame:
    """Return the dashboard data; fingerprint only keys the cache.

    Parameters
    ----------
    _fingerprint : tuple[tuple[str, int, int], ...]
        A fingerprint of input files used to invalidate the cache when
        the input data changes. Only used as a cache key; not accessed in the function.

    Returns
    -------
    pl.DataFrame
        The processed book club data.
    """
    return load_dashboard_data()


def get_bookclub() -> pl.DataFrame:
    """Return the cached data, or stop the page with a readable error.

    Returns
    -------
    pl.DataFrame
        The processed book club data.
    """
    try:
        return load_bookclub(source_fingerprint(input_files()))
    except FileNotFoundError as e:
        logger.exception("Data files not found")
        st.error(f"📁 Data files not found: {e}")
        st.info(
            "💡 Make sure your data files are in the correct directories:\n"
            "```\n"
            "data/\n"
            "├── goodreads/\n"
            "│   └── clean/\n"
            "│       └── [member CSV files]\n"
            "└── bookclub/\n"
            "    ├── bookclub.csv\n"
            "    ├── manual_ratings.csv\n"
            "    └── authors.csv\n"
            "```"
        )
        st.stop()
        return pl.DataFrame()  # type: ignore[unreachable]
    except (pl.exceptions.PolarsError, ValueError, OSError) as e:
        logger.exception("Error processing data")
        st.error(f"❌ Error processing data: {e}")
        st.stop()
        return pl.DataFrame()  # type: ignore[unreachable]
