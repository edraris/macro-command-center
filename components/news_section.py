from __future__ import annotations

import streamlit as st

from config import COLORS, NEWS_CATEGORIES
from utils.formatters import format_date, truncate

CATEGORY_COLORS = {
    "inflation": COLORS["negative_red"],
    "growth": COLORS["accent_blue"],
    "central_bank": COLORS["amber"],
    "fiscal": "#64d2ff",
    "trade": "#bf5af2",
    "geopolitics": "#ff9f0a",
}


def render_news_section(news_items: list[dict], category_filter: str = None) -> None:
    active = [item for item in news_items if not category_filter or item["category"] == category_filter]
    st.markdown(
        f"""
        <div class="section-heading-row">
            <div class="section-heading">Macro News Flow</div>
            <div class="section-badge">{len(active)} items</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chips = st.columns(len(NEWS_CATEGORIES) + 1)
    options = [None] + NEWS_CATEGORIES
    labels = ["All"] + [item.replace("_", " ").title() for item in NEWS_CATEGORIES]
    for column, option, label in zip(chips, options, labels):
        is_active = option == category_filter or (option is None and category_filter is None)
        if column.button(label, use_container_width=True, key=f"news-chip-{label}"):
            st.session_state.news_category_filter = option
        if is_active:
            column.markdown('<div class="chip-active"></div>', unsafe_allow_html=True)

    left_col, right_col = st.columns(2, gap="medium")
    for index, item in enumerate(active):
        target = left_col if index % 2 == 0 else right_col
        color = CATEGORY_COLORS[item["category"]]
        with target:
            with st.container():
                summary = truncate(item["summary"], 155)
                st.markdown(
                    f"""
                    <article class="mc-card news-card fade-in">
                        <div class="news-meta-row">
                            <span class="news-pill" style="background:{color}22;color:{color};">{item["category"].replace("_", " ").title()}</span>
                            <span class="news-source">{item["source"]}</span>
                            <span class="news-date">{format_date(item["date"])}</span>
                        </div>
                        <div class="news-title">{item["headline"]}</div>
                        <div class="news-summary">{summary}</div>
                        <div class="news-link"><a href="{item['url']}" target="_blank">Open story ↗</a></div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
