from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import COLORS

LABELS = {
    "inflation": "Inflation (%, yoy)",
    "gdp_growth": "GDP Growth (%, yoy)",
    "unemployment": "Unemployment (%)",
    "interest_rate": "Policy Rate (%)",
}


def _make_trend_chart(series_df: pd.DataFrame, metric_key: str) -> go.Figure:
    fig = go.Figure()

    if series_df.empty:
        fig.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    fig.add_trace(
        go.Scatter(
            x=series_df["year"],
            y=series_df["value"],
            mode="lines",
            line=dict(color=COLORS["accent_blue"], width=2, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(74,127,193,0.08)",
            hovertemplate="<b>%{x}</b><br>%{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text=LABELS.get(metric_key, metric_key),
            x=0,
            font=dict(size=11, color=COLORS["text_secondary"], family="IBM Plex Sans, sans-serif"),
        ),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=4, r=4, t=32, b=4),
        xaxis=dict(showgrid=False, zeroline=False, color=COLORS["text_muted"], nticks=6),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            zeroline=False,
            color=COLORS["text_muted"],
            ticksuffix="%",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1d28",
            bordercolor=COLORS["accent_blue"],
            font=dict(color=COLORS["text_primary"], size=11, family="IBM Plex Sans, sans-serif"),
        ),
    )
    return fig


def render_trend_chart(series_df: pd.DataFrame, metric_key: str) -> None:
    st.plotly_chart(
        _make_trend_chart(series_df, metric_key),
        use_container_width=True,
        config={"displayModeBar": False, "staticPlot": False, "responsive": True},
    )


def render_trend_grid(series_map: dict[str, pd.DataFrame]) -> None:
    rows = [("inflation", "gdp_growth"), ("unemployment", "interest_rate")]
    for left_key, right_key in rows:
        left_col, right_col = st.columns(2, gap="large")
        for col, key in ((left_col, left_key), (right_col, right_key)):
            with col:
                with st.container(border=True):
                    render_trend_chart(series_map[key], key)
