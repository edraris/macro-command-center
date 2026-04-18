# ── Macro Center — Global Configuration ─────────────────────────────────────

import os

# ── Colour palette — institutional dark (Bloomberg/FT/IMF) ─────────────────
COLORS = {
    "background":      "#0c0e14",
    "surface":         "#13151f",
    "card_surface":   "#181b26",
    "card_border":    "rgba(255,255,255,0.065)",
    "text_primary":   "#e2e4ec",
    "text_secondary": "#7b7f94",
    "text_muted":     "#4c5068",
    "accent_blue":     "#4a7fc1",
    "accent_dim":     "rgba(74,127,193,0.12)",
    "positive_green": "#4a9e74",
    "negative_red":   "#b84d44",
    "amber":          "#b8943c",
    "divider":        "rgba(255,255,255,0.055)",
    # Risk category colours
    "risk_low":       "#4a9e74",
    "risk_medium":    "#b8943c",
    "risk_high":      "#b84d44",
}

# ── Typography ────────────────────────────────────────────────────────────────
FONT_SANS = '"IBM Plex Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
FONT_SERIF = '"IBM Plex Serif", "Georgia", "Times New Roman", serif'

# ── Country ISO mappings ───────────────────────────────────────────────────
COUNTRY_CODE_MAP = {
    "us":       {"name": "United States",  "iso3": "USA", "iso2": "US"},
    "canada":   {"name": "Canada",         "iso3": "CAN", "iso2": "CA"},
    "uk":       {"name": "United Kingdom", "iso3": "GBR", "iso2": "GB"},
    "germany":  {"name": "Germany",        "iso3": "DEU", "iso2": "DE"},
    "france":   {"name": "France",         "iso3": "FRA", "iso2": "FR"},
    "china":    {"name": "China",          "iso3": "CHN", "iso2": "CN"},
    "japan":    {"name": "Japan",          "iso3": "JPN", "iso2": "JP"},
    "india":    {"name": "India",          "iso3": "IND", "iso2": "IN"},
    "brazil":   {"name": "Brazil",         "iso3": "BRA", "iso2": "BR"},
    "australia":{"name": "Australia",     "iso3": "AUS", "iso2": "AU"},
}

# ── FRED (US only via FRED API; all countries via World Bank) ───────────────
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_SERIES = {
    "gdp_growth":    "A191RL1Q225SBEA",
    "inflation":     "FPCPITOTLZGUSA",
    "unemployment":  "UNRATE",
    "interest_rate": "FEDFUNDS",
}

WORLD_BANK_INDICATORS = {
    "gdp_value":     "NY.GDP.MKTP.CD",
    "gdp_growth":    "NY.GDP.MKTP.KD.ZG",
    "inflation":     "FP.CPI.TOTL.ZG",
    "unemployment":  "SL.UEM.TOTL.ZS",
    "interest_rate": "FR.INR.LEND",
    "debt_to_gdp":   "GC.DOD.TOTL.GD.ZS",
    "current_account":"BN.CAB.XOKA.GD.ZS",
}

# ── Cache TTL by data type ───────────────────────────────────────────────────
CACHE_TTL = {
    "api":        3600,   # FRED + World Bank live calls
    "composite":  600,    # Derived country snapshots
    "map":        900,    # Map dataset
    "news":       900,    # RSS news (15 min — news changes fast)
    "static":     86400,  # Static metadata
}

# ── News categories ──────────────────────────────────────────────────────────
NEWS_CATEGORIES = [
    "inflation",
    "growth",
    "central_bank",
    "fiscal",
    "trade",
    "geopolitics",
    "labor",
    "markets",
    "sovereign_risk",
]

NEWS_CATEGORY_LABELS = {
    "inflation":      "Inflation",
    "growth":         "Growth",
    "central_bank":   "Central Bank",
    "fiscal":         "Fiscal",
    "trade":          "Trade",
    "geopolitics":    "Geopolitics",
    "labor":          "Labour",
    "markets":        "Markets",
    "sovereign_risk": "Sovereign Risk",
}

# ── Map layers ────────────────────────────────────────────────────────────────
MAP_LAYERS = ["gdp_value", "gdp_growth", "inflation", "interest_rate"]

MAP_LAYER_LABELS = {
    "gdp_value":     "GDP (USD)",
    "gdp_growth":    "GDP Growth (%)",
    "inflation":     "Inflation (%)",
    "interest_rate": "Policy Rate (%)",
}

# ── Sentiment regimes ─────────────────────────────────────────────────────────
SENTIMENT_TAGS = {
    "Disinflation":          "Price pressures are abating; central banks are navigating a soft landing path.",
    "Reflation":             "Inflation is re-accelerating; policy tightening or prolonged restraint is warranted.",
    "Stagnation":            "Activity is weak; recession risk is elevated and policy options are narrowing.",
    "Policy tightening":      "Rates are rising to counter inflation; growth and credit conditions will feel the drag.",
    "Policy easing":         "Rates are being cut to support flagging activity; transmission takes 12–18 months.",
    "Fiscal stress":         "Sovereign finances are under pressure; spreads and debt servicing costs are rising.",
    "External vulnerability":"Trade or commodity shocks are testing the external balance; FX pressure is notable.",
    "Stable expansion":      "Growth is at trend; inflation is close to target; policy is on hold.",
    "Overheating":           "Demand is outpacing supply; capacity constraints are building in labour and goods markets.",
}

# ── Risk categories ──────────────────────────────────────────────────────────
RISK_CATEGORIES = ["inflation_risk", "fiscal_risk", "external_risk", "growth_momentum", "policy_stance"]

RISK_LABELS = {
    "inflation_risk":   "Inflation Risk",
    "fiscal_risk":      "Fiscal Risk",
    "external_risk":    "External Risk",
    "growth_momentum":  "Growth Momentum",
    "policy_stance":    "Policy Stance",
}

RISK_THRESHOLDS = {
    "inflation_risk": {"low": 2.5,  "medium": 4.0,  "high": 6.0},
    "fiscal_risk":    {"low": 50.0, "medium": 80.0, "high": 100.0},
    "external_risk":   {"low": -3.0,"medium": -5.0, "high": -10.0},
    "growth_momentum": {"low": 1.0,  "medium": 2.5,  "high": 4.5},
    "policy_stance":   {"low": 3.5,  "medium": 5.0,  "high": 7.0},
}