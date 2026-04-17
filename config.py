from __future__ import annotations

import os

COLORS = {
    "background": "#0a0a0f",
    "card_surface": "rgba(255,255,255,0.04)",
    "card_border": "rgba(255,255,255,0.08)",
    "text_primary": "#f5f5f7",
    "text_secondary": "#86868b",
    "accent_blue": "#2997ff",
    "positive_green": "#30d158",
    "negative_red": "#ff453a",
    "amber": "#ffd60a",
}

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

FRED_SERIES = {
    "gdp_growth": "A191RL1Q225SBEA",
    "inflation": "FPCPITOTLZGUSA",
    "unemployment": "UNRATE",
    "interest_rate": "FEDFUNDS",
}

WORLD_BANK_INDICATORS = {
    "gdp_value": "NY.GDP.MKTP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "interest_rate": "FR.INR.LEND",
}

COUNTRY_CODE_MAP = {
    "us": {"name": "United States", "iso3": "USA", "iso2": "US"},
    "canada": {"name": "Canada", "iso3": "CAN", "iso2": "CA"},
    "uk": {"name": "United Kingdom", "iso3": "GBR", "iso2": "GB"},
    "germany": {"name": "Germany", "iso3": "DEU", "iso2": "DE"},
    "france": {"name": "France", "iso3": "FRA", "iso2": "FR"},
    "china": {"name": "China", "iso3": "CHN", "iso2": "CN"},
    "japan": {"name": "Japan", "iso3": "JPN", "iso2": "JP"},
    "india": {"name": "India", "iso3": "IND", "iso2": "IN"},
    "brazil": {"name": "Brazil", "iso3": "BRA", "iso2": "BR"},
    "australia": {"name": "Australia", "iso3": "AUS", "iso2": "AU"},
}

NEWS_CATEGORIES = [
    "inflation",
    "growth",
    "central_bank",
    "fiscal",
    "trade",
    "geopolitics",
]

CACHE_TTL = {
    "api": 3600,
    "hot": 300,
}

SENTIMENT_TAGS = {
    "Cooling inflation": "Price pressures are easing without a clear deterioration in domestic demand.",
    "Growth slowdown": "Activity is losing momentum and labor slack is beginning to show.",
    "Hawkish policy": "Sticky inflation is keeping central banks restrictive.",
    "External vulnerability": "Trade, commodity, or FX sensitivity is raising downside risk.",
    "Recovery phase": "Growth is rebuilding from a soft patch with policy support helping.",
    "Stable expansion": "Growth and inflation remain broadly balanced.",
    "Overheating risks": "Demand is running hot and capacity constraints are building.",
}
