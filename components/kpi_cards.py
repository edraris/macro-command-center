from __future__ import annotations

import streamlit as st

from utils.formatters import format_currency, format_delta, format_percent


def render_kpi_cards(indicators: dict) -> None:
    cards = [
        ("GDP", format_currency(indicators.get("gdp_value")), None),
        ("GDP Growth", format_percent(indicators.get("gdp_growth", 0.0)), format_delta(indicators.get("gdp_growth_delta", 0.0))[0]),
        ("Inflation", format_percent(indicators.get("inflation", 0.0)), format_delta(indicators.get("inflation_delta", 0.0))[0]),
        ("Unemployment", format_percent(indicators.get("unemployment", 0.0)), format_delta(indicators.get("unemployment_delta", 0.0))[0]),
        ("Policy Rate", format_percent(indicators.get("interest_rate", 0.0)), format_delta(indicators.get("interest_rate_delta", 0.0))[0]),
    ]

    cols = st.columns(len(cards), gap="medium")
    for col, (label, value, delta) in zip(cols, cards):
        with col:
            st.metric(label=label, value=value, delta=delta, border=True)
