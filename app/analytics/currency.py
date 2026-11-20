"""
FinSight AI - Multi-Currency Conversion & Formatting Engine
"""
from typing import Optional, Dict

class CurrencyConverter:
    # Reference exchange rates (Updated dynamically if live provider available)
    DEFAULT_RATES: Dict[str, float] = {
        "USD_INR": 84.25,
        "INR_USD": 1.0 / 84.25,
        "USD_USD": 1.0,
        "INR_INR": 1.0,
    }

    def __init__(self, rates: Optional[Dict[str, float]] = None):
        self.rates = rates or self.DEFAULT_RATES.copy()

    def update_rate(self, from_curr: str, to_curr: str, rate: float):
        key = f"{from_curr}_{to_curr}".upper()
        self.rates[key] = rate
        rev_key = f"{to_curr}_{from_curr}".upper()
        if rate > 0:
            self.rates[rev_key] = 1.0 / rate

    def convert(self, amount: float, from_curr: str, to_curr: str) -> float:
        if from_curr == to_curr:
            return amount
        key = f"{from_curr}_{to_curr}".upper()
        if key in self.rates:
            return amount * self.rates[key]
        raise ValueError(f"Exchange rate for {from_curr} to {to_curr} not found.")

    @staticmethod
    def format_currency(amount: float, currency: str = "INR", include_symbol: bool = True) -> str:
        """Formats currency with proper symbols and formatting."""
        sym = "₹" if currency == "INR" else ("$" if currency == "USD" else "")
        prefix = f"{sym} " if include_symbol and sym else ""
        
        if currency == "INR":
            # Indian numbering format (e.g., ₹ 1,25,000.00)
            if abs(amount) >= 10000000:  # Crores
                val_cr = amount / 10000000.0
                return f"{prefix}{val_cr:,.2f} Cr"
            elif abs(amount) >= 100000:   # Lakhs
                val_lakh = amount / 100000.0
                return f"{prefix}{val_lakh:,.2f} L"
            else:
                return f"{prefix}{amount:,.2f}"
        else:
            # Western numbering format (e.g., $ 1.25M, $ 125,000.00)
            if abs(amount) >= 1000000000:
                return f"{prefix}{amount / 1e9:,.2f} B"
            elif abs(amount) >= 1000000:
                return f"{prefix}{amount / 1e6:,.2f} M"
            else:
                return f"{prefix}{amount:,.2f}"

currency_engine = CurrencyConverter()
