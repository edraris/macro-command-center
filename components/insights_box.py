from __future__ import annotations

import streamlit as st

from utils.country_utils import get_country_metadata


def render_insights_box(country_key: str, indicators: dict, sentiment_tag: str) -> None:
    meta = get_country_metadata(country_key)
    bullets = []

    if indicators["inflation"] > 4.0 and indicators["gdp_growth"] < 2.0:
        bullets.append("Inflation remains uncomfortably high even as the growth profile softens, keeping policy tradeoffs difficult.")
    if indicators["interest_rate_delta"] >= 0:
        bullets.append("Rate settings are still leaning restrictive, which should continue to cool domestic demand with a lag.")
    if indicators["unemployment"] <= 4.5:
        bullets.append("Labor conditions are still relatively tight, limiting the speed at which domestic inflation can normalize.")
    if indicators["gdp_growth"] >= 3.5:
        bullets.append("Growth remains above developed-market trend, reinforcing a higher-for-longer backdrop for macro pricing.")
    if len(bullets) < 3:
        bullets.append(f"{meta['name']} remains exposed to external shocks through trade, energy, and global financial conditions.")
    bullets.append(f"Current regime reads as {sentiment_tag.lower()}, with the next policy signal likely driven by inflation and labor data.")

    st.markdown('<div class="mc-card insights-shell"><div class="section-heading">What Matters Now</div>', unsafe_allow_html=True)
    for bullet in bullets[:5]:
        st.markdown(
            f"""
            <div class="insight-row">
                <span class="insight-dot"></span>
                <span>{bullet}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
