"""
Country metadata and indicators — re-exported from data.country_data
for backwards compatibility with existing imports.
The authoritative source is data/country_data.py
"""
from __future__ import annotations

from data.country_data import (
    COUNTRY_METADATA,
    get_country_metadata,
    get_all_countries,
    compute_risks,
    get_regime_tag,
)