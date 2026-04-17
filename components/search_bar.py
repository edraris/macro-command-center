from __future__ import annotations

import streamlit as st

from utils.country_utils import get_all_countries, get_country_metadata


def render_search() -> str:
    countries = get_all_countries()

    def label(country_key: str) -> str:
        meta = get_country_metadata(country_key)
        return f"{meta['flag']}  {meta['name']}  ·  {meta['region']}"

    current = st.session_state.get("selected_country", countries[0])
    selected = st.selectbox(
        "Select a country to explore",
        countries,
        index=countries.index(current),
        format_func=label,
        help="Search by typing country name or region.",
    )
    st.session_state.selected_country = selected
    return selected
