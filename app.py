"""
Macro Center — main application entry point.
Full page structure:
  1. Compact header bar
  2. Main interactive world map (central)
  3. Selected country overview panel
  4. Key macro indicators
  5. Trend charts
  6. Macro news flow
  7. Country risk summary
  8. Collapsible source panel
"""
from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

from datetime import datetime, timezone

from config import COLORS, CACHE_TTL
from data.country_data import get_all_countries, get_country_metadata, compute_risks, get_regime_tag
from services.news_service import get_all_news
from services.data_cache import (
    clear_all_caches,
    get_country_snapshot,
    get_indicator_series,
    get_map_dataset,
)

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# CSS — institutional dark theme
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

        .stApp {{ background-color: var(--bg); color: var(--text);
                  font-family: "IBM Plex Sans", Inter, -apple-system, sans-serif; }}

        /* Typography */
        h1,h2,h3,h4 {{ font-family: "IBM Plex Sans",Inter,sans-serif;
                       font-weight: 700; letter-spacing: -0.01em; color: var(--text); }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--dim); border-radius: 2px; }}

        /* Layout */
        .block-container {{ max-width: 1600px; padding-top: 16px; padding-bottom: 60px; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{ background: {COLORS["surface"]};
                                    border-right: 1px solid var(--border); }}
        [data-testid="stSidebar"] .stMarkdown {{ color: var(--text); }}

        /* Sidebar buttons — institutional */
        [data-testid="stSidebar"] .stButton > button {{ 
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["text_primary"]} !important;
            border: 1px solid {COLORS["card_border"]} !important;
            border-radius: 3px !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            padding: 6px 12px !important;
            width: 100% !important;
            transition: border-color 0.15s, color 0.15s !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{ 
            border-color: {COLORS["accent_blue"]} !important;
            color: {COLORS["accent_blue"]} !important;
        }}

        /* Sidebar selectbox */
        [data-testid="stSidebar"] .stSelectbox > div > div {{ 
            background: {COLORS["card_surface"]} !important;
            border: 1px solid {COLORS["card_border"]} !important;
            border-radius: 3px !important;
        }}
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {{
            background: {COLORS["card_surface"]} !important;
        }}
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {{
            background: {COLORS["card_surface"]} !important;
            border-color: {COLORS["card_border"]} !important;
        }}

        /* Sidebar toggle */
        [data-testid="stSidebar"] .stToggle label {{ color: {COLORS["text_secondary"]} !important; }}
        
        /* Sidebar divider */
        [data-testid="stSidebar"] hr {{ border-color: {COLORS["divider"]} !important; }}

        /* Sidebar caption */
        [data-testid="stSidebar"] .stCaption {{ color: {COLORS["text_muted"]} !important; }}

        /* Cards */
        .mc-card {{ background: var(--card); border: 1px solid var(--border);
                    border-radius: 4px; padding: 18px 20px; }}

        /* Top bar */
        .topbar {{ display:flex; align-items:center; justify-content:space-between;
                   padding: 10px 0 10px; border-bottom: 1px solid var(--divider);
                   margin-bottom: 20px; }}
        .topbar-brand {{ font-size: 0.62rem; letter-spacing: 0.22em; text-transform: uppercase;
                         color: var(--accent); font-weight: 700; }}
        .topbar-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text);
                         letter-spacing: -0.01em; }}
        .topbar-meta {{ font-size: 0.68rem; color: var(--dim); text-align: right; line-height: 1.5; }}

        /* Section label */
        .sec-label {{ font-size: 0.62rem; letter-spacing: 0.2em; text-transform: uppercase;
                      color: var(--dim); font-weight: 600; margin-bottom: 10px; }}

        /* KPI cards */
        .kpi {{ background: var(--card); border: 1px solid var(--border); border-radius: 4px;
                padding: 16px 18px; }}
        .kpi-label {{ font-size: 0.6rem; letter-spacing: 0.12em; text-transform: uppercase;
                       color: var(--dim); font-weight: 600; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1; }}
        .kpi-delta {{ font-size: 0.72rem; font-weight: 600; margin-top: 7px; }}
        .kpi-sub   {{ font-size: 0.62rem; color: var(--muted); margin-top: 3px; }}

        /* Country header */
        .cname {{ font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1.1; }}
        .cmeta {{ font-size: 0.75rem; color: var(--muted); margin-top: 4px; }}
        .casof  {{ font-size: 0.65rem; color: var(--dim); text-align: right; }}
        .ctag   {{ display:inline-block; font-size:0.62rem; letter-spacing:0.1em; text-transform:uppercase;
                   padding:4px 10px; border-radius:2px; font-weight:600; margin-right:6px; }}

        /* Risk pills */
        .risk-low    {{ color: {COLORS['risk_low']};    border: 1px solid {COLORS['risk_low']}44;
                        background: {COLORS['risk_low']}11; }}
        .risk-medium {{ color: {COLORS['risk_medium']}; border: 1px solid {COLORS['risk_medium']}44;
                        background: {COLORS['risk_medium']}11; }}
        .risk-high   {{ color: {COLORS['risk_high']};   border: 1px solid {COLORS['risk_high']}44;
                        background: {COLORS['risk_high']}11; }}

        /* Insight row */
        .ins-row {{ display:flex; gap:10px; align-items:flex-start; margin-bottom:10px;
                    font-size:0.8rem; line-height:1.5; color: var(--muted); }}
        .ins-dot  {{ width:4px; height:4px; border-radius:50%; background:var(--accent);
                     margin-top:7px; flex-shrink:0; }}

        /* News card */
        .news-card {{ background:var(--card); border:1px solid var(--border);
                      border-left:3px solid var(--accent); border-radius:4px;
                      padding:16px 18px; margin-bottom:12px; }}
        .news-cat {{ font-size:0.6rem; letter-spacing:0.1em; text-transform:uppercase;
                     font-weight:600; }}
        .news-src  {{ font-size:0.65rem; color:var(--muted); font-weight:500; }}
        .news-fresh{{ font-size:0.62rem; color:var(--dim); margin-left:auto; }}
        .news-title{{ font-size:0.88rem; font-weight:700; line-height:1.35; color:var(--text);
                      margin:8px 0 6px; }}
        .news-summary{{ font-size:0.75rem; line-height:1.55; color:var(--muted); }}
        .news-link-btn {{ font-size:0.65rem; color:var(--accent); text-decoration:none;
                          letter-spacing:0.04em; font-weight:600; }}
        .news-no-link  {{ font-size:0.65rem; color:var(--dim); font-style:italic; }}

        /* Freshness badge colours */
        .fresh-today   {{ color:{COLORS['positive_green']}; font-weight:600; }}
        .fresh-week    {{ color:{COLORS['amber']};           font-weight:600; }}
        .fresh-old     {{ color:{COLORS['text_muted']}; }}

        /* Spacers */
        .sp {{ height:10px; }}
        .sm {{ height:18px; }}
        .md {{ height:28px; }}
        .lg {{ height:44px; }}

        /* Compare mode */
        .cmp-country {{ font-size:1.2rem; font-weight:700; margin-bottom:2px; }}
        .cmp-meta    {{ font-size:0.72rem; color:var(--muted); }}
        .cmp-row     {{ display:flex; justify-content:space-between; padding:11px 0;
                        border-bottom:1px solid var(--divider); font-size:0.8rem; }}
        .cmp-better  {{ font-weight:600; }}

        /* Map layer toggle */
        .layer-btn {{ border:1px solid var(--border) !important; border-radius:3px !important;
                      background:var(--card) !important; color:var(--muted) !important;
                      font-size:0.62rem !important; letter-spacing:0.08em !important;
                      text-transform:uppercase !important; }}
        .layer-btn.active {{ border-color:var(--accent) !important; color:var(--accent) !important;
                             background:var(--accent_dim) !important; }}

        /* Compare row colours */
        .pos {{ color:var(--positive); font-weight:600; }}
        .neg {{ color:var(--negative); font-weight:600; }}

        /* Streamlit widget overrides — institutional dark */

        /* Main area buttons */
        .stApp .stButton > button {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["accent_blue"]} !important;
            border: 1px solid {COLORS["accent_blue"]}44 !important;
            border-radius: 3px !important;
            font-size: 0.65rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
            padding: 6px 14px !important;
        }}
        .stApp .stButton > button:hover {{
            border-color: {COLORS["accent_blue"]} !important;
            background: {COLORS["accent_dim"]} !important;
        }}

        /* Filter chip buttons (news category) */
        [data-testid="stHorizontalBlock"] .stButton > button {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["text_secondary"]} !important;
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 2px !important;
            font-size: 0.62rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em !important;
            padding: 4px 10px !important;
        }}
        [data-testid="stHorizontalBlock"] .stButton > button:hover {{
            border-color: {COLORS["accent_blue"]} !important;
            color: {COLORS["accent_blue"]} !important;
        }}

        /* Streamlit tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 0 !important; }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            color: {COLORS["text_secondary"]} !important;
            border-bottom: 2px solid transparent !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
            padding: 8px 16px !important;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS["text_primary"]} !important;
            background: transparent !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS["accent_blue"]} !important;
            border-bottom-color: {COLORS["accent_blue"]} !important;
        }}

        /* Streamlit expander */
        .streamlit-expander {{ 
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 4px !important;
            background: {COLORS["card_surface"]} !important;
        }}
        .streamlit-expander header {{
            color: {COLORS["text_secondary"]} !important;
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.06em !important;
        }}

        /* Alert / info boxes */
        .stAlert {{
            background: {COLORS["card_surface"]} !important;
            border: 1px solid {COLORS["divider"]} !important;
            border-radius: 4px !important;
        }}

        /* Success/info messages */
        div[data-testid="stSuccess"] {{
            background: {COLORS["card_surface"]} !important;
            color: {COLORS["positive_green"]} !important;
        }}

        /* Responsive */
        @media (max-width: 900px) {{ .topbar {{ flex-direction:column; gap:4px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "selected_country":  "us",
        "news_filter":       None,
        "map_layer":        "gdp_value",
        "compare_mode":     False,
        "sources_open":     False,
        "fred_api_key":     "",
        "refresh_key":      0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"<div style='font-size:0.6rem;letter-spacing:0.22em;text-transform:uppercase;"
            f"color:{COLORS['accent_blue']};font-weight:700;'>Macro Intelligence</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:1rem;font-weight:700;color:{COLORS['text_primary']};margin-bottom:16px;'>"
            f"MACRO CENTER</div>",
            unsafe_allow_html=True,
        )

        # Country selector
        countries = get_all_countries()
        idx = countries.index(st.session_state.selected_country) if st.session_state.selected_country in countries else 0
        selected = st.selectbox(
            "Country",
            countries,
            index=idx,
            format_func=lambda k: f"{get_country_metadata(k)['flag']}  {get_country_metadata(k)['name']}",
        )
        if selected != st.session_state.selected_country:
            st.session_state.selected_country = selected
            st.rerun()

        st.divider()

        # All countries list
        st.markdown(f"<div class='sec-label' style='margin-bottom:8px;'>Countries</div>", unsafe_allow_html=True)
        for ck in countries:
            meta = get_country_metadata(ck)
            if st.button(f"{meta['flag']}  {meta['name']}", key=f"sb-{ck}", use_container_width=True):
                st.session_state.selected_country = ck
                st.rerun()

        st.divider()

        # Settings
        st.markdown(f"<div class='sec-label' style='margin-bottom:8px;'>Settings</div>", unsafe_allow_html=True)
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
            f"News: {CACHE_TTL['news']//60}min · API: {CACHE_TTL['api']//3600}h · Composite: {CACHE_TTL['composite']//60}min",
            help="Data is cached by type. News and live API data have independent TTLs.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Top bar
# ─────────────────────────────────────────────────────────────────────────────
def _render_topbar(news_updated: str, data_updated: str) -> None:
    now_str = datetime.now().strftime("%H:%M · %b %d, %Y")
    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="topbar-brand">Macro Intelligence Platform</div>
                <div class="topbar-title">MACRO CENTER</div>
            </div>
            <div class="topbar-meta">
                <div>Data: {data_updated}</div>
                <div>News: {news_updated}</div>
                <div style="margin-top:2px;color:{COLORS['accent_blue']};">{now_str}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Country overview panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_country_overview(country_key: str, snapshot: dict) -> None:
    meta = get_country_metadata(country_key)
    ind = snapshot
    regime = get_regime_tag(ind)

    regime_colors = {
        "Disinflation":       COLORS["positive_green"],
        "Reflation":          COLORS["negative_red"],
        "Stagnation":         COLORS["negative_red"],
        "Policy tightening":  COLORS["amber"],
        "Policy easing":      COLORS["accent_blue"],
        "Fiscal stress":      COLORS["negative_red"],
        "External vulnerability": COLORS["negative_red"],
        "Stable expansion":   COLORS["accent_blue"],
        "Overheating":        COLORS["negative_red"],
    }
    rc = regime_colors.get(regime, COLORS["text_secondary"])

    as_of_str = snapshot.get("as_of", "")
    if as_of_str:
        try:
            as_of_fmt = datetime.fromisoformat(as_of_str).strftime("%b %d, %Y")
        except Exception:
            as_of_fmt = as_of_str[:10]
    else:
        as_of_fmt = "N/A"

    st.markdown(
        f"""
        <div class="mc-card" style="margin-bottom:14px;">
            <!-- Country name + meta row -->
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid {COLORS['divider']};">
                <div>
                    <div class="cname">{meta['flag']}  {meta['name']}</div>
                    <div class="cmeta">{meta['region']} · {meta['income_group']}</div>
                </div>
                <div class="casof">
                    <div>Data as of</div>
                    <div style="color:{COLORS['text_secondary']};margin-top:2px;">{as_of_fmt}</div>
                </div>
            </div>

            <!-- Regime tag + summary sentence -->
            <div style="margin-bottom:12px;">
                <span class="ctag" style="color:{rc};border:1px solid {rc}44;background:{rc}11;">{regime}</span>
                <span style="font-size:0.78rem;color:{COLORS['text_secondary']};font-style:italic;
                             font-family:'IBM Plex Serif',Georgia,serif;">
                    {meta['summary_sentence']}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI cards — 10 key macro indicators
# ─────────────────────────────────────────────────────────────────────────────
def _render_kpi_cards(country_key: str, snapshot: dict) -> None:
    ind = snapshot

    cards = [
        ("GDP",           _fmt_gdp(ind.get("gdp_value")),            "USD",       None),
        ("GDP Growth",    _fmt_pct(ind.get("gdp_growth", 0)),       "yoy",      _delta(snapshot.get("gdp_growth_delta", 0), higher_positive=True)),
        ("Inflation",    _fmt_pct(ind.get("inflation", 0)),         "yoy",      _delta(snapshot.get("inflation_delta", 0), higher_positive=False, warn_threshold=4.0)),
        ("Unemployment", _fmt_pct(ind.get("unemployment", 0)),      "%",        _delta(snapshot.get("unemployment_delta", 0), higher_positive=False)),
        ("Policy Rate",  _fmt_pct(ind.get("interest_rate", 0)),    "%",        _delta(snapshot.get("interest_rate_delta", 0), higher_positive=False)),
        ("Debt / GDP",   _fmt_pct(ind.get("debt_to_gdp", 0)),      "% of GDP", None),
        ("Curr. Account",_fmt_pct(ind.get("current_account", 0)),    "% of GDP", None),
        ("Population",   _fmt_pop(ind.get("population")),           "people",   None),
        ("GDP per capita",_fmt_gdp_pc(ind.get("gdp_per_capita")),   "USD",       None),
        ("Currency",     ind.get("currency", "N/A"),               "CCY",       None),
    ]

    rows = [cards[:5], cards[5:]]
    for row in rows:
        cols = st.columns(5)
        for col, (label, value, unit, delta) in zip(cols, row):
            delta_text, delta_color = delta if delta is not None else ("", COLORS["text_muted"])
            with col:
                st.markdown(
                    f"""
                    <div class="kpi">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-sub">{unit}</div>
                        <div class="kpi-delta" style="color:{delta_color};">{delta_text or '&nbsp;'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if row == rows[0]:
            st.markdown("<div class='sm'></div>", unsafe_allow_html=True)


def _fmt_gdp(v) -> str:
    if v is None:
        return "N/A"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    return f"${v:,.0f}"

def _fmt_gdp_pc(v) -> str:
    if v is None:
        return "N/A"
    return f"${v:,.0f}"

def _fmt_pct(v: float, decimals: int = 1) -> str:
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}%"

def _fmt_pop(v) -> str:
    if v is None:
        return "N/A"
    if v >= 1e9:
        return f"{v/1e9:.2f}B"
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    return f"{v:,.0f}"

def _delta(value: float, higher_positive: bool, warn_threshold: float = None) -> tuple[str, str]:
    if value is None:
        return "", COLORS["text_muted"]
    if abs(value) < 0.05:
        return "Flat", COLORS["text_secondary"]
    color = COLORS["positive_green"] if (value > 0) == higher_positive else COLORS["negative_red"]
    sign  = "+" if value > 0 else ""
    return f"{sign}{value:.1f}pts vs prior", color


# ─────────────────────────────────────────────────────────────────────────────
# Map layer toggle + world map
# ─────────────────────────────────────────────────────────────────────────────
def _render_map_section(country_key: str) -> None:
    from components.country_map import render_map

    st.markdown(f"<div class='sec-label' style='margin-bottom:10px;'>"
                 f"Global Macro Map — click a country to navigate</div>",
                 unsafe_allow_html=True)

    layers = ["gdp_value", "gdp_growth", "inflation", "interest_rate"]
    layer_labels = {"gdp_value": "GDP", "gdp_growth": "Growth", "inflation": "Inflation", "interest_rate": "Policy Rate"}

    cols = st.columns(len(layers))
    for col, layer in zip(cols, layers):
        active = layer == st.session_state.map_layer
        label  = layer_labels[layer]
        if col.button(
            label,
            use_container_width=True,
            key=f"layer-{layer}",
        ):
            st.session_state.map_layer = layer

    st.markdown("<div class='sp'></div>", unsafe_allow_html=True)

    render_map(country_key, layer=st.session_state.map_layer)


# ─────────────────────────────────────────────────────────────────────────────
# Trend charts
# ─────────────────────────────────────────────────────────────────────────────
def _render_trends(country_key: str) -> None:
    from components.chart_panel import render_trend_grid
    from services.data_cache import get_indicator_series

    st.markdown(f"<div class='sec-label' style='margin-bottom:10px;'>Macroeconomic Trends</div>", unsafe_allow_html=True)
    trend_map = {
        m: get_indicator_series(country_key, m)
        for m in ("inflation", "gdp_growth", "unemployment", "interest_rate")
    }
    render_trend_grid(trend_map)


# ─────────────────────────────────────────────────────────────────────────────
# News flow
# ─────────────────────────────────────────────────────────────────────────────
def _render_news(news_items: list[dict], fetched_at: str, filter_cat: str = None) -> None:
    from components.news_section import render_news_section
    from config import NEWS_CATEGORY_LABELS, NEWS_CATEGORIES

    st.markdown(f"<div class='sec-label' style='margin-bottom:10px;'>Macro News Flow</div>", unsafe_allow_html=True)

    active = [n for n in news_items if not filter_cat or n.get("category") == filter_cat]

    # Filter chips
    all_opts  = [None] + NEWS_CATEGORIES
    all_labels= ["All"] + [NEWS_CATEGORY_LABELS.get(c, c.title()) for c in NEWS_CATEGORIES]
    chip_cols = st.columns(len(all_opts))
    for col, opt, lbl in zip(chip_cols, all_opts, all_labels):
        is_active = opt == filter_cat or (opt is None and filter_cat is None)
        if col.button(lbl, use_container_width=True, key=f"nc-{lbl}"):
            st.session_state.news_filter = opt

    st.markdown("<div class='sp'></div>", unsafe_allow_html=True)
    render_news_section(active, fetched_at)


# ─────────────────────────────────────────────────────────────────────────────
# Risk panel
# ─────────────────────────────────────────────────────────────────────────────
def _render_risk_panel(country_key: str, snapshot: dict) -> None:
    from config import RISK_LABELS

    risks = compute_risks(snapshot)

    risk_colors = {
        "low":    COLORS["risk_low"],
        "medium": COLORS["risk_medium"],
        "high":   COLORS["risk_high"],
    }

    st.markdown(
        f"<div class='sec-label' style='margin-bottom:12px;'>Country Risk Assessment</div>",
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
                    <div class="mc-card" style="padding:14px 16px;text-align:center;">
                        <div class="ctag risk-{level}">{level.upper()}</div>
                        <div style="font-size:0.82rem;font-weight:600;color:{COLORS['text_primary']};margin-top:6px;">
                            {label}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if i + 3 < len(items):
            st.markdown("<div class='sp'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# What Matters Now — analytical commentary
# ─────────────────────────────────────────────────────────────────────────────
def _render_insights(country_key: str, snapshot: dict, regime: str) -> None:
    from config import SENTIMENT_TAGS
    from data.country_data import get_country_metadata

    meta    = get_country_metadata(country_key)
    ind     = snapshot
    bullets = []

    inf   = ind.get("inflation", 0)
    grow  = ind.get("gdp_growth", 0)
    unem  = ind.get("unemployment", 0)
    rate  = ind.get("interest_rate", 0)
    delta = ind.get("interest_rate_delta", 0)
    debt  = ind.get("debt_to_gdp", 0)
    ca    = ind.get("current_account", 0)

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
            "sustaining that progress without premature loosening that could reignite price pressures."
        )

    if delta >= 0.25:
        bullets.append(
            f"Rates held or raised ({delta:+.1f}pts), maintaining a restrictive posture. "
            "The transmission to demand is underway with a typical 12–18 month lag."
        )
    elif delta <= -0.25:
        bullets.append(
            f"Rate cuts of {delta:+.1f}pts are in train. The easing cycle should support "
            "activity through the year, though credit conditions remain tight for now."
        )

    if unem <= 4.0:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals a tight labour market. "
            "Wage growth is likely to stay elevated, keeping services inflation sticky."
        )
    elif unem >= 6.5:
        bullets.append(
            f"Unemployment at {unem:.1f}% signals growing labour slack. "
            "This should eventually ease wage and services price pressures, "
            "giving the central bank more room to support activity."
        )

    if grow >= 4.0:
        bullets.append(
            f"Growth of {grow:.1f}% is above trend for a developed economy, "
            "reinforcing a higher-for-longer policy backdrop and limiting easing scope."
        )
    elif grow < 0.5:
        bullets.append(
            f"Growth of {grow:.1f}% signals significant economic slack. "
            "The risk of a more pronounced downturn is elevated and warrants close monitoring."
        )

    if debt >= 100 and ca < -3:
        bullets.append(
            f"Sovereign finances are under pressure: debt at {debt:.0f}% of GDP with a "
            f"current account deficit of {ca:.1f}% creates external vulnerability. "
            "Bond spreads and currency risk premiums could rise if fiscal credibility slips."
        )
    elif debt >= 100:
        bullets.append(
            f"Debt at {debt:.0f}% of GDP is a long-term constraint on fiscal flexibility. "
            "Debt servicing costs will remain elevated even if rates fall, limiting "
            "the budget's ability to respond to future shocks."
        )

    bullets.append(
        f"Current regime: <strong>{regime}</strong>. "
        f"{SENTIMENT_TAGS.get(regime, 'The macro backdrop remains fluid.')}"
    )

    st.markdown(
        f"""
        <div class="mc-card">
            <div class="sec-label" style="margin-bottom:14px;">What Matters Now</div>
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
# Source panel (collapsible)
# ─────────────────────────────────────────────────────────────────────────────
def _render_source_panel() -> None:
    with st.expander("Data sources & methodology", expanded=st.session_state.sources_open):
        st.markdown(
            f"""
            <div style="font-size:0.78rem; color:{COLORS['text_secondary']}; line-height:1.6;">
            <strong style="color:{COLORS['text_primary']};">Indicator data</strong><br>
            Primary: World Bank Open Data API — all countries, all non-US series.<br>
            US indicators: Federal Reserve Economic Data (FRED) API, accessed via FRED API key.<br>
            Fallback: curated static estimates from IMF World Economic Outlook when APIs are unavailable.<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">News data</strong><br>
            Live: Reuters Business, Reuters Economics, Financial Times, CNBC, MarketWatch RSS feeds.<br>
            Fallback: curated macro summaries when all RSS sources fail.<br>
            News items without a valid source URL are clearly labelled "Source unavailable".<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">Cache strategy</strong><br>
            World Bank / FRED API data: cached {CACHE_TTL['api']//3600}h.<br>
            Derived country snapshots: cached {CACHE_TTL['composite']//60}min.<br>
            Map dataset: cached {CACHE_TTL['map']//60}min.<br>
            News items: cached {CACHE_TTL['news']//60}min.<br>
            <br>
            <strong style="color:{COLORS['text_primary']};">Risk methodology</strong><br>
            Inflation Risk: low < 2.5%, medium < 4.0%, high ≥ 4.0%.<br>
            Fiscal Risk: low < 50%, medium < 80%, high ≥ 80% of GDP.<br>
            External Risk: low > -3%, medium > -5%, high ≤ -5% of current account.<br>
            Growth Momentum: low < 1%, medium < 2.5%, high ≥ 2.5%.<br>
            Policy Stance: low < 3.5%, medium < 5.0%, high ≥ 5.0%.<br>
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

    # Get news first (for timestamps)
    news_items, news_fetched = get_all_news(st.session_state.selected_country)

    # Get data snapshot
    snapshot = get_country_snapshot(st.session_state.selected_country)
    data_as_of = snapshot.get("as_of", "")[:16] if snapshot.get("as_of") else "N/A"
    regime = get_regime_tag(snapshot)

    # Top bar
    _render_topbar(news_fetched, data_as_of)

    # Compare mode vs country view
    if st.session_state.compare_mode:
        _render_compare()
    else:
        country_key = st.session_state.selected_country

        # 1. Country overview panel
        _render_country_overview(country_key, snapshot)

        # 2. KPI cards
        st.markdown("<div class='sm'></div>", unsafe_allow_html=True)
        _render_kpi_cards(country_key, snapshot)

        # 3. Map + layer toggle
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        _render_map_section(country_key)

        # 4+5. Trends + risk panel
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        trend_col, risk_col = st.columns([2.0, 1.0], gap="large")
        with trend_col:
            _render_trends(country_key)
        with risk_col:
            _render_risk_panel(country_key, snapshot)

        # 6. What Matters Now
        st.markdown("<div class='md'></div>", unsafe_allow_html=True)
        insight_col, news_col = st.columns([1.2, 2.0], gap="large")
        with insight_col:
            _render_insights(country_key, snapshot, regime)
        with news_col:
            _render_news(news_items, news_fetched, st.session_state.news_filter)

    # 7. Source panel
    st.markdown("<div class='md'></div>", unsafe_allow_html=True)
    _render_source_panel()

    st.markdown("<div class='lg'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()