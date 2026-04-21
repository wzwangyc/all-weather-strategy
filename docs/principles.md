# Strategy Principle

The project implements a simplified risk parity allocation workflow.

## Business Flow

1. Read ETF history from repository-managed offline CSV files.
2. Align the history into a common return matrix.
3. Optimize ETF weights so each asset contributes similar portfolio risk.
4. Convert weights into a tradable allocation plan using explicit lot sizing.
5. Render the result table, allocation chart, CSV, and PDF outputs.

## Modeling Notes

- Capital is represented as an explicit monetary value.
- Share counts are rounded down to the nearest trading lot.
- Optimization is deterministic for the same input dataset.
- The runtime path does not depend on live network data.

## Boundary Conditions

- At least two assets are required for risk parity optimization.
- Offline data must cover the selected lookback window.
- Missing files or invalid input terminate execution immediately.
