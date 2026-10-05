"""Data loading for the Sci-Fi Book Club dashboard."""

import polars as pl
import streamlit as st

from scifi.data_processor import load_dashboard_data


def get_bookclub() -> pl.DataFrame:
    """Return the processed data, or stop the page with a readable error.

    The pipeline runs on every rerun. It takes about 12 ms on the club's data,
    so there is no cache to keep fresh when a CSV changes.

    Returns
    -------
    pl.DataFrame
        The processed book club data.

    Raises
    ------
    AssertionError
        Never in practice: st.stop() ends the script run before it.
    """
    try:
        return load_dashboard_data()
    except FileNotFoundError as e:
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
    except (pl.exceptions.PolarsError, ValueError, OSError) as e:
        st.error(f"❌ Error processing data: {e}")
    st.stop()
    msg = "st.stop() ends the script run"
    raise AssertionError(msg)
