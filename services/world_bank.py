from __future__ import annotations

import pandas as pd
import requests


def fetch_world_bank_indicator(country_iso3: str, indicator: str) -> pd.DataFrame:
    url = f"https://api.worldbank.org/v2/country/{country_iso3}/indicator/{indicator}?format=json&per_page=50"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        parsed = [
            {"year": int(item["date"]), "value": float(item["value"])}
            for item in rows
            if item.get("value") is not None and str(item.get("date", "")).isdigit()
        ]
        if not parsed:
            return pd.DataFrame(columns=["year", "value"])
        return pd.DataFrame(parsed).sort_values("year").reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["year", "value"])
