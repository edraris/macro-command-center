"""
Country comparison view — side-by-side institutional layout.
"""
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

    st.markdown("<div class='spacer-sm'></div>", unsafe_allow_html=True)

    sel_left, sel_right = st.columns(2, gap="medium")
    with sel_left:
        left_country = st.selectbox(
            "Country A",
            countries,
            index=countries.index(defaults[0]),
            format_func=lambda k: f"{get_country_metadata(k)['flag']}  {get_country_metadata(k)['name']}",
        )
    with sel_right:
        right_country = st.selectbox(
            "Country B",
            countries,
            index=countries.index(defaults[1]),
            format_func=lambda k: f"{get_country_metadata(k)['flag']}  {get_country_metadata(k)['name']}",
        )
    st.session_state.compare_selection = (left_country, right_country)

    lsnap = get_country_snapshot(left_country)
    rsnap = get_country_snapshot(right_country)
    lmeta = get_country_metadata(left_country)
    rmeta = get_country_metadata(right_country)

    # ── Country labels ─────────────────────────────────────────────────────
    hdr_l, hdr_r = st.columns(2, gap="medium")
    with hdr_l:
        st.markdown(
            f"<div class='country-name-large'>{lmeta['flag']}  {lmeta['name']}</div>"
            f"<div class='country-meta'>{lmeta['region']} · {lmeta['income_group']}</div>",
            unsafe_allow_html=True,
        )
    with hdr_r:
        st.markdown(
            f"<div class='country-name-large'>{rmeta['flag']}  {rmeta['name']}</div>"
            f"<div class='country-meta'>{rmeta['region']} · {rmeta['income_group']}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='spacer-sm'></div>", unsafe_allow_html=True)

    # ── KPI row ─────────────────────────────────────────────────────────────
    kpi_l, kpi_r = st.columns(2, gap="medium")
    with kpi_l:
        render_kpi_cards(lsnap)
    with kpi_r:
        render_kpi_cards(rsnap)

    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ── Relative positioning table ─────────────────────────────────────────
    st.markdown("<div class='section-label'>Relative Positioning</div>", unsafe_allow_html=True)

    metrics = ["gdp_growth", "inflation", "unemployment", "interest_rate"]
    for metric in metrics:
        lv = lsnap[metric]
        rv = rsnap[metric]
        diff = lv - rv
        if metric == "gdp_growth":
            winner = "left" if diff > 0.1 else "right" if diff < -0.1 else "even"
        else:  # lower is better for these
            winner = "left" if diff < -0.1 else "right" if diff > 0.1 else "even"
        wc = {"left": COLORS["positive_green"], "right": COLORS["negative_red"], "even": COLORS["text_secondary"]}[winner]
        label = metric.replace("_", " ").title()
        st.markdown(
            f"""
            <div class="compare-row">
                <span style="color:{COLORS['text_secondary']};">{label}</span>
                <span style="color:{wc};">{format_percent(lv)}  vs  {format_percent(rv)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='spacer-md'></div>", unsafe_allow_html=True)

    # ── Trend charts ─────────────────────────────────────────────────────────
    chart_l, chart_r = st.columns(2, gap="medium")
    with chart_l:
        for metric in metrics:
            st.markdown('<div class="mc-card" style="padding:14px 14px 6px;margin-bottom:12px;">', unsafe_allow_html=True)
            render_trend_chart(get_indicator_series(left_country, metric), metric)
            st.markdown("</div>", unsafe_allow_html=True)
    with chart_r:
        for metric in metrics:
            st.markdown('<div class="mc-card" style="padding:14px 14px 6px;margin-bottom:12px;">', unsafe_allow_html=True)
            render_trend_chart(get_indicator_series(right_country, metric), metric)
            st.markdown("</div>", unsafe_allow_html=True)
