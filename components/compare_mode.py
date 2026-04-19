"""
Country comparison view — side-by-side institutional layout.
"""
from __future__ import annotations

import streamlit as st

from config import COLORS
from components.chart_panel import render_trend_chart
from services.data_cache import get_country_snapshot, get_indicator_series
from utils.country_utils import get_all_countries, get_country_metadata
from utils.formatters import format_percent


def render_compare_mode() -> None:
    countries = get_all_countries()
    defaults = st.session_state.get("compare_selection", ("us", "canada"))

    st.markdown("<div class='sm'></div>", unsafe_allow_html=True)

    sel_left, sel_right = st.columns(2, gap="medium")
    with sel_left:
        left_country = st.selectbox(
            "Country A",
            countries,
            index=countries.index(defaults[0]) if defaults[0] in countries else 0,
            format_func=lambda k: f"{get_country_metadata(k)['flag']}  {get_country_metadata(k)['name']}",
        )
    with sel_right:
        right_country = st.selectbox(
            "Country B",
            countries,
            index=countries.index(defaults[1]) if defaults[1] in countries else 1,
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
            f"<div class='cmp-country'>{lmeta['flag']}  {lmeta['name']}</div>"
            f"<div class='cmp-meta'>{lmeta['region']} · {lmeta['income_group']}</div>",
            unsafe_allow_html=True,
        )
    with hdr_r:
        st.markdown(
            f"<div class='cmp-country'>{rmeta['flag']}  {rmeta['name']}</div>"
            f"<div class='cmp-meta'>{rmeta['region']} · {rmeta['income_group']}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='sm'></div>", unsafe_allow_html=True)

    # ── KPI comparison row ─────────────────────────────────────────────────
    kpi_metrics = [
        ("GDP Growth",   "gdp_growth",    True),
        ("Inflation",    "inflation",     False),
        ("Unemploy.",   "unemployment",   False),
        ("Policy Rate", "interest_rate", False),
        ("Debt / GDP",  "debt_to_gdp",   False),
    ]

    cols = st.columns(5)
    for col, (label, key, higher_better) in zip(cols, kpi_metrics):
        lv = lsnap.get(key) or 0
        rv = rsnap.get(key) or 0
        with col:
            # Left country value
            st.markdown(
                f"""<div class="kpi" style="padding:12px 14px;margin-bottom:4px;">
                    <div class="kpi-label" style="color:{COLORS['accent_blue']};">{lmeta['flag']} {label}</div>
                    <div class="kpi-value" style="font-size:1.1rem;">{format_percent(lv)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            # Right country value
            diff = lv - rv
            color = (
                COLORS["positive_green"] if (diff > 0.05) == higher_better else
                COLORS["negative_red"] if abs(diff) > 0.05 else
                COLORS["text_secondary"]
            )
            st.markdown(
                f"""<div class="kpi" style="padding:10px 14px;">
                    <div class="kpi-label" style="color:{COLORS['amber']};">{rmeta['flag']} {label}</div>
                    <div class="kpi-value" style="font-size:1.1rem;">{format_percent(rv)}</div>
                    <div class="kpi-delta" style="color:{color};font-size:0.65rem;">
                        {format_percent(abs(diff))} {'A adv.' if (diff > 0.05) == higher_better else 'B adv.' if abs(diff) > 0.05 else '~'}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div class='md'></div>", unsafe_allow_html=True)

    # ── Relative positioning table ─────────────────────────────────────────
    st.markdown(
        f"<div class='sec-label' style='margin-bottom:10px;'>Relative Positioning — {lmeta['flag']} vs {rmeta['flag']}</div>",
        unsafe_allow_html=True,
    )

    for metric, label, higher_better in [
        ("gdp_growth",    "GDP Growth",    True),
        ("inflation",     "Inflation",     False),
        ("unemployment",  "Unemployment",  False),
        ("interest_rate", "Policy Rate",   False),
        ("debt_to_gdp",   "Debt / GDP",    False),
        ("current_account","Curr. Account",False),
    ]:
        lv = lsnap.get(metric) or 0
        rv = rsnap.get(metric) or 0
        diff = lv - rv
        winner = "left" if (diff > 0.05) == higher_better else "right" if (diff < -0.05) == higher_better else "even"
        wc = {"left": COLORS["positive_green"], "right": COLORS["negative_red"], "even": COLORS["text_secondary"]}[winner]
        diff_str = format_percent(abs(diff))
        st.markdown(
            f"""<div class="cmp-row">
                <span style="color:{COLORS['text_secondary']};font-size:0.8rem;">{label}</span>
                <span class="cmp-better" style="color:{wc};">{format_percent(lv)}  vs  {format_percent(rv)}  <span style="color:{COLORS['text_muted']};font-size:0.65rem;">({diff_str})</span></span>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='md'></div>", unsafe_allow_html=True)

    # ── Trend charts ─────────────────────────────────────────────────────────
    chart_l, chart_r = st.columns(2, gap="medium")
    metrics = ["gdp_growth", "inflation", "unemployment", "interest_rate"]
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
