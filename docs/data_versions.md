# Data Versions

This repository supports two data preparation variants.

## 1. YFinance Version

- Default web demo.
- Uses `scripts/build_offline_data.py` to generate offline CSV files.
- No token is required.
- The Streamlit app reads the offline CSV files and renders the UI at runtime.

## 2. Tushare Local Version

- Intended for local execution with a Tushare account.
- Uses `scripts/build_offline_data_tushare.py` to generate the same offline CSV layout.
- Requires the `TUSHARE_TOKEN` environment variable.
- The runtime app remains the same because both versions produce the same offline data contract.

## Shared Runtime

- `app.py` remains the single Streamlit entry point.
- `all_weather_strategy/data_repository.py` reads local CSV files only.
- `data/offline/` is the runtime data source for both variants.
