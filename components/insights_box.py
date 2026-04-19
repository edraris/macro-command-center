from __future__ import annotations

import re

import streamlit as st

from config import SENTIMENT_TAGS
from data.country_data import get_country_metadata

_STRIP_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
_STRIP_HTML = re.compile(r"<[^>]+>")
_MULTISPACE = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = _STRIP_COMMENTS.sub(" ", text or "")
    text = _STRIP_HTML.sub(" ", text)
    return _MULTISPACE.sub(" ", text).strip()


def render_insights_box(country_key: str, indicators: dict, sentiment_tag: str) -> None:
    meta = get_country_metadata(country_key)
    bullets = [
        f"{_clean(meta['name'])} remains exposed to global rates, trade conditions, and energy-price volatility.",
        f"Inflation is running at {indicators.get('inflation', 0):.1f}% and growth at {indicators.get('gdp_growth', 0):.1f}%.",
        f"Policy rates stand at {indicators.get('interest_rate', 0):.1f}% and unemployment at {indicators.get('unemployment', 0):.1f}%.",
        f"Current regime: {_clean(sentiment_tag)}. {_clean(SENTIMENT_TAGS.get(sentiment_tag, 'The macro backdrop remains fluid.'))}",
    ]
    with st.container(border=True):
        st.caption("WHAT MATTERS NOW")
        st.subheader("Analyst Notes", anchor=False)
        for bullet in bullets:
            st.write(f"- {bullet}")
