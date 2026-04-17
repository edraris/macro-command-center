from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional during bare import verification
    def load_dotenv() -> bool:
        return False

from components.chart_panel import render_trend_grid
from components.compare_mode import render_compare_mode
from components.country_map import render_map
from components.header import render_header
from components.insights_box import render_insights_box
from components.kpi_cards import render_kpi_cards
from components.news_section import render_news_section
from components.search_bar import render_search
from config import COLORS
from utils.country_utils import get_all_countries, get_country_metadata
from services.data_cache import clear_all_caches, get_country_snapshot, get_indicator_series
from services.news_service import get_all_news
from utils.country_utils import get_country_metadata
from utils.formatters import format_date
from utils.sentiment import get_market_sentiment

load_dotenv()


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            :root {{
                --bg: {COLORS["background"]};
                --card: {COLORS["card_surface"]};
                --border: {COLORS["card_border"]};
                --text: {COLORS["text_primary"]};
                --muted: {COLORS["text_secondary"]};
                --accent: {COLORS["accent_blue"]};
                --positive: {COLORS["positive_green"]};
                --negative: {COLORS["negative_red"]};
                --amber: {COLORS["amber"]};
                --radius: 20px;
                --pad: 24px;
                --gap: 20px;
                --section-gap: 40px;
            }}
            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(41,151,255,0.18), transparent 26%),
                    radial-gradient(circle at top right, rgba(255,255,255,0.05), transparent 18%),
                    linear-gradient(180deg, #090b12 0%, var(--bg) 100%);
                color: var(--text);
                font-family: "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            .block-container {{
                max-width: 1500px;
                padding-top: 28px;
                padding-bottom: 48px;
            }}
            .mc-card, .hero-shell {{
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                backdrop-filter: blur(22px);
                -webkit-backdrop-filter: blur(22px);
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
            }}
            .hero-shell {{
                padding: 30px;
                margin-bottom: var(--section-gap);
            }}
            .hero-topline {{
                color: var(--accent);
                font-size: 0.74rem;
                letter-spacing: 0.22em;
                text-transform: uppercase;
                margin-bottom: 18px;
            }}
            .hero-title {{
                font-size: 2.8rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                line-height: 1;
            }}
            .hero-subtitle {{
                color: var(--muted);
                font-size: 0.95rem;
                margin-top: 8px;
            }}
            .hero-nav {{
                display: flex;
                gap: 12px;
                margin-top: 24px;
                flex-wrap: wrap;
            }}
            .hero-nav span, .section-badge, .news-pill {{
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(255,255,255,0.06);
                color: var(--text);
                font-size: 0.76rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}
            .section-heading-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 14px;
            }}
            .section-heading {{
                font-size: 1rem;
                font-weight: 600;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}
            .country-header {{
                display: flex;
                justify-content: space-between;
                gap: 16px;
                align-items: flex-start;
                margin-bottom: 18px;
            }}
            .country-name {{
                font-size: 2rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }}
            .country-meta, .as-of-text, .news-source, .news-date, .sentiment-copy {{
                color: var(--muted);
                font-size: 0.9rem;
            }}
            .mc-kpi-card {{
                padding: var(--pad);
                min-height: 180px;
                transition: transform 140ms ease, border-color 140ms ease;
            }}
            .mc-kpi-card:hover {{
                transform: translateY(-4px);
                border-color: rgba(41,151,255,0.35);
            }}
            .mc-kpi-label {{
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.78rem;
            }}
            .mc-kpi-value {{
                font-size: 2.2rem;
                font-weight: 700;
                margin-top: 18px;
            }}
            .mc-kpi-delta {{
                margin-top: 20px;
                font-size: 0.92rem;
                font-weight: 600;
            }}
            .stMarkdown p {{
                color: var(--text);
            }}
            [data-testid="stSidebar"] {{
                background: rgba(8, 10, 15, 0.95);
                border-right: 1px solid var(--border);
            }}
            .insights-shell {{
                padding: var(--pad);
            }}
            .insight-row {{
                display: flex;
                gap: 12px;
                align-items: flex-start;
                margin-top: 14px;
                font-size: 0.95rem;
            }}
            .insight-dot {{
                width: 8px;
                height: 8px;
                margin-top: 7px;
                border-radius: 999px;
                background: var(--accent);
                box-shadow: 0 0 0 6px rgba(41,151,255,0.12);
                flex: 0 0 auto;
            }}
            .sentiment-pill {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                padding: 12px 16px;
                border-radius: 999px;
                background: rgba(48, 209, 88, 0.10);
                border: 1px solid rgba(48, 209, 88, 0.24);
                margin-bottom: 10px;
            }}
            .news-card {{
                padding: var(--pad);
                margin-bottom: 20px;
                min-height: 220px;
            }}
            .news-meta-row {{
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
                margin-bottom: 14px;
            }}
            .news-title {{
                font-size: 1.06rem;
                font-weight: 700;
                line-height: 1.35;
                margin-bottom: 10px;
            }}
            .news-summary {{
                color: var(--muted);
                font-size: 0.9rem;
                line-height: 1.5;
                min-height: 52px;
            }}
            .news-link {{
                margin-top: 16px;
                text-align: right;
            }}
            .news-link a {{
                color: var(--accent);
                text-decoration: none;
            }}
            .fade-in {{
                animation: fadeUp 420ms ease both;
            }}
            .chip-active {{
                height: 2px;
                background: var(--accent);
                border-radius: 999px;
                margin-top: 6px;
            }}
            .compare-row {{
                display: flex;
                justify-content: space-between;
                padding: 14px 0;
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }}
            .left-better {{
                color: var(--positive);
                font-weight: 600;
            }}
            .right-better {{
                color: var(--amber);
                font-weight: 600;
            }}
            .compare-chart {{
                padding: 16px;
                margin-bottom: 16px;
            }}
            @keyframes fadeUp {{
                from {{ opacity: 0; transform: translateY(6px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @media (max-width: 960px) {{
                .country-header, .section-heading-row {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "selected_country": "us",
        "compare_mode": False,
        "news_category_filter": None,
        "fred_api_key_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Macro Center")
        render_search()
        st.divider()
        st.markdown("### Countries")
        for country_key in get_all_countries():
            meta = get_country_metadata(country_key)
            if st.button(f"{meta['flag']} {meta['name']}", key=f"side-country-{country_key}", use_container_width=True):
                st.session_state.selected_country = country_key
                st.session_state.compare_mode = False
        st.divider()
        st.markdown("### Settings")
        st.session_state.compare_mode = st.toggle("Compare mode", value=st.session_state.compare_mode)
        st.text_input("FRED API Key", key="fred_api_key_input", type="password", placeholder="Loaded from env by default")
        if st.button("Clear cache", use_container_width=True):
            clear_all_caches()
            st.success("Cache cleared.")
        st.caption("API calls are cached for 1 hour. Composite views are cached for 5 minutes.")


def render_country_dashboard(country_key: str) -> None:
    meta = get_country_metadata(country_key)
    snapshot = get_country_snapshot(country_key)
    trend_map = {
        metric: get_indicator_series(country_key, metric)
        for metric in ("inflation", "gdp_growth", "unemployment", "interest_rate")
    }
    sentiment_tag, sentiment_copy = get_market_sentiment(country_key, snapshot)

    st.markdown(
        f"""
        <div class="country-header">
            <div>
                <div class="country-name">{meta['flag']} {meta['name']}</div>
                <div class="country-meta">{meta['region']} · {meta['income_group']}</div>
                <div class="country-meta" style="margin-top:8px;">{meta['summary_sentence']}</div>
            </div>
            <div class="as-of-text">Data as of {format_date(snapshot['as_of'][:10]) if snapshot.get('as_of') else 'N/A'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_kpi_cards(snapshot)
    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1], gap="medium")
    with left_col:
        render_trend_grid(trend_map)
    with right_col:
        st.markdown(
            f"""
            <div class="sentiment-pill">
                <span>{sentiment_tag}</span>
            </div>
            <div class="sentiment-copy">{sentiment_copy}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        render_insights_box(country_key, snapshot, sentiment_tag)

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
    render_news_section(get_all_news(country_key), st.session_state.news_category_filter)


def main() -> None:
    st.set_page_config(page_title="Macro Center V2", layout="wide", initial_sidebar_state="expanded")
    inject_global_css()
    init_state()
    render_sidebar()
    render_header()

    if st.session_state.compare_mode:
        render_compare_mode()
    else:
        render_country_dashboard(st.session_state.selected_country)

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Global GDP Map</div>', unsafe_allow_html=True)
    render_map(st.session_state.selected_country)


if __name__ == "__main__":
    main()
