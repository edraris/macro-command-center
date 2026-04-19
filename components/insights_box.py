"""
What Matters Now — institutional macro commentary box.
All bullets are pure plain text — any HTML from regime tags is stripped at render.
"""
from __future__ import annotations

import re
import streamlit as st

from config import COLORS, SENTIMENT_TAGS
from data.country_data import get_country_metadata


_STRIP_HTML = re.compile(r"<[^>]+>")
_STRIP_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
_MULTI_SPACE = re.compile(r"\s+")


def _clean(text: str) -> str:
    if not text:
        return ""
    text = _STRIP_COMMENTS.sub("", text)
    text = _STRIP_HTML.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text).strip()
    return text


def render_insights_box(country_key: str, indicators: dict, sentiment_tag: str) -> None:
    meta = get_country_metadata(country_key)
    bullets = []

    inf  = indicators.get("inflation", 0)
    grow = indicators.get("gdp_growth", 0)
    unem = indicators.get("unemployment", 0)
    rate_delta = indicators.get("interest_rate_delta", 0)
    debt = indicators.get("debt_to_gdp", 0)
    ca   = indicators.get("current_account", 0)

    # Inflation framing
    if inf > 4.0 and grow < 2.0:
        bullets.append(
            f"Inflation at {inf:.1f}% keeps policy trade-offs difficult "
            "even as growth is running below trend. Rate easing is likely delayed."
        )
    elif inf > 4.0:
        bullets.append(
            f"Elevated inflation ({inf:.1f}%) remains the primary constraint "
            "on monetary policy. Services prices are the main residual risk."
        )
    elif inf < 2.0:
        bullets.append(
            f"Inflation at {inf:.1f}% is near or below target, "
            "giving the central bank room to ease if growth softens materially."
        )
    else:
        bullets.append(
            f"Inflation at {inf:.1f}% is close to target. "
            "Focus shifts to sustaining that progress without premature loosening."
        )

    # Rate delta framing
    if rate_delta >= 0:
        bullets.append(
            f"Rate settings are on hold or rising ({rate_delta:+.1f} pts), "
            "maintaining a restrictive stance. Transmission takes 12–18 months."
        )
    elif rate_delta <= -0.5:
        bullets.append(
            f"Rate cuts ({rate_delta:+.1f} pts) are now in train, "
            "supporting growth with a typical 12–18 month transmission lag."
        )

    # Labour market framing
    if unem <= 4.0:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals a tight labour market "
            "that underpins services inflation and limits easing scope."
        )
    elif unem >= 6.5:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals labour market slack "
            "that should eventually ease wage and services price pressures."
        )

    # Growth framing
    if grow >= 3.5:
        bullets.append(
            f"Growth of {grow:.1f}% is running above developed-market trend, "
            "reinforcing a higher-for-longer rate backdrop."
        )
    elif grow < 1.0:
        bullets.append(
            f"Growth of {grow:.1f}% signals meaningful economic slack. "
            "Active monitoring of recession signals is warranted."
        )

    # External exposure
    bullets.append(
        f"{meta['name']} retains exposure to external shocks via trade channels, "
        "energy costs, and global financial conditions — material given current geopolitical fragmentation."
    )

    # Regime — plain text only, no HTML
    regime_clean = _clean(sentiment_tag)
    sentiment_clean = _clean(SENTIMENT_TAGS.get(sentiment_tag, "The macro backdrop remains fluid."))
    bullets.append(
        f"Current regime: {regime_clean}. {sentiment_clean}"
    )

    st.markdown(
        f"""<div class="mc-card">
        <div class="sec-label" style="margin-bottom:12px;">What Matters Now</div>
        """,
        unsafe_allow_html=True,
    )
    for b in bullets[:6]:
        st.markdown(
            f"""<div class="ins-row"><span class="ins-dot"></span><span>{b}</span></div>""",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
