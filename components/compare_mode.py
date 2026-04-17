from __future__ import annotations

import streamlit as st

from components.chart_panel import render_trend_chart
from components.kpi_cards import render_kpi_cards
from services.data_cache import get_country_snapshot, get_indicator_series
from utils.country_utils import get_all_countries, get_country_metadata
from utils.formatters import format_percent


def render_compare_mode() -> None:
    countries = get_all_countries()
    defaults = st.session_state.get("compare_selection", ("us", "china"))

    left_selector, right_selector = st.columns(2, gap="medium")
    with left_selector:
        left_country = st.selectbox("Left country", countries, index=countries.index(defaults[0]), format_func=lambda key: get_country_metadata(key)["name"])
    with right_selector:
        right_country = st.selectbox("Right country", countries, index=countries.index(defaults[1]), format_func=lambda key: get_country_metadata(key)["name"])

    st.session_state.compare_selection = (left_country, right_country)

    left_snapshot = get_country_snapshot(left_country)
    right_snapshot = get_country_snapshot(right_country)
    left_meta = get_country_metadata(left_country)
    right_meta = get_country_metadata(right_country)

    title_left, title_right = st.columns(2, gap="medium")
    title_left.markdown(f"### {left_meta['flag']} {left_meta['name']}")
    title_right.markdown(f"### {right_meta['flag']} {right_meta['name']}")

    split_left, split_right = st.columns(2, gap="medium")
    with split_left:
        render_kpi_cards(left_snapshot)
    with split_right:
        render_kpi_cards(right_snapshot)

    st.markdown('<div class="section-heading">Relative Positioning</div>', unsafe_allow_html=True)
    metrics = ["gdp_growth", "inflation", "unemployment", "interest_rate"]
    for metric in metrics:
        left_value = left_snapshot[metric]
        right_value = right_snapshot[metric]
        diff = left_value - right_value
        better = "left-better" if metric == "gdp_growth" and diff > 0 else "left-better" if metric in {"inflation", "unemployment", "interest_rate"} and diff < 0 else "right-better"
        st.markdown(
            f"""
            <div class="compare-row">
                <span>{metric.replace('_', ' ').title()}</span>
                <span class="{better}">{format_percent(left_value)} vs {format_percent(right_value)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    chart_left, chart_right = st.columns(2, gap="medium")
    with chart_left:
        for metric in metrics:
            st.markdown('<div class="mc-card compare-chart">', unsafe_allow_html=True)
            render_trend_chart(get_indicator_series(left_country, metric), metric)
            st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        for metric in metrics:
            st.markdown('<div class="mc-card compare-chart">', unsafe_allow_html=True)
            render_trend_chart(get_indicator_series(right_country, metric), metric)
            st.markdown("</div>", unsafe_allow_html=True)
