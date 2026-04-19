from __future__ import annotations

import re
from datetime import date as date_type
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st

from config import NEWS_CATEGORY_LABELS

_STRIP_HTML = re.compile(r"<[^>]+>")
_STRIP_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
_MULTISPACE = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = _STRIP_COMMENTS.sub(" ", text or "")
    text = _STRIP_HTML.sub(" ", text)
    return _MULTISPACE.sub(" ", text).strip()


def _validate_url(url: str) -> str:
    clean_url = _clean(url)
    parsed = urlparse(clean_url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return clean_url
    return ""


def _freshness(date_str: str) -> str:
    if not date_str:
        return "Undated"
    try:
        delta = (date_type.today() - datetime.fromisoformat(date_str[:10]).date()).days
    except Exception:
        return "Undated"
    if delta <= 0:
        return "Fresh today"
    if delta == 1:
        return "Last 24h"
    if delta < 7:
        return "This week"
    return f"{delta}d old"


def render_news_section(news_items: list[dict], fetched_at: str) -> None:
    if not news_items:
        st.info("No news items available for the selected filter.")
        return

    left_col, right_col = st.columns(2, gap="large")
    for idx, item in enumerate(news_items):
        with (left_col if idx % 2 == 0 else right_col):
            _render_card(item)
    st.caption(f"News cache updated {fetched_at}")


def _render_card(item: dict) -> None:
    category_key = _clean(item.get("category", ""))
    headline = _clean(item.get("headline", ""))
    summary = _clean(item.get("summary", ""))
    source = _clean(item.get("source", "Source unavailable"))
    date_str = _clean(item.get("date", ""))
    url = _validate_url(item.get("url", ""))
    date_display = date_str[:10] if date_str else "N/A"
    category_label = NEWS_CATEGORY_LABELS.get(category_key, category_key.replace("_", " ").title())

    with st.container(border=True):
        st.caption(f"{category_label}  |  {source}")
        st.caption(f"{date_display}  |  {_freshness(date_str)}")
        st.subheader(headline, anchor=False)
        st.caption(summary)
        if url:
            st.link_button("Open Story", url)
        else:
            st.caption("Verified link unavailable.")
