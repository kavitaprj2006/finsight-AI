"""
FinSight AI - Interactive Plotly Financial Visualizations
Dark-theme compliant charts: Candlesticks, Multi-indicator subplots, Frontiers, Drawdowns, Regimes.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.constants import (
    COLOR_CARD_BG, COLOR_MAIN_BG, COLOR_BORDER, COLOR_PRIMARY_ACCENT,
    COLOR_SECONDARY_ACCENT, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
)

def create_candlestick_chart(
    df: pd.DataFrame,
    symbol: str,
    show_sma: bool = True,
    show_bb: bool = True,
    show_volume: bool = True
) -> go.Figure:
    """Creates a TradingView-style interactive candlestick chart with overlays."""
    rows = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights
    )

    # 1. Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=symbol,
            increasing_line_color=COLOR_POSITIVE,
            decreasing_line_color=COLOR_NEGATIVE
        ),
        row=1, col=1
    )

    # 2. Moving Averages
    if show_sma and "SMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_20"], mode="lines", name="SMA 20", line=dict(color=COLOR_SECONDARY_ACCENT, width=1.5)),
            row=1, col=1
        )
    if show_sma and "SMA_50" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA_50"], mode="lines", name="SMA 50", line=dict(color=COLOR_WARNING, width=1.5)),
            row=1, col=1
        )

    # 3. Bollinger Bands
    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Upper"], mode="lines", name="BB Upper", line=dict(color="rgba(148, 163, 184, 0.4)", width=1, dash="dot")),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Lower"], mode="lines", name="BB Lower", line=dict(color="rgba(148, 163, 184, 0.4)", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(75, 155, 255, 0.05)"),
            row=1, col=1
        )

    # 4. Volume Bars
    if show_volume and "Volume" in df.columns:
        colors = [COLOR_POSITIVE if c >= o else COLOR_NEGATIVE for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(
            go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors, opacity=0.6),
            row=2, col=1
        )

    fig.update_layout(
        paper_bgcolor=COLOR_CARD_BG,
        plot_bgcolor=COLOR_CARD_BG,
        font=dict(color=COLOR_TEXT_PRIMARY, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=COLOR_BORDER, showgrid=True, rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor=COLOR_BORDER, showgrid=True),
        margin=dict(l=30, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    if show_volume:
        fig.update_yaxes(gridcolor=COLOR_BORDER, row=2, col=1)

    return fig

def create_rsi_macd_chart(df: pd.DataFrame) -> go.Figure:
    """Creates secondary indicator panel (RSI + MACD)."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=["RSI (14)", "MACD (12, 26, 9)"])

    # RSI
    if "RSI_14" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI_14"], name="RSI 14", line=dict(color=COLOR_PRIMARY_ACCENT, width=1.5)), row=1, col=1)
        fig.add_hline(y=70, line=dict(color=COLOR_NEGATIVE, width=1, dash="dash"), row=1, col=1)
        fig.add_hline(y=30, line=dict(color=COLOR_POSITIVE, width=1, dash="dash"), row=1, col=1)

    # MACD
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color=COLOR_SECONDARY_ACCENT, width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal", line=dict(color=COLOR_WARNING, width=1.5)), row=2, col=1)
        colors = [COLOR_POSITIVE if h >= 0 else COLOR_NEGATIVE for h in df["MACD_Hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram", marker_color=colors), row=2, col=1)

    fig.update_layout(
        paper_bgcolor=COLOR_CARD_BG,
        plot_bgcolor=COLOR_CARD_BG,
        font=dict(color=COLOR_TEXT_PRIMARY, family="Inter, sans-serif"),
        margin=dict(l=30, r=20, t=30, b=20),
        xaxis=dict(gridcolor=COLOR_BORDER),
        yaxis=dict(gridcolor=COLOR_BORDER),
        xaxis2=dict(gridcolor=COLOR_BORDER),
        yaxis2=dict(gridcolor=COLOR_BORDER),
        showlegend=False
    )
    return fig

def create_efficient_frontier_chart(frontier_points: List[Dict[str, Any]], scenarios: Dict[str, Any]) -> go.Figure:
    """Plots Markowitz Efficient Frontier with educational scenario markers."""
    vols = [p["volatility"] * 100.0 for p in frontier_points]
    rets = [p["return"] * 100.0 for p in frontier_points]

    fig = go.Figure()
    # Frontier Curve
    fig.add_trace(
        go.Scatter(
            x=vols, y=rets, mode="lines",
            name="Efficient Frontier",
            line=dict(color=COLOR_PRIMARY_ACCENT, width=3)
        )
    )

    # Markers for scenarios
    palette = {"Conservative": COLOR_POSITIVE, "Balanced": COLOR_SECONDARY_ACCENT, "Growth-Oriented": COLOR_WARNING}
    for name, s in scenarios.items():
        if name in palette:
            fig.add_trace(
                go.Scatter(
                    x=[s["expected_volatility"] * 100.0],
                    y=[s["expected_return"] * 100.0],
                    mode="markers+text",
                    name=name,
                    text=[f"  {name}"],
                    textposition="middle right",
                    marker=dict(size=14, color=palette[name], symbol="diamond", line=dict(width=2, color="#FFFFFF"))
                )
            )

    fig.update_layout(
        paper_bgcolor=COLOR_CARD_BG,
        plot_bgcolor=COLOR_CARD_BG,
        font=dict(color=COLOR_TEXT_PRIMARY, family="Inter, sans-serif"),
        xaxis=dict(title="Annualized Volatility (%)", gridcolor=COLOR_BORDER),
        yaxis=dict(title="Expected Annual Return (%)", gridcolor=COLOR_BORDER),
        margin=dict(l=40, r=30, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_equity_curve_chart(equity_series: pd.Series, benchmark_series: Optional[pd.Series] = None) -> go.Figure:
    """Draws Strategy vs Benchmark equity curve."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=equity_series.index, y=equity_series.values,
            mode="lines", name="Strategy Equity",
            line=dict(color=COLOR_PRIMARY_ACCENT, width=2.5)
        )
    )
    if benchmark_series is not None:
        fig.add_trace(
            go.Scatter(
                x=benchmark_series.index, y=benchmark_series.values,
                mode="lines", name="Benchmark",
                line=dict(color=COLOR_SECONDARY_ACCENT, width=1.5, dash="dash")
            )
        )

    fig.update_layout(
        paper_bgcolor=COLOR_CARD_BG,
        plot_bgcolor=COLOR_CARD_BG,
        font=dict(color=COLOR_TEXT_PRIMARY, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=COLOR_BORDER),
        yaxis=dict(title="Portfolio Value", gridcolor=COLOR_BORDER),
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """Draws correlation matrix heatmap."""
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale=[[0, COLOR_NEGATIVE], [0.5, COLOR_CARD_BG], [1, COLOR_PRIMARY_ACCENT]],
            zmin=-1.0, zmax=1.0,
            colorbar=dict(title="Corr", tickfont=dict(color=COLOR_TEXT_PRIMARY))
        )
    )
    fig.update_layout(
        paper_bgcolor=COLOR_CARD_BG,
        plot_bgcolor=COLOR_CARD_BG,
        font=dict(color=COLOR_TEXT_PRIMARY, family="Inter, sans-serif"),
        margin=dict(l=40, r=20, t=20, b=40)
    )
    return fig
