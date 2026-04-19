from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

from config import FRED_API_KEY


def fetch_fred_series(series_id: str) -> pd.DataFrame:
    session_key_val = ""
    try:
        session_key_val = st.session_state.get("fred_api_key", "")
    except Exception:
        session_key_val = ""
    api_key = session_key_val or FRED_API_KEY or os.getenv("FRED_API_KEY", "")
    if not api_key:
        raise ValueError("Missing FRED_API_KEY — add it in Settings or set FRED_API_KEY env var")

    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
        timeout=15,
    )
    response.raise_for_status()

    observations = response.json().get("observations", [])
    rows: list[dict] = []
    for item in observations:
        value = item.get("value")
        if value in (None, "."):
            continue
        try:
            dt = pd.to_datetime(item["date"])
            rows.append({"year": dt.year, "value": float(value)})
        except (ValueError, TypeError):
            continue

    if not rows:
        return pd.DataFrame(columns=["year", "value"])

    frame = pd.DataFrame(rows)

    # Use last available value per year (more accurate for growth/inflation series
    # where annual values are reported as year-end or annual averages)
    frame = frame.groupby("year", as_index=False).last()
    frame = frame.sort_values("year").reset_index(drop=True)
    return frame
