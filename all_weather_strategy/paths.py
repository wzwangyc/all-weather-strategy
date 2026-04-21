"""Project path helpers.

All runtime paths are resolved relative to the repository root so the project
can be moved or cloned without breaking execution.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OFFLINE_DATA_DIR = DATA_DIR / "offline"
REPORT_DIR = DATA_DIR / "reports"
SOURCES_DIR = PROJECT_ROOT / "sources"
ORIGINAL_REPO_DIR = SOURCES_DIR / "original_repo"
FONT_PATH = PROJECT_ROOT / "SIMHEI.TTF"
OFFLINE_INDEX_PATH = OFFLINE_DATA_DIR / "index.csv"
