from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

from data.sample_data import COUNTRIES, NEWS_HEADLINES, SERIES_META

load_dotenv()
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

BG = "#0d1117"
CARD = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
RED = "#f85149"

WORLD_BANK_CODES = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "interest_rate": "FR.INR.RINR",
    "gdp_value": "NY.GDP.MKTP.CD",
}

FRED_SERIES = {
    "gdp_growth": "A191RL1Q225SBEA",
    "inflation": "FPCPITOTLZGUSA",
    "unemployment": "UNRATE",
    "interest_rate": "FEDFUNDS",
}

COUNTRY_CODE_MAP = {
    "US": "USA",
    "Canada": "CAN",
    "UK": "GBR",
    "Germany": "DEU",
    "France": "FRA",
    "China": "CHN",
    "Japan": "JPN",
    "India": "IND",
    "Brazil": "BRA",
    "Australia": "AUS",
}

st.set_page_config(page_title="Macro Command Center", layout="wide")


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{ background: {BG}; color: {TEXT}; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
            .block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1400px; }}
            .hero {{ background: linear-gradient(135deg, rgba(88,166,255,0.16), rgba(13,17,23,0.96)); border: 1px solid {BORDER}; border-radius: 18px; padding: 24px 28px; margin-bottom: 18px; }}
            .hero h1 {{ margin: 0; font-size: 2.2rem; letter-spacing: 0.08em; }}
            .hero p {{ margin: 8px 0 0 0; color: {MUTED}; font-size: 0.98rem; }}
            .nav-strip {{ margin-top: 14px; color: {MUTED}; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.12em; }}
            .kpi-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px; padding: 18px; min-height: 132px; box-shadow: 0 10px 30px rgba(0,0,0,0.18); }}
            .kpi-label {{ color: {MUTED}; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }}
            .kpi-value {{ font-size: 2rem; font-weight: 700; margin-top: 10px; }}
            .kpi-delta {{ margin-top: 10px; font-size: 0.88rem; font-weight: 600; }}
            .panel {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px; padding: 18px; }}
            .panel-title {{ font-size: 1rem; font-weight: 700; letter-spacing: 0.04em; margin-bottom: 10px; }}
            .news-item {{ border-top: 1px solid {BORDER}; padding: 12px 0; }}
            .news-item:first-child {{ border-top: none; padding-top: 0; }}
            .news-source {{ color: {ACCENT}; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.08em; }}
            div[data-baseweb="select"] > div {{ background-color: {CARD}; border-color: {BORDER}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def fetch_world_bank_indicator(country_code: str, indicator: str) -> pd.DataFrame:
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=80"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    payload = response.json()
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    cleaned = [
        {"year": int(item["date"]), "value": item["value"]}
        for item in rows
        if item.get("value") is not None and str(item.get("date", "")).isdigit()
    ]
    df = pd.DataFrame(cleaned).sort_values("year")
    return df


@st.cache_data(ttl=3600)
def fetch_fred_series(series_id: str) -> pd.DataFrame:
    if not FRED_API_KEY:
        raise ValueError("Missing FRED_API_KEY")
    url = "https://api.stlouisfed.org/fred/series/observations"
    response = requests.get(
        url,
        params={"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"},
        timeout=15,
    )
    response.raise_for_status()
    observations = response.json().get("observations", [])
    rows = []
    for item in observations:
        value = item.get("value")
        if value in (None, "."):
            continue
        rows.append({"year": pd.to_datetime(item["date"]).year, "value": float(value)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby("year", as_index=False)["value"].mean()


@st.cache_data(ttl=3600)
def make_sample_series(country_key: str, metric_key: str) -> pd.DataFrame:
    base = COUNTRIES[country_key][metric_key]
    years = list(range(datetime.now().year - 19, datetime.now().year + 1))
    drift = {
        "gdp_growth": 0.25,
        "inflation": 0.18,
        "unemployment": 0.12,
        "interest_rate": 0.2,
    }[metric_key]
    vals = []
    for idx, year in enumerate(years):
        wave = ((idx % 5) - 2) * drift
        trend = (idx - len(years) / 2) * drift * 0.03
        vals.append({"year": year, "value": round(max(base + wave + trend, -2 if metric_key == 'gdp_growth' else 0), 2)})
    return pd.DataFrame(vals)


@st.cache_data(ttl=3600)
def get_country_series(country_key: str, metric_key: str) -> pd.DataFrame:
    if country_key == "US" and metric_key in FRED_SERIES:
        try:
            df = fetch_fred_series(FRED_SERIES[metric_key])
            return df.tail(20)
        except Exception:
            pass
    try:
        code = COUNTRY_CODE_MAP[country_key]
        df = fetch_world_bank_indicator(code, WORLD_BANK_CODES[metric_key])
        return df.tail(20)
    except Exception:
        return make_sample_series(country_key, metric_key)


@st.cache_data(ttl=3600)
def get_latest_value(country_key: str, metric_key: str) -> tuple[float, float]:
    series = get_country_series(country_key, metric_key)
    if len(series) >= 2:
        current = float(series.iloc[-1]["value"])
        previous = float(series.iloc[-2]["value"])
        return current, current - previous
    value = float(COUNTRIES[country_key][metric_key])
    return value, 0.0


@st.cache_data(ttl=3600)
def build_map_frame() -> pd.DataFrame:
    rows = []
    for country_key, meta in COUNTRIES.items():
        gdp_value = meta["gdp_value"]
        try:
            df = fetch_world_bank_indicator(meta["iso3"], WORLD_BANK_CODES["gdp_value"])
            if not df.empty:
                gdp_value = float(df.iloc[-1]["value"])
        except Exception:
            pass
        rows.append(
            {
                "country": meta["name"],
                "iso3": meta["iso3"],
                "gdp_value": gdp_value,
                "gdp_growth": COUNTRIES[country_key]["gdp_growth"],
                "inflation": COUNTRIES[country_key]["inflation"],
                "unemployment": COUNTRIES[country_key]["unemployment"],
                "interest_rate": COUNTRIES[country_key]["interest_rate"],
            }
        )
    return pd.DataFrame(rows)


def format_delta(delta: float) -> tuple[str, str]:
    arrow = "▲" if delta >= 0 else "▼"
    color = GREEN if delta >= 0 else RED
    return f"{arrow} {abs(delta):.2f} vs prior", color


inject_styles()

st.markdown(
    """
    <div class="hero">
        <h1>MACRO COMMAND CENTER</h1>
        <p>Real-time macro dashboard for global growth, inflation, labor, and rates. Built for fast scanning, deep comparison, and clean presentation.</p>
        <div class="nav-strip">Overview · Time Series · World Map · News Flow · Comparison Matrix</div>
    </div>
    """,
    unsafe_allow_html=True,
)

country = st.selectbox("Select country", list(COUNTRIES.keys()), index=0)
selected_metric = st.radio(
    "Trend indicator",
    options=list(SERIES_META.keys()),
    format_func=lambda key: SERIES_META[key]["label"],
    horizontal=True,
)

kpi_cols = st.columns(4)
for col, metric_key in zip(kpi_cols, SERIES_META.keys()):
    value, delta = get_latest_value(country, metric_key)
    delta_text, delta_color = format_delta(delta)
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{SERIES_META[metric_key]['label']}</div>
                <div class="kpi-value">{value:.2f}{SERIES_META[metric_key]['unit']}</div>
                <div class="kpi-delta" style="color:{delta_color};">{delta_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

left, right = st.columns((1.65, 1), gap="large")

with left:
    st.markdown('<div class="panel-title">20-Year Indicator Trend</div>', unsafe_allow_html=True)
    series_df = get_country_series(country, selected_metric)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=series_df["year"],
            y=series_df["value"],
            mode="lines+markers",
            line={"color": ACCENT, "width": 3},
            marker={"size": 7, "color": ACCENT},
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.10)",
            hovertemplate="%{x}: %{y:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font={"color": TEXT},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"gridcolor": "rgba(139,148,158,0.18)", "zeroline": False},
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">Latest Macro News</div>', unsafe_allow_html=True)
    for item in NEWS_HEADLINES:
        st.markdown(
            f"""
            <div class="news-item">
                <div>{item['headline']}</div>
                <div class="news-source">{item['source']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

map_df = build_map_frame()
map_fig = px.choropleth(
    map_df,
    locations="iso3",
    color="gdp_value",
    hover_name="country",
    hover_data={
        "gdp_value": ":,.0f",
        "gdp_growth": True,
        "inflation": True,
        "unemployment": True,
        "interest_rate": True,
        "iso3": False,
    },
    color_continuous_scale=[[0, "#1f2937"], [0.5, "#2563eb"], [1, "#58a6ff"]],
)
map_fig.update_layout(
    paper_bgcolor=BG,
    plot_bgcolor=CARD,
    margin={"l": 0, "r": 0, "t": 10, "b": 0},
    font={"color": TEXT},
    geo={"bgcolor": BG, "showframe": False, "showcoastlines": False, "projection_type": "natural earth"},
    height=460,
)

st.markdown('<div class="panel-title">Global GDP Map</div>', unsafe_allow_html=True)
st.plotly_chart(map_fig, use_container_width=True)

st.markdown('<div class="panel-title">Country Comparison</div>', unsafe_allow_html=True)
compare_cols = st.columns(2)
country_a = compare_cols[0].selectbox("Country A", list(COUNTRIES.keys()), index=0, key="country_a")
country_b = compare_cols[1].selectbox("Country B", list(COUNTRIES.keys()), index=1, key="country_b")

radar_metrics = list(SERIES_META.keys())
radar_labels = [SERIES_META[m]["label"] for m in radar_metrics]
values_a = [float(get_latest_value(country_a, m)[0]) for m in radar_metrics]
values_b = [float(get_latest_value(country_b, m)[0]) for m in radar_metrics]

radar_fig = go.Figure()
radar_fig.add_trace(
    go.Scatterpolar(r=values_a, theta=radar_labels, fill="toself", name=country_a, line={"color": ACCENT})
)
radar_fig.add_trace(
    go.Scatterpolar(r=values_b, theta=radar_labels, fill="toself", name=country_b, line={"color": "#f78166"})
)
radar_fig.update_layout(
    paper_bgcolor=BG,
    plot_bgcolor=CARD,
    font={"color": TEXT},
    polar={
        "bgcolor": CARD,
        "radialaxis": {"gridcolor": "rgba(139,148,158,0.2)", "linecolor": BORDER, "tickfont": {"color": MUTED}},
        "angularaxis": {"gridcolor": "rgba(139,148,158,0.15)", "tickfont": {"color": TEXT}},
    },
    margin={"l": 20, "r": 20, "t": 10, "b": 20},
    height=420,
)
st.plotly_chart(radar_fig, use_container_width=True)

with st.expander("Data notes"):
    st.write(
        "US indicators use FRED when available. International indicators use World Bank series where possible. If an API request fails, the dashboard falls back to curated sample data to stay fully functional."
    )
