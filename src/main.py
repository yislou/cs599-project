"""
Main entry point — launches the Streamlit application.

Usage:
    streamlit run src/main.py
    or
    python -m streamlit run src/main.py
"""

import sys
from pathlib import Path

# Ensure the project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.app import render_app

if __name__ == "__main__":
    render_app()
