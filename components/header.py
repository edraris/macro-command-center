"""
Minimal institutional page header — brand identity strip.
No gradients, no playful elements. Clean, authoritative.
"""
from __future__ import annotations

import streamlit as st

from config import COLORS


def render_header() -> None:
    # Header is now integrated into the sidebar branding.
    # This function is kept for backwards compatibility / slot usage.
    st.markdown(
        f"""
        <div style="
            border-bottom: 1px solid {COLORS['divider']};
            padding: 20px 0 16px;
            margin-bottom: 24px;
        ">
            <div style="
                font-size: 0.62rem;
                letter-spacing: 0.22em;
                text-transform: uppercase;
                color: {COLORS['accent_blue']};
                font-weight: 600;
                margin-bottom: 4px;
            ">Macroeconomic Intelligence Platform</div>
            <div style="
                font-size: 1.5rem;
                font-weight: 700;
                color: {COLORS['text_primary']};
                letter-spacing: -0.01em;
            ">MACRO CENTER</div>
            <div style="
                font-size: 0.78rem;
                color: {COLORS['text_secondary']};
                margin-top: 4px;
                font-family: 'IBM Plex Serif', Georgia, serif;
                font-style: italic;
            ">Real-time global macroeconomic intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
