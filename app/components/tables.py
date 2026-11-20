"""
FinSight AI - Financial Table Formatting Components
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_holdings_table(holdings: List[Dict[str, Any]], currency: str = "INR"):
    """Renders styled holdings dataframe with formatted PnL."""
    if not holdings:
        st.info("No active holdings found in this portfolio.")
        return

    df = pd.DataFrame(holdings)
    sym = "₹" if currency == "INR" else "$"

    # Formatting
    df["quantity"] = df["quantity"].apply(lambda x: f"{x:,.2f}")
    df["avg_cost"] = df["avg_cost"].apply(lambda x: f"{sym} {x:,.2f}")
    df["current_price"] = df["current_price"].apply(lambda x: f"{sym} {x:,.2f}")
    df["total_cost"] = df["total_cost"].apply(lambda x: f"{sym} {x:,.2f}")
    df["market_value"] = df["market_value"].apply(lambda x: f"{sym} {x:,.2f}")
    df["unrealized_pnl"] = df["unrealized_pnl"].apply(lambda x: f"{sym} {x:,.2f}")
    df["pnl_percent"] = df["pnl_percent"].apply(lambda x: f"{x:+.2f}%")

    df.columns = ["Symbol", "Quantity", "Avg Cost", "Current Price", "Total Cost", "Market Value", "Unrealized P&L", "Return %"]
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_transaction_history_table(transactions: List[Dict[str, Any]], currency: str = "INR"):
    """Renders transaction history."""
    if not transactions:
        st.info("No recorded transactions.")
        return

    df = pd.DataFrame(transactions)
    sym = "₹" if currency == "INR" else "$"
    df["price"] = df["price"].apply(lambda x: f"{sym} {x:,.2f}")
    df["cost"] = df["cost"].apply(lambda x: f"{sym} {x:,.2f}")
    df["realized_pnl"] = df["realized_pnl"].apply(lambda x: f"{sym} {x:,.2f}")
    df["quantity"] = df["quantity"].apply(lambda x: f"{x:,.2f}")

    df = df[["date", "symbol", "type", "quantity", "price", "cost", "realized_pnl"]]
    df.columns = ["Date", "Symbol", "Action", "Quantity", "Price", "Fee", "Realized P&L"]
    st.dataframe(df, use_container_width=True, hide_index=True)
