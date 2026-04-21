"""Strongly typed financial value objects.

The project is a portfolio allocation demo, so the main monetary values are
represented explicitly rather than as raw primitives. This keeps the handling
of capital, prices, and share counts auditable and deterministic.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    """Convert an input to Decimal without inheriting binary float error."""
    return Decimal(str(value))


@dataclass(frozen=True)
class Money:
    """Monetary amount in a fixed currency."""

    amount: Decimal
    currency: str = "CNY"

    @classmethod
    def from_number(cls, value, currency: str = "CNY") -> "Money":
        """Create a monetary value from a numeric input."""
        amount = _to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
        return cls(amount=amount, currency=currency)

    def multiply(self, ratio: Decimal) -> "Money":
        """Scale the amount by a deterministic ratio."""
        amount = (self.amount * ratio).quantize(CENT, rounding=ROUND_HALF_UP)
        return Money(amount=amount, currency=self.currency)

    def to_decimal(self) -> Decimal:
        """Return the internal Decimal amount."""
        return self.amount


@dataclass(frozen=True)
class Price:
    """Quoted price for a single ETF share."""

    amount: Decimal
    currency: str = "CNY"

    @classmethod
    def from_number(cls, value, currency: str = "CNY") -> "Price":
        """Create a price from a numeric input."""
        amount = _to_decimal(value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        return cls(amount=amount, currency=currency)

    def to_decimal(self) -> Decimal:
        """Return the internal Decimal amount."""
        return self.amount


@dataclass(frozen=True)
class Quantity:
    """Share quantity rounded to a tradable lot."""

    shares: int

    def to_int(self) -> int:
        """Return the integer number of shares."""
        return self.shares


@dataclass(frozen=True)
class PnL:
    """Profit and loss value used for reporting and auditing."""

    amount: Decimal
    currency: str = "CNY"

    @classmethod
    def from_number(cls, value, currency: str = "CNY") -> "PnL":
        """Create a PnL value from a numeric input."""
        amount = _to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)
        return cls(amount=amount, currency=currency)
