"""
Unit Tests for Currency Converter and Formatting Engine
"""
import pytest
from app.analytics.currency import CurrencyConverter

def test_currency_conversion():
    conv = CurrencyConverter({"USD_INR": 84.0, "INR_USD": 1.0 / 84.0, "USD_USD": 1.0, "INR_INR": 1.0})
    
    # 100 USD to INR
    inr_amt = conv.convert(100.0, "USD", "INR")
    assert pytest.approx(inr_amt, abs=1e-2) == 8400.0

    # Same currency conversion
    assert conv.convert(500.0, "INR", "INR") == 500.0

def test_currency_formatting():
    # Western format
    fmt_usd = CurrencyConverter.format_currency(1250000.0, "USD")
    assert "$ 1.25 M" in fmt_usd

    # Indian format (Lakhs & Crores)
    fmt_inr_lakh = CurrencyConverter.format_currency(500000.0, "INR")
    assert "₹ 5.00 L" in fmt_inr_lakh

    fmt_inr_cr = CurrencyConverter.format_currency(25000000.0, "INR")
    assert "₹ 2.50 Cr" in fmt_inr_cr
