# Project Structure

This project is a Streamlit-based ETF allocation demo organized for a test-two style Python delivery.

## Runtime Entry

- `app.py`: minimal Streamlit launcher.

## Core Package

- `all_weather_strategy/config.py`: app defaults, plotting settings, and runtime configuration.
- `all_weather_strategy/domain.py`: explicit financial value objects.
- `all_weather_strategy/data_repository.py`: offline ETF data loading.
- `all_weather_strategy/strategy.py`: risk parity optimization.
- `all_weather_strategy/reports.py`: CSV and PDF report generation.
- `all_weather_strategy/engine.py`: orchestration of data, strategy, and outputs.
- `all_weather_strategy/ui.py`: Streamlit UI composition.

## Data

- `data/offline/`: repository-managed ETF CSV files and manifest.
- `data/reports/`: generated CSV and PDF outputs created at runtime.

## Source Archive

- `sources/original_repo/`: archived copy of the upstream source files and dependency list.

## Utilities

- `scripts/build_offline_data.py`: one-time script that refreshes the offline dataset from public sources.
