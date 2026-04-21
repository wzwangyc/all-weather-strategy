"""Project path helpers.

The GitHub version keeps only runtime code and generated reports. No stock-price
history is stored in the repository.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = DATA_DIR / "reports"
FONT_PATH = PROJECT_ROOT / "SIMHEI.TTF"
