"""
KPI metric cards — institutional presentation.
5-column grid, restrained palette, no decorative elements.
"""
from __future__ import annotations

import streamlit as st

from config import COLORS
from utils.formatters import format_currency, format_delta, format_percent


def render_kpi_cards(indicators: dict) -> None:
    cards = [
        ("GDP",        format_currency(indicators.get("gdp_value")), None,                           COLORS["text_muted"]),
        ("GDP Growth", format_percent(indicators.get("gdp_growth", 0.0)),       *format_delta(indicators.get("gdp_growth_delta", 0.0))),
        ("Inflation",  format_percent(indicators.get("inflation", 0.0)),          *format_delta(indicators.get("inflation_delta", 0.0))),
        ("Unemploy.",  format_percent(indicators.get("unemployment", 0.0)),     *format_delta(indicators.get("unemployment_delta", 0.0))),
        ("Policy Rate",format_percent(indicators.get("interest_rate", 0.0)),     *format_delta(indicators.get("interest_rate_delta", 0.0))),
    ]

    cols = st.columns(5, gap="medium")
    for col, (label, value, delta_text, delta_color) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-delta" style="color:{delta_color};">
                        {delta_text or "&nbsp;"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
