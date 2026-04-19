from __future__ import annotations

import html
import re
from datetime import datetime
from urllib.parse import urlparse

import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

from config import COLORS, MAP_LAYER_LABELS, NEWS_CATEGORIES, NEWS_CATEGORY_LABELS, RISK_LABELS, SENTIMENT_TAGS
from data.country_data import compute_risks, get_all_countries, get_country_metadata, get_regime_tag
from services.data_cache import clear_all_caches, get_country_snapshot, get_indicator_series
from services.news_service import get_all_news
from utils.formatters import format_currency, format_date, format_number, format_percent, truncate

load_dotenv()

st.set_page_config(
    page_title="Macro Center",
    page_icon="MC",
    layout="wide",
    initial_sidebar_state="expanded",
)

_HTML_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAGS = re.compile(r"<[^>]+>")
_HTML_ENTITIES = re.compile(r"&[a-zA-Z#0-9]+;")
_MULTISPACE = re.compile(r"\s+")


def sanitize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    text = _HTML_COMMENTS.sub(" ", text)
    text = _HTML_TAGS.sub(" ", text)
    text = html.unescape(text)
    text = _HTML_ENTITIES.sub(" ", text)
    return _MULTISPACE.sub(" ", text).strip()


def normalize_url(value: object) -> str:
    text = sanitize_text(value)
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = parsed.netloc.lower()
    blocked_tokens = {
        "abc123", "xyz789", "def456", "content/china-", "content/uk-", "content/france-",
        "content/germany-", "content/japan-", "content/india-", "content/brazil-",
        "content/australia-", "content/canada-", "content/us-", "articles/canada-",
        "articles/uk-", "articles/germany-", "articles/china-", "articles/japan-",
        "articles/india-", "articles/brazil-", "articles/australia-", "articles/france-",
    }
    lowered = text.lower()
    if any(token in lowered for token in blocked_tokens):
        return ""
    return text


def section_label(text: str) -> None:
    st.caption(sanitize_text(text).upper())


def vertical_space(lines: int = 1) -> None:
    for _ in range(lines):
        st.write("")


def inject_styles() -> None:
    st.html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:wght@400;600&display=swap');

        :root {{
            --bg: {COLORS["background"]};
            --surface: {COLORS["surface"]};
            --card: {COLORS["card_surface"]};
            --border: {COLORS["card_border"]};
            --text: {COLORS["text_primary"]};
            --muted: {COLORS["text_secondary"]};
            --dim: {COLORS["text_muted"]};
            --accent: {COLORS["accent_blue"]};
            --positive: {COLORS["positive_green"]};
            --negative: {COLORS["negative_red"]};
            --amber: {COLORS["amber"]};
        }}

        .stApp {{
            background:
                linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0)),
                radial-gradient(circle at top left, rgba(74,127,193,0.10), transparent 26%),
                var(--bg);
            color: var(--text);
            font-family: "IBM Plex Sans", sans-serif;
        }}

        [data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0)),
                var(--surface);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] .stRadio label,
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stToggle label,
        [data-testid="stSidebar"] .stTextInput label {{
            color: var(--muted) !important;
            font-size: 0.72rem !important;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .stApp h1, .stApp h2, .stApp h3 {{
            color: var(--text);
            font-family: "IBM Plex Sans", sans-serif;
            letter-spacing: -0.01em;
        }}

        .stMarkdown, .stText, .stCaption, p, li {{
            color: var(--text);
        }}

        [data-testid="stMetric"] {{
            background: rgba(24,27,38,0.88);
            border: 1px solid var(--border);
            padding: 0.85rem 0.9rem;
            border-radius: 6px;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--dim);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.58rem;
            font-weight: 600;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--text);
            font-size: 1.18rem;
            font-weight: 700;
        }}

        [data-testid="stMetricDelta"] {{
            font-size: 0.68rem;
            font-weight: 600;
        }}

        .stButton > button, .stDownloadButton > button {{
            border-radius: 4px !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(24,27,38,0.9) !important;
            color: var(--text) !important;
            font-size: 0.72rem !important;
        }}

        .stRadio [role="radiogroup"] {{
            gap: 0.35rem;
        }}

        .stRadio [role="radio"] {{
            background: rgba(24,27,38,0.82);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 4px;
            padding: 0.35rem 0.65rem;
        }}

        .stRadio [aria-checked="true"] {{
            border-color: var(--accent);
            box-shadow: inset 0 -2px 0 var(--accent);
        }}

        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: rgba(24,27,38,0.86);
            border: 1px solid rgba(255,255,255,0.08);
        }}

        .stLinkButton a {{
            color: var(--accent) !important;
            border: 1px solid rgba(74,127,193,0.35) !important;
            background: rgba(74,127,193,0.08) !important;
            border-radius: 4px !important;
        }}

        .stAlert {{
            background: rgba(24,27,38,0.88) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}
        </style>
        """
    )


def init_state() -> None:
    defaults = {
        "selected_country": "us",
        "map_layer": "gdp_value",
        "news_filter": "All",
        "compare_mode": False,
        "fred_api_key": "",
        "refresh_key": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def render_sidebar() -> None:
    with st.sidebar:
        section_label("Platform")
        st.subheader("Macro Center", anchor=False)
        st.caption("Institutional macro intelligence")

        countries = get_all_countries()
        labels = {
            key: f"{get_country_metadata(key)['flag']}  {sanitize_text(get_country_metadata(key)['name'])}"
            for key in countries
        }
        selected = st.selectbox(
            "Coverage Universe",
            countries,
            index=countries.index(st.session_state.selected_country),
            format_func=lambda key: labels[key],
        )
        if selected != st.session_state.selected_country:
            st.session_state.selected_country = selected
            st.rerun()

        section_label("Navigation")
        chosen = st.radio(
            "Country Navigation",
            countries,
            index=countries.index(st.session_state.selected_country),
            format_func=lambda key: labels[key],
            label_visibility="collapsed",
        )
        if chosen != st.session_state.selected_country:
            st.session_state.selected_country = chosen
            st.rerun()

        section_label("Workspace")
        st.session_state.compare_mode = st.toggle("Compare Mode", value=st.session_state.compare_mode)
        st.text_input(
            "FRED API Key",
            key="fred_api_key",
            type="password",
            placeholder="Optional override",
        )
        if st.button("Refresh Data", use_container_width=True):
            clear_all_caches()
            st.session_state.refresh_key += 1
            st.rerun()
        if st.button("Clear Cache", use_container_width=True):
            clear_all_caches()
            st.success("Cache cleared.")

        section_label("Cadence")
        st.caption("APIs refresh hourly. News refreshes every 15 minutes. Composite snapshots refresh every 10 minutes.")


def render_top_bar(news_updated: str, data_updated: str) -> None:
    left, right = st.columns([3.6, 1.4], vertical_alignment="center")
    with left:
        section_label("Global Macro Monitor")
        st.title("Macro Center", anchor=False)
        st.caption("A country-by-country analytical briefing environment for rates, inflation, growth, and sovereign conditions.")
    with right:
        with st.container(border=True):
            st.caption("Terminal Clock")
            st.text(datetime.now().strftime("%H:%M %Z"))
            st.caption(f"Data as of {sanitize_text(data_updated)}")
            st.caption(f"News as of {sanitize_text(news_updated)}")


def regime_tone(regime: str) -> str:
    tones = {
        "Disinflation": "Progress on prices, but policy remains cautious.",
        "Reflation": "Price pressures are re-emerging and may challenge easing expectations.",
        "Stagnation": "Demand is weak and the policy trade-off is deteriorating.",
        "Policy tightening": "Restrictive settings are still feeding through to demand and credit.",
        "Policy easing": "The cycle is turning, but transmission remains gradual.",
        "Fiscal stress": "Fiscal credibility is the binding constraint on the macro outlook.",
        "External vulnerability": "Funding and trade channels remain the principal transmission risk.",
        "Stable expansion": "Activity is resilient and inflation is broadly manageable.",
        "Overheating": "Demand is outrunning supply and inflation persistence is the main concern.",
    }
    return tones.get(regime, "The macro backdrop remains fluid.")


def render_country_briefing(country_key: str, snapshot: dict) -> str:
    meta = get_country_metadata(country_key)
    regime = sanitize_text(get_regime_tag(snapshot))
    summary = sanitize_text(meta.get("summary_sentence"))
    data_as_of = format_date(snapshot.get("as_of", ""))

    left, right = st.columns([3.2, 1.1], gap="large")
    with left:
        with st.container(border=True):
            section_label("Selected Country")
            st.subheader(f"{meta['flag']} {sanitize_text(meta['name'])}", anchor=False)
            st.caption(
                f"{sanitize_text(meta['region'])}  |  {sanitize_text(meta['income_group'])}  |  Data as of {data_as_of}"
            )
            st.text(f"Regime: {regime}")
            st.write(summary)
            st.caption(regime_tone(regime))
    with right:
        with st.container(border=True):
            section_label("Briefing Frame")
            st.text("Region")
            st.caption(sanitize_text(meta["region"]))
            st.text("Income Group")
            st.caption(sanitize_text(meta["income_group"]))
            st.text("Macro Regime")
            st.caption(regime)
            st.text("Data As Of")
            st.caption(data_as_of)
    return regime


def kpi_delta(snapshot: dict, key: str, inverse: bool = False) -> str | None:
    raw = snapshot.get(f"{key}_delta")
    if raw is None or abs(raw) < 0.05:
        return "Flat"
    display = f"{raw:+.1f} pts"
    if inverse:
        return f"{display} vs prior"
    return display


def render_kpi_strip(snapshot: dict) -> None:
    section_label("Key Indicators")
    metrics = [
        ("GDP", format_currency(snapshot.get("gdp_value")), None),
        ("GDP Growth", format_percent(snapshot.get("gdp_growth")), kpi_delta(snapshot, "gdp_growth")),
        ("Inflation", format_percent(snapshot.get("inflation")), kpi_delta(snapshot, "inflation", inverse=True)),
        ("Unemployment", format_percent(snapshot.get("unemployment")), kpi_delta(snapshot, "unemployment", inverse=True)),
        ("Policy Rate", format_percent(snapshot.get("interest_rate")), kpi_delta(snapshot, "interest_rate", inverse=True)),
        ("Debt / GDP", format_percent(snapshot.get("debt_to_gdp")), None),
        ("Current Account", format_percent(snapshot.get("current_account")), None),
        ("Population", format_number(snapshot.get("population", 0) / 1_000_000, 1) + "M" if snapshot.get("population") else "N/A", None),
    ]
    cols = st.columns(len(metrics))
    for col, (label, value, delta_value) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value, delta=delta_value, border=True)
    st.caption("Primary series sourced from FRED and the World Bank, with controlled fallback estimates where live series are unavailable.")


def render_map_section(country_key: str) -> None:
    from components.country_map import render_map

    with st.container(border=True):
        top_left, top_right = st.columns([4, 2], vertical_alignment="center")
        with top_left:
            section_label("Global Map")
            st.subheader("Cross-Country Macro Map", anchor=False)
            st.caption("Switch the active layer to compare the selected country against the wider macro universe.")
        with top_right:
            layer_options = list(MAP_LAYER_LABELS.keys())
            current_idx = layer_options.index(st.session_state.map_layer)
            choice = st.radio(
                "Map Layer",
                layer_options,
                index=current_idx,
                format_func=lambda key: MAP_LAYER_LABELS[key],
                horizontal=True,
                label_visibility="collapsed",
            )
            if choice != st.session_state.map_layer:
                st.session_state.map_layer = choice
                st.rerun()
        render_map(country_key, layer=st.session_state.map_layer)
        st.caption("Hover to inspect country metrics. Sidebar selection remains the authoritative country switch.")


def render_trends(country_key: str) -> None:
    from components.chart_panel import render_trend_grid

    section_label("Trend Analysis")
    trend_map = {
        metric: get_indicator_series(country_key, metric)
        for metric in ("gdp_growth", "inflation", "unemployment", "interest_rate")
    }
    render_trend_grid(trend_map)


def build_what_matters(snapshot: dict, regime: str, country_key: str) -> list[str]:
    meta = get_country_metadata(country_key)
    inflation = snapshot.get("inflation", 0.0)
    growth = snapshot.get("gdp_growth", 0.0)
    unemployment = snapshot.get("unemployment", 0.0)
    policy = snapshot.get("interest_rate", 0.0)
    debt = snapshot.get("debt_to_gdp", 0.0)
    current_account = snapshot.get("current_account", 0.0)

    bullets: list[str] = []
    if inflation >= 4.0 and growth <= 1.5:
        bullets.append(f"Inflation at {inflation:.1f}% remains elevated while growth at {growth:.1f}% is already running below trend. The policy mix is restrictive and politically difficult.")
    elif inflation < 2.5:
        bullets.append(f"Inflation at {inflation:.1f}% is close to target. The focus shifts from emergency tightening to the durability of disinflation.")
    else:
        bullets.append(f"Inflation at {inflation:.1f}% is moderating, but price persistence still limits how quickly policymakers can turn dovish.")

    if unemployment <= 4.0:
        bullets.append(f"Unemployment at {unemployment:.1f}% signals a tight labour market. Services inflation and wage resilience remain relevant risks.")
    elif unemployment >= 6.5:
        bullets.append(f"Unemployment at {unemployment:.1f}% points to slack in the labour market, which should gradually ease domestic price pressure.")

    bullets.append(f"Policy rates at {policy:.1f}% continue to set the tone for financing conditions, credit creation, and fiscal servicing costs.")

    if debt >= 100:
        bullets.append(f"Debt at {debt:.0f}% of GDP constrains discretionary fiscal support and keeps sovereign credibility under scrutiny.")
    if current_account <= -3:
        bullets.append(f"A current-account balance of {current_account:.1f}% of GDP leaves {sanitize_text(meta['name'])} more exposed to external funding and currency shocks.")

    bullets.append(f"Current regime: {regime}. {sanitize_text(SENTIMENT_TAGS.get(regime, 'The macro backdrop remains fluid.'))}")
    return bullets[:5]


def render_risk_and_regime(country_key: str, snapshot: dict, regime: str) -> None:
    risk_col, brief_col = st.columns([1.5, 2], gap="large")
    with risk_col:
        with st.container(border=True):
            section_label("Risk Matrix")
            st.subheader("Risk / Regime", anchor=False)
            risks = compute_risks(snapshot)
            for key, level in risks.items():
                st.text(f"{sanitize_text(RISK_LABELS.get(key, key))}: {level.upper()}")
                st.caption(
                    {
                        "low": "Contained",
                        "medium": "Watch closely",
                        "high": "Material pressure",
                    }.get(level, "Under review")
                )
    with brief_col:
        with st.container(border=True):
            section_label("What Matters Now")
            st.subheader("Analyst Brief", anchor=False)
            for bullet in build_what_matters(snapshot, regime, country_key):
                st.write(f"- {sanitize_text(bullet)}")


def render_news_feed(news_items: list[dict]) -> None:
    section_label("Macro News")
    control_left, control_right = st.columns([4, 1], vertical_alignment="center")
    with control_left:
        options = ["All"] + [NEWS_CATEGORY_LABELS.get(category, category.title()) for category in NEWS_CATEGORIES]
        selected_label = st.radio(
            "News Category",
            options,
            index=options.index(st.session_state.news_filter) if st.session_state.news_filter in options else 0,
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state.news_filter = selected_label
    with control_right:
        st.caption(f"{len(news_items)} stories loaded")

    label_to_key = {NEWS_CATEGORY_LABELS.get(category, category.title()): category for category in NEWS_CATEGORIES}
    active_key = label_to_key.get(st.session_state.news_filter)
    filtered = [
        item for item in news_items
        if not active_key or sanitize_text(item.get("category")) == active_key
    ]

    if not filtered:
        st.info("No stories available for the current category filter.")
        return

    left, right = st.columns(2, gap="large")
    for index, item in enumerate(filtered):
        target = left if index % 2 == 0 else right
        with target:
            render_news_card(item)


def freshness_label(date_str: str) -> str:
    try:
        delta = (datetime.now().date() - datetime.fromisoformat(date_str[:10]).date()).days
    except Exception:
        return "Undated"
    if delta <= 0:
        return "Fresh today"
    if delta == 1:
        return "Last 24h"
    if delta < 7:
        return "This week"
    return f"{delta}d old"


def render_news_card(item: dict) -> None:
    category_key = sanitize_text(item.get("category"))
    headline = sanitize_text(item.get("headline"))
    summary = sanitize_text(item.get("summary"))
    source = sanitize_text(item.get("source") or "Source unavailable")
    url = normalize_url(item.get("url"))
    date_str = sanitize_text(item.get("date"))
    date_label = format_date(date_str)
    category_label = NEWS_CATEGORY_LABELS.get(category_key, category_key.replace("_", " ").title())

    with st.container(border=True):
        top_left, top_right = st.columns([3, 1], vertical_alignment="top")
        with top_left:
            st.caption(f"{category_label}  |  {source}")
        with top_right:
            st.caption(f"{date_label}  |  {freshness_label(date_str)}")
        st.subheader(truncate(headline, 110), anchor=False)
        st.caption(truncate(summary, 240))
        if url:
            st.link_button("Open Story", url, use_container_width=False)
        else:
            st.caption("Verified link unavailable.")


def render_sources(snapshot: dict, news_updated: str) -> None:
    with st.container(border=True):
        section_label("Methodology")
        st.subheader("Sources and Construction", anchor=False)
        st.write("Country snapshots combine current metadata with live FRED and World Bank series where available.")
        st.write("Risk labels are rule-based classifications derived from inflation, debt, external balance, growth momentum, and policy stance.")
        st.write("News is sourced from live RSS feeds first. Fallback items are allowed only when their text is clean and their links pass validation.")
        st.caption(f"Snapshot as of {format_date(snapshot.get('as_of', ''))}. News cache refreshed {sanitize_text(news_updated)}.")


def render_main_view() -> None:
    country_key = st.session_state.selected_country
    snapshot = get_country_snapshot(country_key)
    news_items, news_updated = get_all_news(country_key)
    data_updated = format_date(snapshot.get("as_of", ""))

    render_top_bar(news_updated, data_updated)
    regime = render_country_briefing(country_key, snapshot)
    vertical_space()
    render_kpi_strip(snapshot)
    vertical_space()
    render_map_section(country_key)
    vertical_space()
    render_trends(country_key)
    vertical_space()
    render_risk_and_regime(country_key, snapshot, regime)
    vertical_space()
    render_news_feed(news_items)
    vertical_space()
    render_sources(snapshot, news_updated)


def main() -> None:
    inject_styles()
    init_state()
    render_sidebar()
    if st.session_state.compare_mode:
        from components.compare_mode import render_compare_mode

        render_compare_mode()
        return
    render_main_view()


if __name__ == "__main__":
    main()
