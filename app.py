"""
Macro Center V3 — Institutional Macroeconomic Intelligence Platform
"""
from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

from datetime import datetime, timezone

from config import COLORS
from data.country_data import get_all_countries, get_country_metadata, compute_risks, get_regime_tag
from services.news_service import get_all_news
from services.data_cache import clear_all_caches, get_country_snapshot, get_indicator_series, get_map_dataset

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — strip any residual HTML tags from content strings
# ─────────────────────────────────────────────────────────────────────────────
import re

_STRIP_HTML = re.compile(r"<[^>]+>")

def _clean(text: str) -> str:
    """Remove HTML tags from a string, collapse whitespace."""
    if not text:
        return ""
    # Remove tags
    text = _STRIP_HTML.sub(" ", text)
    # Collapse multiple spaces / newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─────────────────────────────────────────────────────────────────────────────
# CSS — Institutional dark theme (Bloomberg / FT hybrid)
# ─────────────────────────────────────────────────────────────────────────────
def _inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap');

        :root {{
            --bg:          {COLORS["background"]};
            --surface:     {COLORS["surface"]};
            --card:        {COLORS["card_surface"]};
            --border:      {COLORS["card_border"]};
            --text:        {COLORS["text_primary"]};
            --muted:       {COLORS["text_secondary"]};
            --dim:         {COLORS["text_muted"]};
            --accent:      {COLORS["accent_blue"]};
            --accent_dim:  {COLORS["accent_dim"]};
            --positive:    {COLORS["positive_green"]};
            --negative:    {COLORS["negative_red"]};
            --amber:       {COLORS["amber"]};
            --divider:     {COLORS["divider"]};
        }}

        .stApp {{
            background-color: var(--bg);
            color: var(--text);
            font-family: "IBM Plex Sans", Inter, -apple-system, sans-serif;
        }}

        h1, h2, h3, h4 {{
            font-family: "IBM Plex Sans", Inter, sans-serif;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: var(--text);
        }}

        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--dim); border-radius: 2px; }}

        .block-container {{
            max-width: 1600px;
            padding-top: 12px;
            padding-bottom: 60px;
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background: {COLORS["surface"]};
            border-right: 1px solid var(--border);
        }}
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            color: {COLORS["text_primary"]} !important;
        }}
        [data-testid="stSidebar"] .stButton > button {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["text_primary"]} !important;
            border: 1px solid {COLORS["card_border"]} !important;
            border-radius: 3px !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            padding: 5px 10px !important;
            width: 100% !important;
            transition: border-color 0.15s, color 0.15s !important;
            text-align: left !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            border-color: {COLORS["accent_blue"]} !important;
            color: {COLORS["accent_blue"]} !important;
        }}
        [data-testid="stSidebar"] .stSelectbox > div > div {{
            background: {COLORS["card_surface"]} !important;
            border: 1px solid {COLORS["card_border"]} !important;
            border-radius: 3px !important;
        }}
        [data-testid="stSidebar"] .stToggle label {{
            color: {COLORS["text_secondary"]} !important;
            font-size: 0.75rem !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: {COLORS["divider"]} !important;
        }}
        [data-testid="stSidebar"] .stCaption {{
            color: {COLORS["text_muted"]} !important;
            font-size: 0.62rem !important;
        }}
        [data-testid="stSidebar"] .stDivider {{
            border-color: {COLORS["divider"]} !important;
        }}

        /* ── Cards ── */
        .mc-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 16px 18px;
        }}

        /* ── Section label ── */
        .sec-label {{
            font-size: 0.6rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: var(--dim);
            font-weight: 600;
            margin-bottom: 10px;
        }}

        /* ── KPI card ── */
        .kpi {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 14px 16px;
        }}
        .kpi-label {{
            font-size: 0.58rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--dim);
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1;
        }}
        .kpi-delta {{
            font-size: 0.68rem;
            font-weight: 600;
            margin-top: 5px;
        }}
        .kpi-sub {{
            font-size: 0.6rem;
            color: var(--muted);
            margin-top: 2px;
        }}

        /* ── Country header ── */
        .cname {{
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1.1;
        }}
        .cmeta {{
            font-size: 0.72rem;
            color: var(--muted);
            margin-top: 4px;
        }}
        .casof {{
            font-size: 0.62rem;
            color: var(--dim);
            text-align: right;
            line-height: 1.5;
        }}
        .ctag {{
            display: inline-block;
            font-size: 0.6rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 3px 9px;
            border-radius: 2px;
            font-weight: 600;
            margin-right: 5px;
        }}

        /* ── Risk pills ── */
        .risk-low    {{ color: {COLORS['risk_low']};    border: 1px solid {COLORS['risk_low']}44;    background: {COLORS['risk_low']}11; }}
        .risk-medium {{ color: {COLORS['risk_medium']}; border: 1px solid {COLORS['risk_medium']}44; background: {COLORS['risk_medium']}11; }}
        .risk-high   {{ color: {COLORS['risk_high']};   border: 1px solid {COLORS['risk_high']}44;   background: {COLORS['risk_high']}11; }}

        /* ── Insight rows ── */
        .ins-row {{
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin-bottom: 10px;
            font-size: 0.78rem;
            line-height: 1.5;
            color: var(--muted);
        }}
        .ins-dot {{
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: var(--accent);
            margin-top: 7px;
            flex-shrink: 0;
        }}

        /* ── News card ── */
        .news-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
            border-radius: 4px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .news-cat {{
            font-size: 0.58rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .news-src  {{
            font-size: 0.63rem;
            color: var(--muted);
            font-weight: 500;
        }}
        .news-title {{
            font-size: 0.85rem;
            font-weight: 700;
            line-height: 1.35;
            color: var(--text);
            margin: 7px 0 5px;
        }}
        .news-summary {{
            font-size: 0.73rem;
            line-height: 1.55;
            color: var(--muted);
        }}
        .news-link-btn {{
            font-size: 0.63rem;
            color: var(--accent);
            text-decoration: none;
            letter-spacing: 0.04em;
            font-weight: 600;
        }}
        .news-no-link {{
            font-size: 0.63rem;
            color: var(--dim);
            font-style: italic;
        }}
        .fresh-today {{ color: {COLORS['positive_green']}; font-weight: 600; }}
        .fresh-week  {{ color: {COLORS['amber']};          font-weight: 600; }}
        .fresh-old   {{ color: {COLORS['text_muted']}; }}

        /* ── Compare mode ── */
        .cmp-country {{ font-size: 1.15rem; font-weight: 700; margin-bottom: 2px; }}
        .cmp-meta    {{ font-size: 0.7rem;  color: var(--muted); }}
        .cmp-row     {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid var(--divider);
            font-size: 0.78rem;
        }}
        .cmp-better  {{ font-weight: 600; }}

        /* ── Spacers ── */
        .sp {{ height: 8px;  }}
        .sm {{ height: 14px; }}
        .md {{ height: 24px; }}
        .lg {{ height: 40px; }}

        /* ── Streamlit widget overrides ── */
        .stApp .stButton > button {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["accent_blue"]} !important;
            border: 1px solid {COLORS["accent_blue"]}44 !important;
            border-radius: 3px !important;
            font-size: 0.63rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
            padding: 5px 12px !important;
        }}
        .stApp .stButton > button:hover {{
            border-color: {COLORS["accent_blue"]} !important;
            background: {COLORS["accent_dim"]} !important;
        }}
        [data-testid="stHorizontalBlock"] .stButton > button {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["text_secondary"]} !important;
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 2px !important;
            font-size: 0.6rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em !important;
            padding: 3px 9px !important;
        }}
        [data-testid="stHorizontalBlock"] .stButton > button:hover {{
            border-color: {COLORS["accent_blue"]} !important;
            color: {COLORS["accent_blue"]} !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 0 !important; }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            color: {COLORS["text_secondary"]} !important;
            border-bottom: 2px solid transparent !important;
            font-size: 0.7rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
            padding: 7px 14px !important;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS["text_primary"]} !important;
            background: transparent !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS["accent_blue"]} !important;
            border-bottom-color: {COLORS["accent_blue"]} !important;
        }}
        .streamlit-expander {{
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 4px !important;
            background: {COLORS["card_surface"]} !important;
        }}
        .streamlit-expander header {{
            color: {COLORS["text_secondary"]} !important;
            font-size: 0.7rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
        }}
        .stAlert {{
            background: {COLORS["card_surface"]} !important;
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 4px !important;
        }}

        @media (max-width: 900px) {{ .topbar {{ flex-direction: column; gap: 4px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    for k, v in {
        "selected_country": "us",
        "news_filter":      None,
        "map_layer":        "gdp_value",
        "compare_mode":     False,
        "sources_open":      False,
        "fred_api_key":     "",
        "refresh_key":      0,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — compact brand + country nav
# ─────────────────────────────────────────────────────────────────────────────
def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"<div style='font-size:0.58rem;letter-spacing:0.24em;text-transform:uppercase;"
            f"color:{COLORS['accent_blue']};font-weight:700;'>Macro Intelligence</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:0.95rem;font-weight:700;color:"
            f"{COLORS['text_primary']};margin-bottom:14px;letter-spacing:-0.01em;'>"
            f"MACRO CENTER</div>",
            unsafe_allow_html=True,
        )

        countries = get_all_countries()
        idx = countries.index(st.session_state.selected_country) if st.session_state.selected_country in countries else 0
        sel = st.selectbox(
            "Country",
            countries,
            index=idx,
            format_func=lambda k: f"{get_country_metadata(k)['flag']}  {get_country_metadata(k)['name']}",
        )
        if sel != st.session_state.selected_country:
            st.session_state.selected_country = sel
            st.rerun()

        st.divider()

        st.markdown(
            f"<div class='sec-label' style='margin-bottom:8px;'>Countries</div>",
            unsafe_allow_html=True,
        )
        for ck in countries:
            meta = get_country_metadata(ck)
            if st.button(
                f"{meta['flag']}  {meta['name']}",
                key=f"sb-{ck}",
                use_container_width=True,
            ):
                st.session_state.selected_country = ck
                st.rerun()

        st.divider()

        st.markdown(
            f"<div class='sec-label' style='margin-bottom:8px;'>Settings</div>",
            unsafe_allow_html=True,
        )
        st.session_state.compare_mode = st.toggle(
            "Compare mode",
            value=st.session_state.compare_mode,
        )
        st.text_input(
            "FRED API Key",
            key="fred_api_key",
            type="password",
            placeholder="Optional — env default",
        )
        if st.button("Refresh data", use_container_width=True):
            clear_all_caches()
            st.session_state.refresh_key += 1
            st.rerun()
        if st.button("Clear cache", use_container_width=True):
            clear_all_caches()
            st.success("Cache cleared.")

        st.caption(
            f"News: {900//60}min · API: 1h · Composite: 10min",
            help="Data cached by type.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Top bar
# ─────────────────────────────────────────────────────────────────────────────
def _render_topbar(news_updated: str, data_updated: str) -> None:
    now_str = datetime.now().strftime("%H:%M · %b %d, %Y")
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:8px 0 10px;border-bottom:1px solid {COLORS['divider']};margin-bottom:18px;">
            <div>
                <div style="font-size:0.58rem;letter-spacing:0.24em;text-transform:uppercase;
                            color:{COLORS['accent_blue']};font-weight:700;margin-bottom:3px;">
                    Macroeconomic Intelligence Platform
                </div>
                <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text_primary']};letter-spacing:-0.01em;">
                    MACRO CENTER
                </div>
            </div>
            <div style="font-size:0.65rem;color:{COLORS['text_muted']};text-align:right;line-height:1.7;">
                <div>Data: {data_updated}</div>
                <div>News: {news_updated}</div>
                <div style="color:{COLORS['accent_blue']};margin-top:2px;">{now_str}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Country briefing — clean single block, no HTML artifacts
# ─────────────────────────────────────────────────────────────────────────────
def _render_briefing(country_key: str, snapshot: dict) -> None:
    meta   = get_country_metadata(country_key)
    regime = get_regime_tag(snapshot)

    regime_colors = {
        "Disinflation": COLORS["positive_green"],
        "Reflation":    COLORS["negative_red"],
        "Stagnation":   COLORS["negative_red"],
        "Policy tightening": COLORS["amber"],
        "Policy easing":     COLORS["accent_blue"],
        "Fiscal stress":     COLORS["negative_red"],
        "External vulnerability": COLORS["negative_red"],
        "Stable expansion":   COLORS["accent_blue"],
        "Overheating":       COLORS["negative_red"],
    }
    rc = regime_colors.get(regime, COLORS["text_secondary"])

    as_of_str = _clean(snapshot.get("as_of", ""))
    as_of_fmt = as_of_str[:10] if as_of_str else "N/A"

    # Clean the summary sentence — strip any HTML just in case
    summary_text = _clean(meta.get("summary_sentence", ""))

    st.markdown(
        f"""
        <div class="mc-card" style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;
                        margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid {COLORS['divider']};">
                <div>
                    <div class="cname">{meta["flag"]}  {meta["name"]}</div>
                    <div class="cmeta">{meta["region"]} · {meta["income_group"]}</div>
                </div>
                <div class="casof">
                    <div>Data as of</div>
                    <div style="color:{COLORS['text_secondary']};margin-top:2px;">{as_of_fmt}</div>
                </div>
            </div>
            <div style="display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;">
                <span class="ctag" style="color:{rc};border:1px solid {rc}44;background:{rc}11;">
                    {regime}
                </span>
                <span style="font-size:0.77rem;color:{COLORS['text_secondary']};
                             font-style:italic;font-family:'IBM Plex Serif',Georgia,serif;line-height:1.55;flex:1;">
                    {summary_text}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI strip — 10 metrics in two rows
# ─────────────────────────────────────────────────────────────────────────────
def _render_kpis(country_key: str, snapshot: dict) -> None:
    ind = snapshot

    def fmt_gdp(v):
        if v is None: return "N/A"
        if v >= 1e12: return f"${v/1e12:.2f}T"
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        return f"${v:,.0f}"

    def fmt_pct(v):
        if v is None: return "N/A"
        return f"{v:.1f}%"

    def fmt_pop(v):
        if v is None: return "N/A"
        if v >= 1e9: return f"{v/1e9:.2f}B"
        if v >= 1e6: return f"{v/1e6:.1f}M"
        return f"{v:,.0f}"

    def delta(value, higher_positive):
        if value is None or abs(value) < 0.05:
            return "", COLORS["text_muted"]
        color = COLORS["positive_green"] if (value > 0) == higher_positive else COLORS["negative_red"]
        sign  = "+" if value > 0 else ""
        return f"{sign}{value:.1f}pts", color

    cards = [
        ("GDP",            fmt_gdp(ind.get("gdp_value")),            "USD",        None),
        ("GDP Growth",     fmt_pct(ind.get("gdp_growth", 0)),       "yoy",        delta(snapshot.get("gdp_growth_delta"), True)),
        ("Inflation",     fmt_pct(ind.get("inflation", 0)),         "yoy",        delta(snapshot.get("inflation_delta"), False)),
        ("Unemployment",  fmt_pct(ind.get("unemployment", 0)),      "%",          delta(snapshot.get("unemployment_delta"), False)),
        ("Policy Rate",   fmt_pct(ind.get("interest_rate", 0)),     "%",          delta(snapshot.get("interest_rate_delta"), False)),
        ("Debt / GDP",    fmt_pct(ind.get("debt_to_gdp", 0)),       "% of GDP",   None),
        ("Curr. Account", fmt_pct(ind.get("current_account", 0)),    "% of GDP",   None),
        ("Population",   fmt_pop(ind.get("population")),            "people",     None),
        ("GDP / capita",  fmt_gdp(ind.get("gdp_per_capita")),        "USD",        None),
        ("Currency",      ind.get("currency", "N/A"),               "CCY",        None),
    ]

    for row in [cards[:5], cards[5:]]:
        cols = st.columns(5)
        for col, (label, value, unit, delta_info) in zip(cols, row):
            d_text, d_color = delta_info if delta_info else ("", COLORS["text_muted"])
            with col:
                st.markdown(
                    f"""
                    <div class="kpi">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-sub">{unit}</div>
                        <div class="kpi-delta" style="color:{d_color};">{d_text or '&nbsp;'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if row == cards[:5]:
            st.markdown("<div class='sm'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# World map — prominent section, layer toggle
# ─────────────────────────────────────────────────────────────────────────────
def _render_map(country_key: str) -> None:
    from components.country_map import render_map

    layer_labels = {"gdp_value": "GDP (USD)", "gdp_growth": "GDP Growth", "inflation": "Inflation", "interest_rate": "Policy Rate"}
    layers = list(layer_labels.keys())

    cols = st.columns(len(layers))
    for col, layer in zip(cols, layers):
        is_active = layer == st.session_state.map_layer
        label = layer_labels[layer]
        style = (
            f"background:{COLORS['accent_dim']} !important;"
            f"border-color:{COLORS['accent_blue']} !important;"
            f"color:{COLORS['accent_blue']} !important;"
            if is_active else ""
        )
        with col:
            if st.button(label, use_container_width=True, key=f"lyr-{layer}"):
                st.session_state.map_layer = layer
                st.rerun()
            if is_active:
                st.markdown(
                    f"""<style>#lyr-{layer} + div {{ display:none; }}
                       [data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {{ display:none; }}
                    </style>""",
                    unsafe_allow_html=True,
                )

    st.markdown("<div class='sp'></div>", unsafe_allow_html=True)
    render_map(country_key, layer=st.session_state.map_layer)


# ─────────────────────────────────────────────────────────────────────────────
# Trend charts
# ─────────────────────────────────────────────────────────────────────────────
def _render_trends(country_key: str) -> None:
    from components.chart_panel import render_trend_grid

    st.markdown(
        f"<div class='sec-label' style='margin-bottom:10px;'>Macroeconomic Trends</div>",
        unsafe_allow_html=True,
    )
    trend_map = {m: get_indicator_series(country_key, m) for m in ("inflation", "gdp_growth", "unemployment", "interest_rate")}
    render_trend_grid(trend_map)


# ─────────────────────────────────────────────────────────────────────────────
# News feed — clean rendering, no HTML artifacts
# ─────────────────────────────────────────────────────────────────────────────
def _render_news(news_items: list[dict], fetched_at: str, filter_cat: str) -> None:
    from config import NEWS_CATEGORY_LABELS, NEWS_CATEGORIES

    all_opts   = [None] + NEWS_CATEGORIES
    all_labels = ["All"] + [NEWS_CATEGORY_LABELS.get(c, c.title()) for c in NEWS_CATEGORIES]

    cols = st.columns(len(all_opts))
    for col, opt, lbl in zip(cols, all_opts, all_labels):
        active = opt == filter_cat or (opt is None and filter_cat is None)
        if col.button(
            lbl,
            use_container_width=True,
            key=f"nc-{lbl[:8]}",
        ):
            st.session_state.news_filter = opt

    st.markdown("<div class='sp'></div>", unsafe_allow_html=True)

    active = [n for n in news_items if not filter_cat or n.get("category") == filter_cat]

    if not active:
        st.info("No news for this filter.")
        return

    left_col, right_col = st.columns(2, gap="medium")
    for idx, item in enumerate(active):
        target = left_col if idx % 2 == 0 else right_col
        _render_news_card(item, target, idx)


def _render_news_card(item: dict, col, idx: int) -> None:
    """Render a single news card — all content is clean text, no HTML comment artifacts."""
    cat    = _clean(item.get("category", ""))
    accent = {
        "inflation": "#c0524a", "growth": "#4a7fc1", "central_bank": "#b8943c",
        "fiscal": "#6a9e6e", "trade": "#8a6ab5", "geopolitics": "#b07848",
        "labor": "#4a8a9e", "markets": "#5a7a9e", "sovereign_risk": "#b84d44",
    }.get(cat, COLORS["text_secondary"])

    # Clean all text content — remove any HTML tags that might be embedded
    headline = _clean(item.get("headline", ""))
    summary  = _clean(item.get("summary", ""))
    source   = _clean(item.get("source", "Source unavailable"))
    date_str = item.get("date", "")
    url      = item.get("url", "")

    # Freshness
    if date_str:
        try:
            d = datetime.fromisoformat(date_str[:10]).date()
            from datetime import date as date_type
            delta = (date_type.today() - d).days
            if delta == 0:      fresh_lbl, fresh_cls = "Live today", "fresh-today"
            elif delta == 1:    fresh_lbl, fresh_cls = "Last 24h", "fresh-week"
            elif delta < 7:     fresh_lbl, fresh_cls = f"This week", "fresh-week"
            else:               fresh_lbl, fresh_cls = f"{delta}d ago", "fresh-old"
            date_disp = datetime.fromisoformat(date_str[:10]).strftime("%b %d, %Y")
        except Exception:
            fresh_lbl, fresh_cls = "Unknown", "fresh-old"
            date_disp = date_str[:10]
    else:
        fresh_lbl, fresh_cls = "Unknown", "fresh-old"
        date_disp = "N/A"

    with col:
        st.markdown(
            f"""
            <div class="news-card" style="border-left-color:{accent};">
                <div style="display:flex;align-items:center;gap:5px;margin-bottom:9px;flex-wrap:wrap;">
                    <span class="news-cat" style="color:{accent};">{cat.replace('_',' ').title()}</span>
                    <span style="color:{COLORS['text_muted']};font-size:0.6rem;">·</span>
                    <span class="news-src">{source}</span>
                    <span style="color:{COLORS['text_muted']};font-size:0.6rem;margin-left:auto;">{date_disp}</span>
                </div>
                <div class="news-title">{headline}</div>
                <div class="news-summary" style="margin-bottom:10px;">{summary}</div>
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span class="{fresh_cls}" style="font-size:0.62rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;">
                        ● {fresh_lbl}
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


# ─────────────────────────────────────────────────────────────────────────────
# Risk panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_risk(country_key: str, snapshot: dict) -> None:
    from config import RISK_LABELS
    risks = compute_risks(snapshot)
    risk_colors = {
        "low": COLORS["risk_low"],
        "medium": COLORS["risk_medium"],
        "high": COLORS["risk_high"],
    }
    st.markdown(
        f"<div class='sec-label' style='margin-bottom:10px;'>Country Risk Assessment</div>",
        unsafe_allow_html=True,
    )
    items = list(risks.items())
    for i in range(0, len(items), 3):
        row_items = items[i:i+3]
        cols = st.columns(3)
        for col, (risk_key, level) in zip(cols, row_items):
            color = risk_colors.get(level, COLORS["text_secondary"])
            label = RISK_LABELS.get(risk_key, risk_key)
            with col:
                st.markdown(
                    f"""
                    <div class="mc-card" style="padding:12px 14px;text-align:center;">
                        <div class="ctag risk-{level}">{level.upper()}</div>
                        <div style="font-size:0.8rem;font-weight:600;color:{COLORS['text_primary']};margin-top:5px;">
                            {label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if i + 3 < len(items):
            st.markdown("<div class='sp'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# What Matters Now — analytical bullets
# ─────────────────────────────────────────────────────────────────────────────
def _render_insights(country_key: str, snapshot: dict, regime: str) -> None:
    from config import SENTIMENT_TAGS

    ind  = snapshot
    inf  = ind.get("inflation", 0)
    grow = ind.get("gdp_growth", 0)
    unem = ind.get("unemployment", 0)
    rate = ind.get("interest_rate", 0)
    d    = ind.get("interest_rate_delta", 0)
    debt = ind.get("debt_to_gdp", 0)
    ca   = ind.get("current_account", 0)

    bullets = []

    if inf > 5.0 and grow < 1.5:
        bullets.append(
            f"Inflation at {inf:.1f}% coexists with sub-trend growth ({grow:.1f}%), "
            "a stagflationary mix that severely constrains the central bank's options."
        )
    elif inf > 4.0:
        bullets.append(
            f"At {inf:.1f}%, inflation is still materially above the central bank's target. "
            "Services prices — particularly wages — remain the primary residual risk."
        )
    elif inf < 2.0:
        bullets.append(
            f"Inflation at {inf:.1f}% gives the central bank room to ease, "
            "but the pace of normalisation will depend on the growth outlook."
        )
    else:
        bullets.append(
            f"Inflation at {inf:.1f}% is close to target. The focus shifts to "
            "sustaining that progress without premature loosening."
        )

    if d >= 0.25:
        bullets.append(
            f"Rates held or raised ({d:+.1f}pts), maintaining a restrictive posture. "
            "Transmission to demand is underway with a 12–18 month lag."
        )
    elif d <= -0.25:
        bullets.append(
            f"Rate cuts of {d:+.1f}pts are in train. Easing should support activity through the year, "
            "though credit conditions remain tight for now."
        )

    if unem <= 4.0:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals a tight labour market. "
            "Wage growth is likely to stay elevated, keeping services inflation sticky."
        )
    elif unem >= 6.5:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals growing labour slack. "
            "This should ease wage and services price pressures over time."
        )

    if grow >= 4.0:
        bullets.append(
            f"Growth of {grow:.1f}% is above trend for a developed economy, "
            "reinforcing a higher-for-longer policy backdrop."
        )
    elif grow < 0.5:
        bullets.append(
            f"Growth of {grow:.1f}% signals significant economic slack. "
            "The risk of a more pronounced downturn is elevated."
        )

    if debt >= 100 and ca < -3:
        bullets.append(
            f"Sovereign finances are under pressure: debt at {debt:.0f}% of GDP with a "
            f"current account deficit of {ca:.1f}% creates external vulnerability."
        )
    elif debt >= 100:
        bullets.append(
            f"Debt at {debt:.0f}% of GDP is a long-term constraint on fiscal flexibility. "
            "Debt servicing costs will remain elevated even if rates fall."
        )

    bullets.append(
        f"Current regime: <strong>{regime}</strong>. "
        f"{SENTIMENT_TAGS.get(regime, 'The macro backdrop remains fluid.')}"
    )

    st.markdown(
        f"""
        <div class="mc-card">
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


# ─────────────────────────────────────────────────────────────────────────────
# Compare mode
# ─────────────────────────────────────────────────────────────────────────────
def _render_compare() -> None:
    from components.compare_mode import render_compare_mode
    render_compare_mode()


# ─────────────────────────────────────────────────────────────────────────────
# Data sources expander
# ─────────────────────────────────────────────────────────────────────────────
def _render_sources() -> None:
    from config import CACHE_TTL
    with st.expander("Data sources & methodology", expanded=False):
        st.markdown(
            f"""
            <div style="font-size:0.76rem;color:{COLORS['text_secondary']};line-height:1.65;">
            <strong style="color:{COLORS['text_primary']};">Indicator data</strong><br>
            Primary: World Bank Open Data API — all non-US series.<br>
            US indicators: Federal Reserve Economic Data (FRED) API — requires free API key.<br>
            Fallback: curated static estimates from IMF World Economic Outlook when APIs are unavailable.<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">News data</strong><br>
            Live: FT, CNBC, MarketWatch, WSJ, BBC Business RSS feeds.<br>
            Fallback: curated macro summaries when all RSS sources fail.<br>
            Articles without a valid source URL are labelled "Source unavailable".<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">Cache strategy</strong><br>
            World Bank / FRED: {CACHE_TTL['api']//3600}h · Derived snapshots: {CACHE_TTL['composite']//60}min · Map: {CACHE_TTL['map']//60}min · News: {CACHE_TTL['news']//60}min<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">Risk thresholds</strong><br>
            Inflation Risk: low &lt;2.5%, medium &lt;4.0%, high ≥4.0% · Fiscal Risk: low &lt;50%, medium &lt;80%, high ≥80% of GDP<br>
            External Risk: low &gt;-3%, medium &gt;-5%, high ≤-5% · Growth Momentum: low &lt;1%, medium &lt;2.5%, high ≥2.5%<br>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Macro Center",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_css()
    _init_state()
    _render_sidebar()

    news_items, news_fetched = get_all_news(st.session_state.selected_country)
    snapshot     = get_country_snapshot(st.session_state.selected_country)
    data_as_of   = _clean(snapshot.get("as_of", ""))[:16] or "N/A"
    regime       = get_regime_tag(snapshot)

    _render_topbar(news_fetched, data_as_of)

    if st.session_state.compare_mode:
        _render_compare()
    else:
        country_key = st.session_state.selected_country

        # 1. Country briefing
        _render_briefing(country_key, snapshot)

        # 2. KPI strip
        st.markdown("<div class='sm'></div>", unsafe_allow_html=True)
        _render_kpis(country_key, snapshot)

        # 3. Map — prominent section
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='sec-label' style='margin-bottom:8px;'>Global Macro Map — click a country to navigate</div>",
            unsafe_allow_html=True,
        )
        _render_map(country_key)

        # 4. Trends + Risk
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        trend_col, risk_col = st.columns([2.0, 1.0], gap="large")
        with trend_col:
            _render_trends(country_key)
        with risk_col:
            _render_risk(country_key, snapshot)

        # 5. Insights + News
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        insight_col, news_col = st.columns([1.2, 2.0], gap="large")
        with insight_col:
            _render_insights(country_key, snapshot, regime)
        with news_col:
            st.markdown(
                f"<div class='sec-label' style='margin-bottom:10px;'>Macro News Flow</div>",
                unsafe_allow_html=True,
            )
            _render_news(news_items, news_fetched, st.session_state.news_filter)

    st.markdown("<div class='md'></div>", unsafe_allow_html=True)
    _render_sources()
    st.markdown("<div class='lg'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
