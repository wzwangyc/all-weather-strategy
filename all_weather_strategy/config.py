"""Application configuration.

The configuration is intentionally explicit so the app can be audited and
reproduced from the repository alone.
"""

from typing import ClassVar, Dict, List
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .domain import Money
from .paths import FONT_PATH, OFFLINE_DATA_DIR, REPORT_DIR


class AppConfig:
    """Static application settings and defaults."""

    DEFAULT_ETF_LIST: ClassVar[List[str]] = ["159201", "588290", "159531", "159545", "515450", "513100", "518880"]
    DEFAULT_LOOKBACK_DAYS: ClassVar[int] = 365
    MIN_LOOKBACK_DAYS: ClassVar[int] = 90
    MAX_LOOKBACK_DAYS: ClassVar[int] = 1095
    MIN_CAPITAL: ClassVar[float] = 100.0
    DEFAULT_CAPITAL: ClassVar[float] = 10000.0
    LOT_SIZE: ClassVar[int] = 100
    OFFLINE_DATA_DIR: ClassVar[Path] = OFFLINE_DATA_DIR
    REPORT_DIR: ClassVar[Path] = REPORT_DIR

    PLOT_PARAMS: ClassVar[Dict[str, object]] = {
        "font.family": ["SimHei", "Microsoft YaHei", "sans-serif"],
        "axes.unicode_minus": False,
        "figure.dpi": 120,
        "font.size": 11,
    }
    PANDAS_OPTIONS: ClassVar[Dict[str, object]] = {
        "display.unicode.ambiguous_as_wide": True,
        "display.unicode.east_asian_width": True,
        "display.width": 140,
    }

    @classmethod
    def apply_runtime_settings(cls) -> None:
        """Apply deterministic plotting and display settings."""
        for key, value in cls.PLOT_PARAMS.items():
            plt.rcParams[key] = value
        for key, value in cls.PANDAS_OPTIONS.items():
            pd.set_option(key, value)

    @classmethod
    def report_font_path(cls) -> Path:
        """Return the bundled font path used by chart and PDF generation."""
        if not FONT_PATH.exists():
            raise FileNotFoundError(f"Required font file is missing: {FONT_PATH}")
        return FONT_PATH

    @classmethod
    def default_capital(cls) -> Money:
        """Return the default capital as an explicit money object."""
        return Money.from_number(cls.DEFAULT_CAPITAL)
