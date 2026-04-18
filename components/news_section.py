"""
Macro News Flow — institutional news rendering.
Every item shows: real headline, real source, date/time, real URL or "No source link available".
Freshness badges: Live today / Last 24h / This week.
Categories with muted accent colours.
"""
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone

import streamlit as st

from config import COLORS, NEWS_CATEGORY_LABELS

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
    """
    Returns (label, css_class) for the freshness badge.
    """
    if not date_str:
        return "Unknown date", "fresh-old"
    try:
        d = datetime.fromisoformat(date_str[:10]).date()
        today = date_type.today()
        delta = (today - d).days
        if delta == 0:
            return "Live today",   "fresh-today"
        if delta == 1:
            return "Last 24h",    "fresh-week"
        if delta < 7:
            return f"This week",  "fresh-week"
        return f"{delta}d ago",  "fresh-old"
    except Exception:
        return date_str[:10], "fresh-old"


def _source_dot(source: str) -> str:
    """Return a coloured dot for the source credibility indicator."""
    known = {"Reuters", "Reuters Economics", "Financial Times", "CNBC", "MarketWatch",
             "IMF", "World Bank", "BIS"}
    color = COLORS["positive_green"] if source in known else COLORS["text_muted"]
    return f'<span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:{color};margin-right:5px;flex-shrink:0;"></span>'


def render_news_section(news_items: list[dict], fetched_at: str) -> None:
    if not news_items:
        st.info("No news items available for the selected filter.")
        return

    left_col, right_col = st.columns(2, gap="medium")

    for idx, item in enumerate(news_items):
        target = left_col if idx % 2 == 0 else right_col
        _render_card(item, target, idx)


def _render_card(item: dict, col, idx: int) -> None:
    cat    = item.get("category", "growth")
    accent = CATEGORY_ACCENTS.get(cat, COLORS["text_secondary"])
    headline   = item.get("headline", "No headline")
    summary    = item.get("summary", "")
    source     = item.get("source", "Source unavailable")
    date_str   = item.get("date", "")
    url        = item.get("url", "")

    freshness_lbl, fresh_cls = _freshness(date_str)

    # Format date nicely for display
    date_display = ""
    if date_str:
        try:
            date_display = datetime.fromisoformat(date_str[:10]).strftime("%b %d, %Y")
        except Exception:
            date_display = date_str[:10]

    with col:
        with st.container():
            st.markdown(
                f"""
                <div class="news-card" style="border-left-color:{accent};">
                    <!-- Meta row -->
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap;">
                        <span class="news-cat" style="color:{accent};">{cat.replace('_',' ').title()}</span>
                        <span style="color:{COLORS['text_muted']};font-size:0.6rem;">·</span>
                        <span style="display:flex;align-items:center;">
                            {_source_dot(source)}
                            <span class="news-src">{source}</span>
                        </span>
                        <span style="color:{COLORS['text_muted']};font-size:0.6rem;margin-left:auto;">
                            {date_display}
                        </span>
                    </div>

                    <!-- Headline -->
                    <div class="news-title">{headline}</div>

                    <!-- Summary -->
                    <div class="news-summary" style="margin-bottom:12px;">{summary}</div>

                    <!-- Bottom row: freshness + link -->
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        <span class="{fresh_cls}" style="font-size:0.65rem;font-weight:600;
                                                        letter-spacing:0.06em;text-transform:uppercase;">
                            ● {freshness_lbl}
                        </span>
                """,
                unsafe_allow_html=True,
            )

            # URL — only render if it's a real, non-empty URL
            if url and url.strip():
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                except Exception:
                    domain = "source"

                st.markdown(
                    f"""
                        <a href="{url}" target="_blank" rel="noopener noreferrer"
                           class="news-link-btn" style="font-size:0.65rem;">
                            Read full story ↗
                        </a>
                        <span style="font-size:0.6rem;color:{COLORS['text_muted']};margin-left:2px;">
                            ({domain})
                        </span>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """<span class="news-no-link">No source link available</span>""",
                    unsafe_allow_html=True,
                )

            st.markdown("</div></div>", unsafe_allow_html=True)