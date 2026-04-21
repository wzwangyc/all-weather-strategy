"""Build the repository-managed offline ETF dataset.

This script fetches history from public sources once, then writes CSV files to
the local data directory. The application runtime reads these files only.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import akshare as ak
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from all_weather_strategy.config import AppConfig
from all_weather_strategy.paths import OFFLINE_DATA_DIR, OFFLINE_INDEX_PATH


def yf_symbol(symbol: str) -> str:
    """Convert a mainland ETF code into a yfinance symbol."""
    if not symbol.isdigit():
        return symbol
    if symbol.startswith("5"):
        return f"{symbol}.SS"
    if symbol.startswith(("1", "3")):
        return f"{symbol}.SZ"
    return symbol


def fetch_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch history from AkShare first and fall back to yfinance."""
    ak_start = start_date.replace("-", "")
    ak_end = end_date.replace("-", "")

    try:
        frame = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=ak_start, end_date=ak_end, adjust="qfq")
        frame["date"] = pd.to_datetime(frame["日期"])
        frame["close"] = pd.to_numeric(frame["收盘"], errors="raise")
        return frame[["date", "close"]].sort_values("date").reset_index(drop=True)
    except Exception:
        pass

    frame = yf.download(tickers=yf_symbol(symbol), start=start_date, end=end_date, auto_adjust=True, progress=False)
    if frame.empty:
        raise RuntimeError(f"Unable to fetch offline history for {symbol}")
    frame = frame.reset_index()
    frame["date"] = pd.to_datetime(frame["Date"])
    close_data = frame["Close"]
    if isinstance(close_data, pd.DataFrame):
        close_data = close_data.iloc[:, 0]
    frame["close"] = pd.to_numeric(close_data, errors="raise")
    return frame[["date", "close"]].sort_values("date").reset_index(drop=True)


def fetch_name(symbol: str) -> str:
    """Fetch an ETF name from AkShare with a deterministic fallback."""
    try:
        rank_df = ak.fund_exchange_rank_em()
        match_df = rank_df[rank_df["基金代码"] == symbol]
        if not match_df.empty:
            return str(match_df["基金简称"].iloc[0])
    except Exception:
        pass
    try:
        ticker = yf.Ticker(yf_symbol(symbol))
        return str(ticker.info.get("longName") or ticker.info.get("shortName") or f"ETF({symbol})")
    except Exception:
        return f"ETF({symbol})"


def main() -> None:
    """Generate local CSV files and an index manifest."""
    OFFLINE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=AppConfig.MAX_LOOKBACK_DAYS)

    manifest_rows = []
    for symbol in AppConfig.DEFAULT_ETF_LIST:
        frame = fetch_history(symbol, start_date.isoformat(), end_date.isoformat())
        name = fetch_name(symbol)
        file_name = f"{symbol}.csv"
        frame.to_csv(OFFLINE_DATA_DIR / file_name, index=False, encoding="utf-8-sig")
        manifest_rows.append(
            {
                "symbol": symbol,
                "name": name,
                "file_name": file_name,
                "start_date": frame["date"].min().date().isoformat(),
                "end_date": frame["date"].max().date().isoformat(),
                "rows": int(len(frame)),
                "source": "akshare/yfinance",
            }
        )

    pd.DataFrame(manifest_rows).to_csv(OFFLINE_INDEX_PATH, index=False, encoding="utf-8-sig")
    print(f"Offline dataset written to {OFFLINE_DATA_DIR}")


if __name__ == "__main__":
    main()
