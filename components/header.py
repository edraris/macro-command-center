from __future__ import annotations

import streamlit as st


def render_header() -> None:
    st.markdown(
        """
        <section class="hero-shell">
            <div class="hero-topline">MACROECONOMIC INTELLIGENCE PLATFORM</div>
            <div class="hero-title">MACRO CENTER</div>
            <div class="hero-subtitle">Global Macroeconomic Intelligence</div>
            <div class="hero-nav">
                <span>Overview</span>
                <span>Countries</span>
                <span>Compare</span>
                <span>News</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
