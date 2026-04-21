"""Live ETF data access via yfinance.

The GitHub/Streamlit version does not ship price history files. It fetches the
historical prices at runtime and then performs the allocation calculation on the
freshly downloaded data.
"""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf


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
    "159201": "?????ETF??",
    "588290": "????ETF??",
    "159531": "??2000ETF??",
    "159545": "??????ETF???",
    "515450": "????50ETF??",
    "513100": "??ETF??",
    "518880": "??ETF??",
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
        returns = indexed["close"].pct_change().dropna()
        returns.name = self.symbol
        return returns


class YFinanceETFRepository:
    """Load ETF history from Yahoo Finance at runtime."""

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

    def _normalize_history(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            raise ValueError("Yahoo Finance returned an empty history frame.")

        frame = frame.reset_index()
        date_column = frame.columns[0]
        frame = frame.rename(columns={date_column: "date"})
        if "Close" not in frame.columns:
            raise ValueError("Yahoo Finance history is missing the Close column.")

        frame = frame[["date", "Close"]].copy()
        dates = pd.to_datetime(frame["date"], errors="raise")
        if getattr(dates.dt, "tz", None) is not None:
            dates = dates.dt.tz_convert(None)
        frame["date"] = dates
        frame["close"] = pd.to_numeric(frame["Close"], errors="raise")
        frame = frame[["date", "close"]].sort_values("date").reset_index(drop=True)
        if frame.empty:
            raise ValueError("Normalized Yahoo Finance history is empty.")
        return frame

    def resolve(self, symbol: str, start_date: str, end_date: str) -> ETFHistory:
        """Fetch a single ETF history by symbol."""
        yahoo_symbol = self._resolve_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)
        history = ticker.history(
            start=start_date,
            end=(pd.Timestamp(end_date) + timedelta(days=1)).date().isoformat(),
            auto_adjust=False,
        )
        if history.empty:
            raise ValueError(f"Yahoo Finance returned no data for {symbol} ({yahoo_symbol}).")

        frame = self._normalize_history(history)
        frame = frame[(frame["date"] >= pd.Timestamp(start_date)) & (frame["date"] <= pd.Timestamp(end_date))].copy()
        if frame.empty or len(frame) < 2:
            raise ValueError(
                f"Yahoo Finance data for {symbol} does not cover the requested date range: {start_date} to {end_date}."
            )
        return ETFHistory(symbol=symbol, name=self._resolve_name(symbol), frame=frame)

    def load_portfolio(self, symbols: List[str], start_date: str, end_date: str) -> Tuple[Dict[str, pd.Series], Dict[str, Decimal], Dict[str, str]]:
        """Load aligned returns, prices, and names for a portfolio."""
        returns_map: Dict[str, pd.Series] = {}
        price_map: Dict[str, Decimal] = {}
        name_map: Dict[str, str] = {}

        for symbol in symbols:
            history = self.resolve(symbol, start_date, end_date)
            returns = history.to_returns()
            returns_map[symbol] = returns
            price_map[symbol] = history.latest_close
            name_map[symbol] = history.name

        return returns_map, price_map, name_map
