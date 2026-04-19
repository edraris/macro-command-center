from __future__ import annotations

import streamlit as st

from components.chart_panel import render_trend_chart
from services.data_cache import get_country_snapshot, get_indicator_series
from utils.country_utils import get_all_countries, get_country_metadata
from utils.formatters import format_percent


def render_compare_mode() -> None:
    countries = get_all_countries()
    defaults = st.session_state.get("compare_selection", ("us", "canada"))

    st.caption("COMPARE MODE")
    st.title("Relative Country Comparison", anchor=False)
    st.caption("Side-by-side comparison of major macro indicators and trend trajectories.")

    left_picker, right_picker = st.columns(2, gap="large")
    with left_picker:
        left_country = st.selectbox(
            "Country A",
            countries,
            index=countries.index(defaults[0]) if defaults[0] in countries else 0,
            format_func=lambda key: f"{get_country_metadata(key)['flag']}  {get_country_metadata(key)['name']}",
        )
    with right_picker:
        right_country = st.selectbox(
            "Country B",
            countries,
            index=countries.index(defaults[1]) if defaults[1] in countries else 1,
            format_func=lambda key: f"{get_country_metadata(key)['flag']}  {get_country_metadata(key)['name']}",
        )

    st.session_state.compare_selection = (left_country, right_country)

    left_snapshot = get_country_snapshot(left_country)
    right_snapshot = get_country_snapshot(right_country)
    left_meta = get_country_metadata(left_country)
    right_meta = get_country_metadata(right_country)

    hdr_left, hdr_right = st.columns(2, gap="large")
    with hdr_left:
        with st.container(border=True):
            st.subheader(f"{left_meta['flag']} {left_meta['name']}", anchor=False)
            st.caption(f"{left_meta['region']}  |  {left_meta['income_group']}")
    with hdr_right:
        with st.container(border=True):
            st.subheader(f"{right_meta['flag']} {right_meta['name']}", anchor=False)
            st.caption(f"{right_meta['region']}  |  {right_meta['income_group']}")

    metrics = [
        ("GDP Growth", "gdp_growth"),
        ("Inflation", "inflation"),
        ("Unemployment", "unemployment"),
        ("Policy Rate", "interest_rate"),
        ("Debt / GDP", "debt_to_gdp"),
    ]

    metric_cols = st.columns(len(metrics), gap="medium")
    for col, (label, key) in zip(metric_cols, metrics):
        left_value = left_snapshot.get(key) or 0.0
        right_value = right_snapshot.get(key) or 0.0
        diff = left_value - right_value
        with col:
            st.metric(label=f"A {label}", value=format_percent(left_value), delta=f"{diff:+.1f} pts", border=True)
            st.metric(label=f"B {label}", value=format_percent(right_value), border=True)

    st.caption("RELATIVE POSITIONING")
    for label, key in metrics + [("Current Account", "current_account")]:
        left_value = left_snapshot.get(key) or 0.0
        right_value = right_snapshot.get(key) or 0.0
        spread = left_value - right_value
        row_left, row_mid, row_right = st.columns([2, 1, 2])
        with row_left:
            st.text(f"{left_meta['flag']} {label}: {format_percent(left_value)}")
        with row_mid:
            st.caption(f"Spread {spread:+.1f} pts")
        with row_right:
            st.text(f"{right_meta['flag']} {label}: {format_percent(right_value)}")

    chart_left, chart_right = st.columns(2, gap="large")
    metrics_to_chart = ["gdp_growth", "inflation", "unemployment", "interest_rate"]
    with chart_left:
        for metric in metrics_to_chart:
            with st.container(border=True):
                render_trend_chart(get_indicator_series(left_country, metric), metric)
    with chart_right:
        for metric in metrics_to_chart:
            with st.container(border=True):
                render_trend_chart(get_indicator_series(right_country, metric), metric)
