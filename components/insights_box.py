"""
What Matters Now — institutional macro commentary box.
Sharp, evidence-based bullets, no motivational language.
"""
from __future__ import annotations

import streamlit as st

from config import COLORS
from utils.country_utils import get_country_metadata


def render_insights_box(country_key: str, indicators: dict, sentiment_tag: str) -> None:
    meta = get_country_metadata(country_key)
    bullets = []

    # Rule-based commentary — sharper than templated fluff
    if indicators["inflation"] > 4.0 and indicators["gdp_growth"] < 2.0:
        bullets.append(
            f"Inflation at {indicators['inflation']:.1f}% keeps policy trade-offs difficult "
            "even as growth is running below trend. Rate easing is likely delayed."
        )
    elif indicators["inflation"] > 4.0:
        bullets.append(
            f"Elevated inflation ({indicators['inflation']:.1f}%) remains the primary constraint "
            "on monetary policy. Services prices are the main residual risk."
        )
    elif indicators["inflation"] < 2.0:
        bullets.append(
            f"Inflation at {indicators['inflation']:.1f}% is near or below target, "
            "giving the central bank room to ease if growth softens materially."
        )

    if indicators["interest_rate_delta"] >= 0:
        bullets.append(
            f"Rate settings are on hold or rising ({indicators['interest_rate_delta']:+.1f} pts), "
            "maintaining a restrictive stance that should cool demand with a lag."
        )
    elif indicators["interest_rate_delta"] <= -0.5:
        bullets.append(
            f"Rate cuts ({indicators['interest_rate_delta']:+.1f} pts) are now in train, "
            "supporting growth with a typical 12–18 month transmission lag."
        )

    if indicators["unemployment"] <= 4.0:
        bullets.append(
            f"Unemployment at {indicators['unemployment']:.1f}% signals a tight labour market "
            "that continues to underpin services inflation and limits easing scope."
        )
    elif indicators["unemployment"] >= 6.5:
        bullets.append(
            f"Unemployment at {indicators['unemployment']:.1f}% signals labour market slack "
            "that should eventually ease wage and services price pressures."
        )

    if indicators["gdp_growth"] >= 3.5:
        bullets.append(
            f"Growth of {indicators['gdp_growth']:.1f}% is running above developed-market trend, "
            "reinforcing a higher-for-longer rate backdrop for macro pricing."
        )
    elif indicators["gdp_growth"] < 1.0:
        bullets.append(
            f"Growth of {indicators['gdp_growth']:.1f}% signals meaningful economic slack. "
            "Active monitoring of recession signals is warranted."
        )

    # Always include exposure note and current regime
    bullets.append(
        f"{meta['name']} retains exposure to external shocks via trade channels, "
        "energy costs, and global financial conditions — a material consideration "
        "given current geopolitical fragmentation."
    )
    bullets.append(
        f"Current regime reads as <strong>{sentiment_tag}</strong>. "
        "The next policy signal will be driven primarily by inflation trajectory and labour market data."
    )

    st.markdown(
        f"""
        <div class="insights-box">
            <div class="section-label" style="margin-bottom:14px;">What Matters Now</div>
        """,
        unsafe_allow_html=True,
    )
    for bullet in bullets[:6]:
        st.markdown(
            f"""
            <div class="insight-item">
                <span class="insight-dot"></span>
                <span>{bullet}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
