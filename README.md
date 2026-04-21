# All Weather Strategy

This repository is a refactored Python project for the "test two" style delivery described in `REQ.txt`.

## What It Does

The app reads ETF history from repository-managed offline CSV files, computes a risk parity allocation, and exports the result as a table, CSV, and PDF report.

## Versions

- `yfinance` version: default demo path and the recommended Streamlit web experience.
- `Tushare` version: local build path that requires a `TUSHARE_TOKEN` and generates the same offline CSV contract.

## Structure

- `app.py`: Streamlit launcher.
- `all_weather_strategy/`: core package with configuration, domain types, offline data loading, optimization, reporting, and UI.
- `data/offline/`: offline ETF dataset used at runtime.
- `data/reports/`: generated outputs.
- `docs/`: project structure, principle, and requirement notes.
- `scripts/`: maintenance utilities, including offline data refresh.
- `sources/original_repo/`: archived upstream source snapshot.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Rebuild Offline Data

```bash
python scripts/build_offline_data.py
```

## Build Tushare Offline Data

```bash
set TUSHARE_TOKEN=your_token_here
python scripts/build_offline_data_tushare.py
```

## Notes

- The runtime path uses local CSV files only.
- All paths are relative to the repository root.
- `SIMHEI.TTF` is retained for Chinese chart and PDF rendering.
