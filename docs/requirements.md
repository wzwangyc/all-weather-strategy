# Requirements and Delivery Notes

## Environment

- Target platform: Windows
- Development style: PyCharm-friendly project layout
- Runtime entry: `streamlit run app.py`

## Data Policy

- Public data is saved to local CSV files before runtime use.
- The application reads local files only during normal execution.
- All file paths are relative to the repository root.
- The yfinance path is the default web demo.
- The Tushare path is a local rebuild variant and requires `TUSHARE_TOKEN`.

## Deliverables

- Complete Python project source code
- Project structure documentation
- Strategy principle documentation
- Requirements documentation
- Archived copy of the upstream source
- Offline dataset files

## Notes

- `data/reports/` is generated output and can be recreated at any time.
- `sources/original_repo/` preserves the source provenance of the project.
