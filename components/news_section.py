"""
Macro News Flow — institutional news rendering.
All text content is sanitized before rendering. No HTML comment artifacts.
"""
from __future__ import annotations

import re
from datetime import date as date_type
from datetime import datetime

import streamlit as st

from config import COLORS, NEWS_CATEGORY_LABELS

_STRIP_HTML = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    """Remove any HTML tags and collapse whitespace."""
    if not text:
        return ""
    text = _STRIP_HTML.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


CATEGORY_ACCENTS = {
    "inflation":       "#c0524a",
    "growth":          "#4a7fc1",
    "central_bank":    "#b8943c",
    "fiscal":          "#6a9e6e",
    "trade":           "#8a6ab5",
    "geopolitics":     "#b07848",
    "labor":           "#4a8a9e",
    "markets":         "#5a7a9e",
    "sovereign_risk":  "#b84d44",
}


def _freshness(date_str: str) -> tuple[str, str]:
    if not date_str:
        return "Unknown date", "fresh-old"
    try:
        d = datetime.fromisoformat(date_str[:10]).date()
        today = date_type.today()
        delta = (today - d).days
        if delta == 0:
            return "Live today",  "fresh-today"
        if delta == 1:
            return "Last 24h",   "fresh-week"
        if delta < 7:
            return "This week",  "fresh-week"
        return f"{delta}d ago", "fresh-old"
    except Exception:
        return date_str[:10], "fresh-old"


def _source_dot(source: str) -> str:
    known = {"Reuters", "Reuters Economics", "Financial Times", "CNBC", "MarketWatch",
             "IMF", "World Bank", "BIS"}
    color = COLORS["positive_green"] if source in known else COLORS["text_muted"]
    return (
        f'<span style="display:inline-block;width:5px;height:5px;border-radius:50%;'
        f'background:{color};margin-right:5px;flex-shrink:0;"></span>'
    )


def render_news_section(news_items: list[dict], fetched_at: str) -> None:
    if not news_items:
        st.info("No news items available for the selected filter.")
        return

    left_col, right_col = st.columns(2, gap="medium")
    for idx, item in enumerate(news_items):
        target = left_col if idx % 2 == 0 else right_col
        _render_card(item, target, idx)


def _render_card(item: dict, col, idx: int) -> None:
    """
    Render a single news card. All content is pre-sanitized via _clean().
    The raw HTML template uses only CSS class names and pre-sanitized string values.
    """
    # Sanitize every string field before it touches any HTML
    cat      = _clean(item.get("category", ""))
    headline = _clean(item.get("headline", ""))
    summary  = _clean(item.get("summary", ""))
    source   = _clean(item.get("source", ""))
    date_str = item.get("date", "")
    url      = item.get("url", "")

    accent = CATEGORY_ACCENTS.get(cat, COLORS["text_secondary"])
    freshness_lbl, fresh_cls = _freshness(date_str)

    date_display = ""
    if date_str:
        try:
            date_display = datetime.fromisoformat(date_str[:10]).strftime("%b %d, %Y")
        except Exception:
            date_display = date_str[:10]

    with col:
        st.markdown(
            f"""
            <div class="news-card" style="border-left-color:{accent};">
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:9px;flex-wrap:wrap;">
                    <span class="news-cat" style="color:{accent};">{cat.replace('_',' ').title()}</span>
                    <span style="color:{COLORS['text_muted']};font-size:0.6rem;">·</span>
                    <span style="display:flex;align-items:center;">
                        {_source_dot(source)}
                        <span class="news-src">{source}</span>
                    </span>
                    <span style="color:{COLORS['text_muted']};font-size:0.6rem;margin-left:auto;">{date_display}</span>
                </div>
                <div class="news-title">{headline}</div>
                <div class="news-summary" style="margin-bottom:10px;">{summary}</div>
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span class="{fresh_cls}" style="font-size:0.62rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;">
                        ● {freshness_lbl}
                    </span>
            """,
            unsafe_allow_html=True,
        )

        if url and url.strip():
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
            except Exception:
                domain = "source"
            st.markdown(
                f"""
                    <a href="{url}" target="_blank" rel="noopener noreferrer"
                       class="news-link-btn">Read full story ↗</a>
                    <span style="font-size:0.58rem;color:{COLORS['text_muted']};margin-left:2px;">({domain})</span>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """<span class="news-no-link">Source unavailable</span>""",
                unsafe_allow_html=True,
            )

        st.markdown("</div></div>", unsafe_allow_html=True)
