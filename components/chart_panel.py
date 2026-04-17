from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import COLORS

LABELS = {
    "inflation": "Inflation",
    "gdp_growth": "GDP Growth",
    "unemployment": "Unemployment",
    "interest_rate": "Policy Rate",
}


def _make_trend_chart(series_df: pd.DataFrame, metric_key: str) -> go.Figure:
    figure = go.Figure()
    if series_df.empty:
        figure.update_layout(height=320, margin=dict(l=0, r=0, t=8, b=0))
        return figure

    figure.add_trace(
        go.Scatter(
            x=series_df["year"],
            y=series_df["value"],
            mode="lines",
            line=dict(color=COLORS["accent_blue"], width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(41,151,255,0.15)",
            hovertemplate="%{x}: %{y:.2f}<extra></extra>",
        )
    )
    figure.update_layout(
        title=dict(text=LABELS.get(metric_key, metric_key.replace("_", " ").title()), x=0.0, font=dict(size=14, color=COLORS["text_primary"])),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=36, b=0),
        xaxis=dict(showgrid=False, zeroline=False, color=COLORS["text_secondary"], tickmode="auto"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False, color=COLORS["text_secondary"]),
        hovermode="x unified",
    )
    return figure


def render_trend_chart(series_df: pd.DataFrame, metric_key: str) -> None:
    st.plotly_chart(_make_trend_chart(series_df, metric_key), use_container_width=True, config={"displayModeBar": False})


def render_trend_grid(series_map: dict[str, pd.DataFrame]) -> None:
    rows = [("inflation", "gdp_growth"), ("unemployment", "interest_rate")]
    for left_key, right_key in rows:
        left_col, right_col = st.columns(2, gap="medium")
        with left_col:
            st.markdown('<div class="mc-card">', unsafe_allow_html=True)
            render_trend_chart(series_map[left_key], left_key)
            st.markdown("</div>", unsafe_allow_html=True)
        with right_col:
            st.markdown('<div class="mc-card">', unsafe_allow_html=True)
            render_trend_chart(series_map[right_key], right_key)
            st.markdown("</div>", unsafe_allow_html=True)
