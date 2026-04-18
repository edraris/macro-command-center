"""
World choropleth map — primary navigation / exploration tool.
Supports multiple map layers: GDP, Growth, Inflation, Policy Rate.
Click to navigate, selected country highlighted.
"""
from __future__ import annotations

import numpy as np
import plotly.express as px
import streamlit as st

from config import COLORS
from services.data_cache import get_map_dataset


def _color_scales(layer: str) -> list:
    """Return a plotly color scale appropriate to the metric."""
    if layer == "gdp_value":
        return ["#0e1422", "#162438", "#1e3a5f", COLORS["accent_blue"], "#7aacd4", "#bcd4e6"]
    if layer == "gdp_growth":
        # diverging: red (negative) to green (positive)
        return [
            [0.00, "#b84d44"],
            [0.25, "#c0524a"],
            [0.45, "#7a7f94"],
            [0.55, "#7a7f94"],
            [0.75, "#4a9e74"],
            [1.00, "#2d7a54"],
        ]
    if layer == "inflation":
        return ["#2d7a54", "#4a9e74", "#7a9e6e", COLORS["amber"], "#c9a84c", "#b84d44"]
    # interest_rate
    return ["#1a3a5f", COLORS["accent_blue"], "#4a7fc1", COLORS["amber"], "#c9a84c", COLORS["negative_red"]]


def _format_hover_value(layer: str, raw_val: float) -> str:
    if layer == "gdp_value":
        if raw_val >= 1e12:
            return f"${raw_val/1e12:.2f}T"
        return f"${raw_val/1e9:.1f}B"
    return f"{raw_val:.1f}%"


def render_map(selected_country: str, layer: str = "gdp_value") -> None:
    frame = get_map_dataset().copy()

    if layer == "gdp_value":
        frame["plot_value"] = np.log10(frame["gdp_value"].clip(lower=1e9))
    else:
        frame["plot_value"] = frame[layer].clip(lower=-5, upper=15)

    hover_vals = []
    for _, row in frame.iterrows():
        raw = row.get(layer, row.get("gdp_value", 0))
        hover_vals.append(_format_hover_value(layer, raw))
    frame["hover_val"] = hover_vals

    layer_labels = {
        "gdp_value":     "GDP (log scale)",
        "gdp_growth":    "GDP Growth (%)",
        "inflation":     "Inflation (%)",
        "interest_rate": "Policy Rate (%)",
    }

    # ── Selected country highlight ─────────────────────────────────────────
    selected_iso = None
    for k, v in {"us":"USA","canada":"CAN","uk":"GBR","germany":"DEU",
                 "france":"FRA","china":"CHN","japan":"JPN","india":"IND",
                 "brazil":"BRA","australia":"AUS"}.items():
        if k == selected_country:
            selected_iso = v
            break

    fig = px.choropleth(
        frame,
        locations="iso3",
        color="plot_value",
        hover_name="country",
        custom_data=["iso3", "country_key", "hover_val",
                     "gdp_growth", "inflation", "unemployment", "interest_rate"],
        color_continuous_scale=_color_scales(layer),
        projection="natural earth",
    )

    # Highlight selected country with a distinct border
    if selected_iso:
        for trace in fig.data:
            if trace.location == selected_iso:
                trace.marker.line.color = COLORS["accent_blue"]
                trace.marker.line.width = 2.5

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            f"{layer_labels.get(layer, layer)}: " + "%{customdata[2]}<br>"
            "GDP Growth: %{customdata[3]:.1f}%<br>"
            "Inflation: %{customdata[4]:.1f}%<br>"
            "Unemployment: %{customdata[5]:.1f}%<br>"
            "Policy Rate: %{customdata[6]:.1f}%<extra></extra>"
        ),
        marker_line_width=0,
        marker_line_color="rgba(255,255,255,0.04)",
    )

    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=False,
            showocean=True,
            oceancolor="#070b12",
            landcolor="#0d1120",
            countrycolor="rgba(255,255,255,0.04)",
            subunitcolor="rgba(255,255,255,0.03)",
            showlakes=True,
            lakecolor="#070b12",
        ),
    )

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "staticPlot": False,
            "responsive": True,
        },
        on_select="rerun",
        selection_mode="points",
    )
    if event and event.selection and event.selection.get("points"):
        pt = event.selection["points"][0]
        country_key = pt["customdata"][1]
        if country_key != selected_country:
            st.session_state.selected_country = country_key
            st.rerun()