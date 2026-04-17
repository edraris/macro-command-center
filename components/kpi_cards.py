from __future__ import annotations

import streamlit as st

from config import COLORS
from utils.formatters import format_currency, format_delta, format_percent


def render_kpi_cards(indicators: dict) -> None:
    cards = [
        ("GDP", format_currency(indicators.get("gdp_value")), None, COLORS["text_secondary"]),
        ("GDP Growth", format_percent(indicators.get("gdp_growth", 0.0)), *format_delta(indicators.get("gdp_growth_delta", 0.0))),
        ("Inflation", format_percent(indicators.get("inflation", 0.0)), *format_delta(indicators.get("inflation_delta", 0.0))),
        ("Unemployment", format_percent(indicators.get("unemployment", 0.0)), *format_delta(indicators.get("unemployment_delta", 0.0))),
        ("Policy Rate", format_percent(indicators.get("interest_rate", 0.0)), *format_delta(indicators.get("interest_rate_delta", 0.0))),
    ]

    columns = st.columns(5, gap="medium")
    for column, (label, value, delta_text, delta_color) in zip(columns, cards):
        if label == "Inflation" and indicators.get("inflation", 0.0) > 4.0:
            delta_color = COLORS["negative_red"]
        with column:
            st.markdown(
                f"""
                <div class="mc-card mc-kpi-card">
                    <div class="mc-kpi-label">{label}</div>
                    <div class="mc-kpi-value">{value}</div>
                    <div class="mc-kpi-delta" style="color:{delta_color};">{delta_text or "&nbsp;"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
