from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

from config import FRED_API_KEY


def fetch_fred_series(series_id: str) -> pd.DataFrame:
    session_key = ""
    try:
        session_key = st.session_state.get("fred_api_key_input", "")
    except Exception:
        session_key = ""
    api_key = session_key or FRED_API_KEY or os.getenv("FRED_API_KEY", "")
    if not api_key:
        raise ValueError("Missing FRED_API_KEY")

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
        rows.append({"year": pd.to_datetime(item["date"]).year, "value": float(value)})

    if not rows:
        return pd.DataFrame(columns=["year", "value"])

    frame = pd.DataFrame(rows)
    return frame.groupby("year", as_index=False)["value"].mean().sort_values("year").reset_index(drop=True)
