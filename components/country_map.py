from __future__ import annotations

import numpy as np
import plotly.express as px
import streamlit as st

from config import COLORS
from services.data_cache import get_map_dataset
from utils.formatters import format_currency


def render_map(selected_country: str = None) -> None:
    frame = get_map_dataset()
    frame = frame.copy()
    frame["gdp_log"] = np.log10(frame["gdp_value"])
    frame["hover_gdp"] = frame["gdp_value"].apply(format_currency)

    figure = px.choropleth(
        frame,
        locations="iso3",
        color="gdp_log",
        hover_name="country",
        custom_data=["country_key", "hover_gdp", "gdp_growth", "inflation", "unemployment", "interest_rate"],
        color_continuous_scale=["#10213a", COLORS["accent_blue"]],
        projection="natural earth",
    )
    figure.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>GDP %{customdata[1]}<br>Growth %{customdata[2]:.1f}%<br>Inflation %{customdata[3]:.1f}%<br>Unemployment %{customdata[4]:.1f}%<br>Policy Rate %{customdata[5]:.1f}%<extra></extra>",
        marker_line_width=0,
    )
    figure.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=False,
            showocean=True,
            oceancolor="#05070d",
            landcolor="#0f1320",
        ),
    )

    event = st.plotly_chart(
        figure,
        use_container_width=True,
        config={"displayModeBar": False},
        on_select="rerun",
        selection_mode="points",
    )
    if event and event.selection and event.selection.get("points"):
        point = event.selection["points"][0]
        st.session_state.selected_country = point["customdata"][0]
