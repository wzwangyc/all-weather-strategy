# All Weather Strategy

This repository now keeps only the yfinance-based Streamlit demo for GitHub.

## Demo

Live app: https://all-weather-strategy.streamlit.app/

## What Is Included

- `app.py`: Streamlit entry point.
- `all_weather_strategy/`: runtime package for offline ETF allocation.
- `data/offline/`: local CSV dataset used by the app.
- `SIMHEI.TTF`: bundled font for Chinese rendering in charts and reports.
- `requirements.txt`: pinned runtime dependencies.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- This GitHub version is the simplified yfinance track.
- The full test-two submission is kept locally in the `测试二：完整python项目` folder.
- The local test-two folder also contains a Tushare + local-data variant.