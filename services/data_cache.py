from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from config import CACHE_TTL, FRED_SERIES, WORLD_BANK_INDICATORS
from services.fred_api import fetch_fred_series
from services.world_bank import fetch_world_bank_indicator
from utils.country_utils import COUNTRY_METADATA, get_country_metadata

LOGGER = logging.getLogger(__name__)


def _dev_log(cache_name: str, key: str, status: str) -> None:
    try:
        env = st.secrets.get("ENV", "development")
    except Exception:
        env = "development"
    if env == "development":
        LOGGER.info("%s %s %s", cache_name, status, key)


def _attach_meta(frame: pd.DataFrame, fetched_at: str, source: str) -> pd.DataFrame:
    result = frame.copy()
    result.attrs["as_of"] = fetched_at
    result.attrs["source"] = source
    return result


def _fallback_series(country_key: str, metric_key: str) -> pd.DataFrame:
    base = get_country_metadata(country_key)["indicators"][metric_key]
    years = list(range(datetime.now().year - 11, datetime.now().year + 1))
    drift_map = {
        "gdp_value": 0.025,
        "gdp_growth": 0.18,
        "inflation": 0.14,
        "unemployment": 0.10,
        "interest_rate": 0.22,
    }
    drift = drift_map[metric_key]
    rows = []
    for idx, year in enumerate(years):
        phase = np.sin(idx / 2.1) * drift
        if metric_key == "gdp_value":
            value = base * (0.78 + idx * drift)
        else:
            value = max(base + phase + ((idx % 3) - 1) * drift * 0.6, 0.0)
        rows.append({"year": year, "value": round(float(value), 2)})
    return pd.DataFrame(rows)


@st.cache_data(ttl=CACHE_TTL["api"], show_spinner=False)
def _cached_world_bank(country_iso3: str, indicator: str) -> tuple[pd.DataFrame, str]:
    frame = fetch_world_bank_indicator(country_iso3, indicator)
    _dev_log("api", f"wb:{country_iso3}:{indicator}", "miss")
    return frame, datetime.now().isoformat(timespec="seconds")


@st.cache_data(ttl=CACHE_TTL["api"], show_spinner=False)
def _cached_fred(series_id: str) -> tuple[pd.DataFrame, str]:
    frame = fetch_fred_series(series_id)
    _dev_log("api", f"fred:{series_id}", "miss")
    return frame, datetime.now().isoformat(timespec="seconds")


@st.cache_data(ttl=CACHE_TTL["hot"], show_spinner=False)
def _cached_country_series(country_key: str, metric_key: str) -> tuple[pd.DataFrame, str, str]:
    meta = get_country_metadata(country_key)
    if country_key == "us" and metric_key in FRED_SERIES:
        frame, fetched_at = _cached_fred(FRED_SERIES[metric_key])
        if not frame.empty:
            return frame.tail(20), fetched_at, "FRED"
    indicator = WORLD_BANK_INDICATORS.get(metric_key)
    if indicator:
        frame, fetched_at = _cached_world_bank(meta["iso3"], indicator)
        if not frame.empty:
            return frame.tail(20), fetched_at, "World Bank"
    return _fallback_series(country_key, metric_key), datetime.now().isoformat(timespec="seconds"), "Fallback"


@st.cache_data(ttl=CACHE_TTL["hot"], show_spinner=False)
def _cached_map_dataset() -> tuple[pd.DataFrame, str]:
    rows = []
    fetched_at = datetime.now().isoformat(timespec="seconds")
    for country_key, meta in COUNTRY_METADATA.items():
        gdp_series, series_as_of, _ = _cached_country_series(country_key, "gdp_value")
        gdp_value = float(gdp_series.iloc[-1]["value"]) if not gdp_series.empty else meta["indicators"]["gdp_value"]
        rows.append(
            {
                "country_key": country_key,
                "country": meta["name"],
                "iso3": meta["iso3"],
                "gdp_value": gdp_value,
                "gdp_growth": meta["indicators"]["gdp_growth"],
                "inflation": meta["indicators"]["inflation"],
                "unemployment": meta["indicators"]["unemployment"],
                "interest_rate": meta["indicators"]["interest_rate"],
                "as_of": series_as_of,
            }
        )
    _dev_log("hot", "world_map", "miss")
    return pd.DataFrame(rows), fetched_at


def get_indicator_series(country_key: str, metric_key: str) -> pd.DataFrame:
    key = f"series:{country_key}:{metric_key}"
    seen = st.session_state.setdefault("_cache_trace", set())
    _dev_log("hot", key, "hit" if key in seen else "lookup")
    seen.add(key)
    try:
        frame, fetched_at, source = _cached_country_series(country_key, metric_key)
        return _attach_meta(frame, fetched_at, source)
    except Exception:
        fallback = _fallback_series(country_key, metric_key)
        return _attach_meta(fallback, datetime.now().isoformat(timespec="seconds"), "Fallback")


def get_country_snapshot(country_key: str) -> dict:
    base = get_country_metadata(country_key)["indicators"].copy()
    for metric_key in ("gdp_value", "gdp_growth", "inflation", "unemployment", "interest_rate"):
        frame = get_indicator_series(country_key, metric_key)
        if not frame.empty:
            base[metric_key] = float(frame.iloc[-1]["value"])
            if len(frame) > 1:
                base[f"{metric_key}_delta"] = float(frame.iloc[-1]["value"] - frame.iloc[-2]["value"])
            else:
                base[f"{metric_key}_delta"] = 0.0
        else:
            base[f"{metric_key}_delta"] = 0.0
    base["as_of"] = get_indicator_series(country_key, "gdp_growth").attrs.get("as_of")
    return base


def get_map_dataset() -> pd.DataFrame:
    frame, fetched_at = _cached_map_dataset()
    return _attach_meta(frame, fetched_at, "Macro Center composite")


def clear_all_caches() -> None:
    st.cache_data.clear()
