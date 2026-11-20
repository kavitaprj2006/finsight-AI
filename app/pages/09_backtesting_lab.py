"""
FinSight AI - Historical Strategy Backtesting Lab
Walk-forward strategy simulation with chronological rebalancing, transaction fees, and zero look-ahead bias.
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.charts import create_equity_curve_chart
from app.analytics.backtester import HistoricalBacktester
from app.services.stock_service import stock_service
from app.analytics.currency import currency_engine
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, BENCHMARKS

def show():
    render_global_header("Algorithmic Backtesting Lab", "Rigorous historical simulation: Walk-forward optimization, transaction frictions & benchmark alpha")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", "INR" if market == MARKET_IN else "USD")
    bench_sym = BENCHMARKS.get(market, "^NSEI")

    all_syms = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, []) if not s["symbol"].startswith("^")]

    # Controls
    col_strat, col_freq, col_cap = st.columns([4, 3, 3])
    with col_strat:
        strategy_choice = st.selectbox(
            "Allocation Strategy",
            ["MAX_SHARPE", "MIN_VAR", "EQUAL_WEIGHT", "INVERSE_VAR"],
            format_func=lambda x: {
                "MAX_SHARPE": "Maximum Sharpe Ratio (Dynamic)",
                "MIN_VAR": "Minimum Variance (Defensive)",
                "EQUAL_WEIGHT": "Equal Weight (1/N Rebalanced)",
                "INVERSE_VAR": "Inverse Variance / Risk Parity"
            }[x]
        )
    with col_freq:
        rebal_freq = st.selectbox("Rebalancing Frequency", [21, 63], format_func=lambda x: "Monthly (~21 days)" if x == 21 else "Quarterly (~63 days)")
    with col_cap:
        init_capital = st.number_input(f"Starting Capital ({currency})", min_value=10000.0, max_value=10000000.0, value=1000000.0 if currency == "INR" else 50000.0, step=10000.0)

    # Fee settings
    c_fee, c_slip, c_cap = st.columns(3)
    with c_fee:
        fee_bps = st.slider("Transaction Fee (bps)", min_value=0.0, max_value=50.0, value=10.0, step=5.0) # 10 bps = 0.1%
    with c_slip:
        slip_bps = st.slider("Execution Slippage (bps)", min_value=0.0, max_value=50.0, value=5.0, step=5.0) # 5 bps = 0.05%
    with c_cap:
        max_pos_cap = st.slider("Max Weight per Asset", min_value=0.20, max_value=0.80, value=0.40, step=0.05)

    # Load multi-asset price matrix
    price_dict = {}
    for s in all_syms:
        t_data = stock_service.get_technical_data(s, market)
        df = t_data.get("df")
        if df is not None and not df.empty:
            price_dict[s] = df["Close"]

    bench_data = stock_service.get_technical_data(bench_sym, market)
    bench_series = bench_data.get("df")["Close"] if bench_data.get("df") is not None else None

    price_df = pd.DataFrame(price_dict).dropna()
    if len(price_df) < 150:
        st.error(f"Insufficient history ({len(price_df)} days) to run backtest with lookback window.")
        return

    # Run Backtest
    backtester = HistoricalBacktester(
        prices_df=price_df,
        benchmark_prices=bench_series,
        initial_capital=init_capital,
        rebalance_interval_days=rebal_freq,
        transaction_cost_pct=fee_bps / 10000.0,
        slippage_pct=slip_bps / 10000.0,
        lookback_window_days=126
    )

    try:
        bt_res = backtester.run(strategy=strategy_choice, max_weight=max_pos_cap)
    except Exception as e:
        st.error(f"Backtesting engine error: {e}")
        return

    # Metric Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card(
            label="Final Portfolio Value",
            value=currency_engine.format_currency(bt_res["final_value"], currency),
            delta=f"{bt_res['total_return_pct']*100.0:+.2f}% total",
            delta_type="positive" if bt_res["total_return_pct"] >= 0 else "negative",
            badge_text="SIMULATION",
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(
            label="Annualized CAGR",
            value=f"{bt_res['cagr']*100.0:+.2f}%",
            delta=f"Benchmark: {bt_res['benchmark_cagr']*100.0:+.2f}%",
            delta_type="positive" if bt_res["cagr"] >= bt_res["benchmark_cagr"] else "negative"
        )
    with k3:
        render_kpi_card(
            label="Strategy Sharpe",
            value=f"{bt_res['sharpe_ratio']:.2f}",
            delta=f"Vol: {bt_res['volatility']*100.0:.1f}%",
            delta_type="positive" if bt_res['sharpe_ratio'] > 1.0 else "neutral"
        )
    with k4:
        render_kpi_card(
            label="Maximum Drawdown",
            value=f"{abs(bt_res['max_drawdown'])*100.0:.1f}%",
            delta="Peak-to-trough",
            delta_type="negative"
        )
    with k5:
        render_kpi_card(
            label="Benchmark Excess Alpha",
            value=f"{(bt_res['cagr'] - bt_res['benchmark_cagr'])*100.0:+.2f}%",
            delta=f"Beta: {bt_res['beta']:.2f}",
            delta_type="positive" if bt_res['cagr'] > bt_res['benchmark_cagr'] else "negative"
        )

    # Visuals: Equity Curve vs Benchmark
    st.markdown(f"##### Strategy Equity Curve vs {bench_sym} Benchmark")
    curve_fig = create_equity_curve_chart(bt_res["equity_curve"], bt_res["benchmark_curve"])
    st.plotly_chart(curve_fig, use_container_width=True)

    # Rebalance Audit Log
    tab_rebal, tab_assumptions = st.tabs(["Periodic Rebalancing Audit Log", "Execution Frictions & Methodology"])
    with tab_rebal:
        st.markdown("##### Walk-Forward Rebalancing History")
        rebal_rows = []
        for r in bt_res["rebalances"]:
            w_str = ", ".join(f"{k}: {v*100:.0f}%" for k, v in r["weights"].items() if v > 0.05)
            rebal_rows.append({
                "Date": r["date"],
                "Reason": r["reason"],
                "Active Allocation": w_str,
                "Friction Cost": currency_engine.format_currency(r["cost"], currency)
            })
        st.dataframe(pd.DataFrame(rebal_rows), use_container_width=True, hide_index=True)

    with tab_assumptions:
        st.markdown(f"""
        - **Lookback Optimization Window**: {bt_res['assumptions']['lookback_window_days']} trading days (~6 calendar months).
        - **Zero Look-Ahead Enforcement**: Allocation weights solved strictly on historical slice $t \\le \\text{rebalance\\_date}$.
        - **Total Frictions**: {bt_res['assumptions']['transaction_fee_bps']:.1f} bps total applied to rebalanced turnover volume.
        """)

if __name__ == "__main__":
    show()
