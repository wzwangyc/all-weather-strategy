"""Streamlit entry point for the All Weather Strategy demo.

When this module is launched directly from an IDE or shell, it relaunches
itself through `streamlit run` so the browser UI opens automatically. When
Streamlit is already executing the script, the app renders normally.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.runtime.scriptrunner import get_script_run_ctx

from all_weather_strategy.ui import render_app


def _is_streamlit_runtime() -> bool:
    """Return True when Streamlit is already hosting this script."""
    try:
        return get_script_run_ctx() is not None
    except Exception:
        return False


def _launch_streamlit() -> None:
    """Replace the current process with a Streamlit server process."""
    script_path = Path(__file__).resolve()
    os.execvpe(
        sys.executable,
        [sys.executable, '-m', 'streamlit', 'run', str(script_path)],
        os.environ.copy(),
    )


if __name__ == '__main__':
    if _is_streamlit_runtime():
        render_app()
    else:
        _launch_streamlit()
