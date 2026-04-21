"""Core orchestration for the all-weather strategy demo.

This layer coordinates data loading, optimization, and report construction. It
contains no UI code and no network fallback in the runtime path.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import AppConfig
from .data_repository import YFinanceETFRepository
from .domain import Money, Price, Quantity
from .reports import ReportGenerator
from .strategy import RiskParityStrategy


class AllWeatherEngine:
    """Run the complete live all-weather allocation workflow."""

    def __init__(self, etf_symbols: List[str], repository: Optional[YFinanceETFRepository] = None):
        AppConfig.apply_runtime_settings()
        self.etf_symbols = etf_symbols
        self.repository = repository or YFinanceETFRepository()
        self.strategy = RiskParityStrategy()

    def _validate_inputs(self, total_amount: Money, lookback_days: int) -> None:
        """Validate runtime inputs before any calculation begins."""
        if total_amount.amount <= 0:
            raise ValueError("Total capital must be positive.")
        if not (AppConfig.MIN_LOOKBACK_DAYS <= lookback_days <= AppConfig.MAX_LOOKBACK_DAYS):
            raise ValueError(
                f"Lookback days must be between {AppConfig.MIN_LOOKBACK_DAYS} and {AppConfig.MAX_LOOKBACK_DAYS}."
            )
        if not self.etf_symbols:
            raise ValueError("At least one ETF symbol must be provided.")

    def run(self, total_amount, lookback_days: int = AppConfig.DEFAULT_LOOKBACK_DAYS, progress_callback=None):
        """Execute the full data -> model -> result workflow."""
        capital = total_amount if isinstance(total_amount, Money) else Money.from_number(total_amount)
        self._validate_inputs(capital, lookback_days)

        if progress_callback:
            progress_callback(0.1, "???? Yahoo Finance ??????...")

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=lookback_days)

        returns_map, price_map, name_map = self.repository.load_portfolio(
            self.etf_symbols,
            start_date.isoformat(),
            end_date.isoformat(),
        )

        if progress_callback:
            progress_callback(0.7, "??????????...")

        returns_df = pd.DataFrame(returns_map).dropna()
        if returns_df.empty:
            raise ValueError("Aligned return matrix is empty after date filtering.")

        optimized = self.strategy.calculate_weights(returns_df)
        metrics = self.strategy.calculate_metrics(optimized.weights, returns_df, optimized.covariance)

        rows = []
        for symbol, weight in zip(returns_df.columns, optimized.weights):
            allocation = capital.multiply(Decimal(str(weight)))
            price = Price.from_number(price_map[symbol])
            raw_shares = int((allocation.amount / price.amount) // AppConfig.LOT_SIZE * AppConfig.LOT_SIZE)
            shares = Quantity(raw_shares)
            actual_amount = Money.from_number(price.amount * Decimal(shares.shares))

            rows.append(
                {
                    "ETF??": symbol,
                    "ETF??": name_map[symbol],
                    "??": f"{weight * 100:.2f}%",
                    "????(?)": f"{allocation.amount:.2f}",
                    "????(?)": f"{price.amount:.3f}",
                    "????(?)": shares.shares,
                    "??????(?)": f"{actual_amount.amount:.2f}",
                }
            )

        result_df = pd.DataFrame(rows)
        result_df["????"] = result_df["??"].str.rstrip("%").astype(float)
        result_df = result_df.sort_values("????", ascending=False).drop(columns=["????"]).reset_index(drop=True)

        if progress_callback:
            progress_callback(1.0, "????")

        return {
            "result_df": result_df,
            "weights": optimized.weights,
            "etf_names": name_map,
            "metrics": metrics,
            "capital": capital,
        }

    def save_reports(self, result_df: pd.DataFrame, weights: np.ndarray, etf_names: Dict[str, str], total_amount) -> None:
        """Persist CSV and PDF report outputs to the repository-managed folder."""
        capital = total_amount if isinstance(total_amount, Money) else Money.from_number(total_amount)
        AppConfig.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        generator = ReportGenerator(capital.amount)

        csv_path = AppConfig.REPORT_DIR / f"AllWeather_Plan_{timestamp}.csv"
        generator.generate_csv(result_df, str(csv_path))

        pdf_path = AppConfig.REPORT_DIR / f"AllWeather_Report_{timestamp}.pdf"
        generator.generate_pdf(result_df, weights, etf_names, str(pdf_path))
