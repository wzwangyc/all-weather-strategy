"""Risk parity strategy implementation.

The objective is to equalize risk contributions across the available ETF
positions. The implementation is deterministic and fails fast if the
optimization does not converge.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass(frozen=True)
class RiskParityOutput:
    """Container for optimized weights and covariance matrix."""

    weights: np.ndarray
    covariance: pd.DataFrame


class RiskParityStrategy:
    """Compute risk parity weights and portfolio metrics."""

    def calculate_weights(self, returns_df: pd.DataFrame) -> RiskParityOutput:
        """Optimize weights so each asset contributes similar portfolio risk."""
        if returns_df.empty:
            raise ValueError("Return matrix cannot be empty.")
        if returns_df.isnull().any().any():
            raise ValueError("Return matrix must not contain missing values.")

        cov_matrix = returns_df.cov() * 252
        if cov_matrix.isnull().any().any():
            raise ValueError("Covariance matrix contains invalid values.")

        n_assets = len(returns_df.columns)
        if n_assets < 2:
            raise ValueError("Risk parity requires at least two assets.")

        initial_weights = np.array([1.0 / n_assets] * n_assets, dtype=float)

        def risk_contribution(weights: np.ndarray) -> np.ndarray:
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_vol <= 0:
                raise ValueError("Portfolio volatility must be positive.")
            marginal_risk = np.dot(cov_matrix, weights) / portfolio_vol
            return weights * marginal_risk

        def objective(weights: np.ndarray) -> float:
            rc = risk_contribution(weights)
            return float(np.sum((rc - np.mean(rc)) ** 2))

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
        solution = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            constraints=constraints,
            bounds=bounds,
            tol=1e-12,
            options={"maxiter": 5000, "ftol": 1e-12, "disp": False},
        )

        if not solution.success:
            raise RuntimeError(f"Risk parity optimization failed: {solution.message}")

        weights = np.asarray(solution.x, dtype=float)
        weights = weights / weights.sum()
        return RiskParityOutput(weights=weights, covariance=cov_matrix)

    def calculate_metrics(self, weights: np.ndarray, returns_df: pd.DataFrame, cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """Calculate annualized return and volatility for the optimized portfolio."""
        annual_returns = returns_df.mean() * 252
        portfolio_return = float(np.dot(weights, annual_returns))
        portfolio_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))
        return {"annualized_return": portfolio_return, "annualized_risk": portfolio_vol}
