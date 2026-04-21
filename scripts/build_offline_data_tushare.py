"""Build the repository-managed offline ETF dataset with Tushare.

This variant is intended for the local version of the project. It requires a
valid Tushare token and writes the same offline CSV layout used by the runtime.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys

import pandas as pd
import tushare as ts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from all_weather_strategy.config import AppConfig
from all_weather_strategy.paths import OFFLINE_DATA_DIR, OFFLINE_INDEX_PATH


def ts_code(symbol: str) -> str:
    """Convert a mainland ETF code into Tushare ts_code format."""
    if not symbol.isdigit():
        return symbol
    if symbol.startswith("5"):
        return f"{symbol}.SH"
    if symbol.startswith(("1", "3")):
        return f"{symbol}.SZ"
    return symbol


def _require_token() -> str:
    """Read the Tushare token from the environment and fail fast if missing."""
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise EnvironmentError("TUSHARE_TOKEN is required for the Tushare offline builder.")
    return token


def fetch_history(pro, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch ETF history from Tushare pro."""
    frame = pro.fund_daily(ts_code=ts_code(symbol), start_date=start_date.replace("-", ""), end_date=end_date.replace("-", ""))
    if frame.empty:
        raise RuntimeError(f"Unable to fetch Tushare history for {symbol}")
    if "trade_date" not in frame.columns or "close" not in frame.columns:
        raise ValueError(f"Unexpected Tushare response for {symbol}")
    frame["date"] = pd.to_datetime(frame["trade_date"], format="%Y%m%d")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise")
    return frame[["date", "close"]].sort_values("date").reset_index(drop=True)


def fetch_name(pro, symbol: str) -> str:
    """Fetch an ETF name from Tushare pro."""
    try:
        basic = pro.fund_basic(market="E")
        match = basic[basic["ts_code"] == ts_code(symbol)]
        if not match.empty and "name" in match.columns:
            return str(match["name"].iloc[0])
    except Exception:
        pass
    return f"ETF({symbol})"


def main() -> None:
    """Generate local CSV files and the manifest for the Tushare variant."""
    token = _require_token()
    pro = ts.pro_api(token)

    OFFLINE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=AppConfig.MAX_LOOKBACK_DAYS)

    manifest_rows = []
    for symbol in AppConfig.DEFAULT_ETF_LIST:
        frame = fetch_history(pro, symbol, start_date.isoformat(), end_date.isoformat())
        name = fetch_name(pro, symbol)
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
                "source": "tushare",
            }
        )

    pd.DataFrame(manifest_rows).to_csv(OFFLINE_INDEX_PATH, index=False, encoding="utf-8-sig")
    print(f"Offline dataset written to {OFFLINE_DATA_DIR}")


if __name__ == "__main__":
    main()
