"""Streamlit entry point for the All Weather Strategy demo.

When this module is launched directly from an IDE or shell, it relaunches
itself through `streamlit run` so the browser UI opens automatically. When
Streamlit is already executing the script, the app renders normally.
"""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from all_weather_strategy.ui import render_app


def _is_streamlit_runtime() -> bool:
    """Return True when Streamlit is already hosting this script."""
    return "streamlit.runtime.scriptrunner" in sys.modules


def _launch_streamlit() -> None:
    """Launch a local Streamlit server for direct script execution."""
    script_path = Path(__file__).resolve()
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script_path),
        "--server.headless",
        "true",
    ]
    print("Starting local Streamlit server...")
    print("Open http://localhost:8501 in your browser if it does not open automatically.")
    webbrowser.open("http://localhost:8501")
    completed = subprocess.run(
        command,
        cwd=str(script_path.parent),
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == '__main__':
    if _is_streamlit_runtime():
        render_app()
    else:
        _launch_streamlit()
