"""Offline ETF data access.

The application reads ETF history from local CSV files only. This satisfies the
offline-data requirement and keeps the demo deterministic once the files are
checked into the repository.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from .paths import OFFLINE_DATA_DIR, OFFLINE_INDEX_PATH


@dataclass(frozen=True)
class ETFHistory:
    """Container for one ETF's offline time series."""

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


class OfflineETFRepository:
    """Load ETF data from repository-managed CSV files."""

    def __init__(self, data_dir: Path = OFFLINE_DATA_DIR, index_path: Path = OFFLINE_INDEX_PATH):
        self.data_dir = Path(data_dir)
        self.index_path = Path(index_path)

    def load_index(self) -> pd.DataFrame:
        """Load the manifest that maps ETF codes to data files."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Offline manifest not found: {self.index_path}")

        index_df = pd.read_csv(self.index_path, dtype={"symbol": str, "name": str, "file_name": str})
        required_columns = {"symbol", "name", "file_name"}
        missing = required_columns - set(index_df.columns)
        if missing:
            raise ValueError(f"Offline manifest is missing columns: {sorted(missing)}")
        return index_df

    def list_symbols(self) -> List[str]:
        """Return the ETFs available in the offline dataset."""
        index_df = self.load_index()
        return index_df["symbol"].tolist()

    def resolve(self, symbol: str) -> ETFHistory:
        """Load a single ETF history by symbol."""
        index_df = self.load_index()
        match = index_df[index_df["symbol"] == symbol]
        if match.empty:
            raise KeyError(f"ETF symbol is not available in offline data: {symbol}")

        row = match.iloc[0]
        file_path = self.data_dir / row["file_name"]
        if not file_path.exists():
            raise FileNotFoundError(f"ETF history file not found: {file_path}")

        frame = pd.read_csv(file_path, parse_dates=["date"])
        expected_columns = {"date", "close"}
        missing = expected_columns - set(frame.columns)
        if missing:
            raise ValueError(f"Offline history file {file_path} is missing columns: {sorted(missing)}")

        frame = frame.sort_values("date").reset_index(drop=True)
        frame["close"] = pd.to_numeric(frame["close"], errors="raise")
        if frame.empty:
            raise ValueError(f"Offline history file is empty: {file_path}")
        return ETFHistory(symbol=symbol, name=str(row["name"]), frame=frame)

    def load_portfolio(self, symbols: List[str], start_date: str, end_date: str) -> Tuple[Dict[str, pd.Series], Dict[str, Decimal], Dict[str, str]]:
        """Load aligned returns, prices, and names for a portfolio."""
        returns_map: Dict[str, pd.Series] = {}
        price_map: Dict[str, Decimal] = {}
        name_map: Dict[str, str] = {}

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)

        for symbol in symbols:
            history = self.resolve(symbol)
            frame = history.frame[(history.frame["date"] >= start_ts) & (history.frame["date"] <= end_ts)].copy()
            if frame.empty or len(frame) < 2:
                raise ValueError(
                    f"Offline data for {symbol} does not cover the requested date range: {start_date} to {end_date}"
                )

            frame = frame.set_index("date").sort_index()
            returns = frame["close"].pct_change().dropna()
            returns.name = symbol
            returns_map[symbol] = returns
            price_map[symbol] = Decimal(str(frame.iloc[-1]["close"]))
            name_map[symbol] = history.name

        return returns_map, price_map, name_map
