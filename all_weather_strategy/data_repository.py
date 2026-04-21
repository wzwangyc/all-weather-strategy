"""Live ETF data access via yfinance.

The GitHub/Streamlit version does not ship price history files. It fetches
historical prices at runtime and then performs the allocation calculation on
freshly downloaded data.
"""

from dataclasses import dataclass
import time
from datetime import timedelta
from decimal import Decimal
from functools import lru_cache
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError


YAHOO_TICKER_MAP = {
    "159201": "159201.SZ",
    "588290": "588290.SS",
    "159531": "159531.SZ",
    "159545": "159545.SZ",
    "515450": "515450.SS",
    "513100": "513100.SS",
    "518880": "518880.SS",
}

DISPLAY_NAME_MAP = {
    "159201": "自由现金流ETF华夏",
    "588290": "科创芯片ETF华安",
    "159531": "中证2000ETF南方",
    "159545": "恒生红利低波ETF易方达",
    "515450": "红利低波50ETF南方",
    "513100": "纳指ETF国泰",
    "518880": "黄金ETF华安",
}


@dataclass(frozen=True)
class ETFHistory:
    """Container for one ETF's fetched time series."""

    symbol: str
    name: str
    frame: pd.DataFrame

    @property
    def latest_close(self) -> Decimal:
        """Return the latest close as a Decimal value."""
        return Decimal(str(self.frame.iloc[-1]["close"]))

    def to_returns(self) -> pd.Series:
        """Convert price history into a simple daily return series."""
        indexed = self.frame.set_index("date").sort_index()
        returns = indexed["close"].pct_change(fill_method=None).dropna()
        returns.name = self.symbol
        return returns


class YFinanceETFRepository:
    """Load ETF history from Yahoo Finance at runtime."""

    REQUEST_DELAY_SECONDS = 0.8
    MAX_RETRIES = 3

    def _resolve_symbol(self, symbol: str) -> str:
        if symbol in YAHOO_TICKER_MAP:
            return YAHOO_TICKER_MAP[symbol]
        if symbol.endswith((".SS", ".SZ", ".HK", ".US")):
            return symbol
        if symbol.startswith(("15", "16")):
            return f"{symbol}.SZ"
        return f"{symbol}.SS"

    def _resolve_name(self, symbol: str) -> str:
        return DISPLAY_NAME_MAP.get(symbol, symbol)

    @staticmethod
    def _normalize_history(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            raise ValueError("Yahoo Finance returned an empty history frame.")
        if "Close" not in frame.columns:
            raise ValueError("Yahoo Finance history is missing the Close column.")

        frame = frame.reset_index()
        date_column = frame.columns[0]
        frame = frame.rename(columns={date_column: "date"})

        frame = frame[["date", "Close"]].copy()
        dates = pd.to_datetime(frame["date"], errors="raise")
        if getattr(dates.dt, "tz", None) is not None:
            dates = dates.dt.tz_convert(None)
        frame["date"] = dates
        frame["close"] = pd.to_numeric(frame["Close"], errors="coerce")
        frame = frame.dropna(subset=["close"])
        frame = frame[["date", "close"]].sort_values("date").reset_index(drop=True)
        if frame.empty:
            raise ValueError("Normalized Yahoo Finance history is empty after cleaning.")
        return frame

    @lru_cache(maxsize=64)
    def _fetch_history(self, yahoo_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch and normalize one Yahoo Finance history frame with retries."""
        end_with_buffer = (pd.Timestamp(end_date) + timedelta(days=1)).date().isoformat()
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                frame = yf.Ticker(yahoo_symbol).history(
                    start=start_date,
                    end=end_with_buffer,
                    auto_adjust=False,
                )
                if frame.empty:
                    raise ValueError(f"Yahoo Finance returned no data for {yahoo_symbol}.")
                return self._normalize_history(frame)
            except YFRateLimitError as exc:
                last_error = exc
                if attempt == self.MAX_RETRIES:
                    raise RuntimeError(
                        f"Yahoo Finance rate limited requests for {yahoo_symbol}. "
                        "Try again after a short delay."
                    ) from exc
                time.sleep(self.REQUEST_DELAY_SECONDS * attempt)
            except Exception as exc:
                last_error = exc
                if attempt == self.MAX_RETRIES:
                    raise
                time.sleep(self.REQUEST_DELAY_SECONDS * attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Unable to fetch Yahoo Finance history for {yahoo_symbol}.")

    def resolve(self, symbol: str, start_date: str, end_date: str) -> ETFHistory:
        """Resolve a single ETF history from Yahoo Finance."""
        yahoo_symbol = self._resolve_symbol(symbol)

        frame = self._fetch_history(yahoo_symbol, start_date, end_date)
        frame = frame[(frame["date"] >= pd.Timestamp(start_date)) & (frame["date"] <= pd.Timestamp(end_date))].copy()
        if frame.empty or len(frame) < 2:
            raise ValueError(
                f"Yahoo Finance data for {symbol} does not cover the requested date range: {start_date} to {end_date}."
            )
        return ETFHistory(symbol=symbol, name=self._resolve_name(symbol), frame=frame)

    def load_portfolio(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
    ) -> Tuple[Dict[str, pd.Series], Dict[str, Decimal], Dict[str, str]]:
        """Load aligned returns, prices, and names for a portfolio."""
        if not symbols:
            raise ValueError("At least one ETF symbol must be provided.")

        returns_map: Dict[str, pd.Series] = {}
        price_map: Dict[str, Decimal] = {}
        name_map: Dict[str, str] = {}

        missing: List[str] = []
        for symbol in symbols:
            try:
                history = self.resolve(symbol, start_date, end_date)
            except Exception:
                missing.append(symbol)
                continue

            returns_map[symbol] = history.to_returns()
            price_map[symbol] = history.latest_close
            name_map[symbol] = history.name

        if missing:
            raise ValueError(
                "Yahoo Finance did not return usable data for these ETFs: " + ", ".join(missing)
            )

        return returns_map, price_map, name_map
