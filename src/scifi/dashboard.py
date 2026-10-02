"""
🚀 Sci-Fi Book Club Analytics Dashboard

This module is kept for backwards compatibility with Community Cloud.
The actual app is now in app.py at the repository root.

To run: streamlit run app.py
"""

import runpy

from scifi.paths import ROOT_DIR

if __name__ == "__main__":
    runpy.run_path(str(ROOT_DIR / "app.py"), run_name="__main__")
