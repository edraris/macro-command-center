"""
Country metadata, indicator definitions, and helper functions.
Single source of truth for all country-level data.
"""
from __future__ import annotations

from config import (
    COLORS, CACHE_TTL, FRED_API_KEY, FRED_SERIES, WORLD_BANK_INDICATORS,
    NEWS_CATEGORIES, NEWS_CATEGORY_LABELS, MAP_LAYERS, MAP_LAYER_LABELS,
    SENTIMENT_TAGS, RISK_CATEGORIES, RISK_LABELS, RISK_THRESHOLDS,
    COUNTRY_CODE_MAP,
)

# ── Full country dataset ──────────────────────────────────────────────────────
# All values are current estimates; sourced from World Bank / IMF where available.
# Debt-to-GDP, current account as % of GDP, population, GDP per capita added.

COUNTRY_METADATA = {
    "us": {
        **COUNTRY_CODE_MAP["us"],
        "flag": "🇺🇸",
        "region": "North America",
        "income_group": "High income",
        "summary_sentence": "The US economy is moderating after a strong post-pandemic expansion. Disinflation is underway but services inflation remains sticky, keeping the Fed cautious.",
        "indicators": {
            "gdp_value":      28_400_000_000_000,
            "gdp_growth":     2.3,
            "inflation":      3.2,
            "unemployment":   4.0,
            "interest_rate":  5.25,
            "debt_to_gdp":    122.1,
            "current_account":-3.0,
            "population":     336_000_000,
            "gdp_per_capita": 85_000,
            "currency":       "USD",
        },
    },
    "canada": {
        **COUNTRY_CODE_MAP["canada"],
        "flag": "🇨🇦",
        "region": "North America",
        "income_group": "High income",
        "summary_sentence": "Canada is navigating a consumer slowdown as the BoC holds rates restrictive. Inflation is close to target but housing and labour market dynamics remain complex.",
        "indicators": {
            "gdp_value":      2_340_000_000_000,
            "gdp_growth":     1.1,
            "inflation":      2.7,
            "unemployment":   6.4,
            "interest_rate":  4.50,
            "debt_to_gdp":    107.0,
            "current_account":-1.2,
            "population":      40_000_000,
            "gdp_per_capita":  58_000,
            "currency":        "CAD",
        },
    },
    "uk": {
        **COUNTRY_CODE_MAP["uk"],
        "flag": "🇬🇧",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "The UK is emerging from a shallow recession. Services inflation remains elevated and real wages have only partially recovered, constraining the BoE's ability to ease.",
        "indicators": {
            "gdp_value":      3_340_000_000_000,
            "gdp_growth":     0.6,
            "inflation":      3.8,
            "unemployment":   4.5,
            "interest_rate":  5.00,
            "debt_to_gdp":    101.0,
            "current_account":-3.5,
            "population":      68_000_000,
            "gdp_per_capita":  49_000,
            "currency":        "GBP",
        },
    },
    "germany": {
        **COUNTRY_CODE_MAP["germany"],
        "flag": "🇩🇪",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "Germany is in a technical recession. Industrial production is weak, energy-intensive sectors face structural challenges, and domestic demand remains subdued.",
        "indicators": {
            "gdp_value":      4_460_000_000_000,
            "gdp_growth":     -0.2,
            "inflation":      2.5,
            "unemployment":   3.4,
            "interest_rate":  4.50,
            "debt_to_gdp":     66.0,
            "current_account": 6.8,
            "population":      84_000_000,
            "gdp_per_capita":  53_000,
            "currency":        "EUR",
        },
    },
    "france": {
        **COUNTRY_CODE_MAP["france"],
        "flag": "🇫🇷",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "France shows resilient services activity but faces fiscal consolidation pressure. The government is navigating a high debt ratio while trying to support trend growth.",
        "indicators": {
            "gdp_value":      3_130_000_000_000,
            "gdp_growth":     0.8,
            "inflation":      2.4,
            "unemployment":   7.3,
            "interest_rate":  4.50,
            "debt_to_gdp":    111.0,
            "current_account":-1.4,
            "population":      68_000_000,
            "gdp_per_capita":  46_000,
            "currency":        "EUR",
        },
    },
    "china": {
        **COUNTRY_CODE_MAP["china"],
        "flag": "🇨🇳",
        "region": "Asia Pacific",
        "income_group": "Upper middle income",
        "summary_sentence": "China is facing a structural demand shortfall after the property sector shock. The PBOC is easing but credit growth is sluggish and deflation risks are growing.",
        "indicators": {
            "gdp_value":      18_270_000_000_000,
            "gdp_growth":     4.6,
            "inflation":      0.2,
            "unemployment":   5.2,
            "interest_rate":  3.45,
            "debt_to_gdp":     83.0,
            "current_account": 1.5,
            "population":    1_411_000_000,
            "gdp_per_capita":  13_000,
            "currency":        "CNY",
        },
    },
    "japan": {
        **COUNTRY_CODE_MAP["japan"],
        "flag": "🇯🇵",
        "region": "Asia Pacific",
        "income_group": "High income",
        "summary_sentence": "Japan is in a gradual policy normalisation cycle. Wage inflation is finally building after decades of deflationary pressure. The BoJ is carefully unwinding YCC.",
        "indicators": {
            "gdp_value":      4_230_000_000_000,
            "gdp_growth":     1.0,
            "inflation":      2.6,
            "unemployment":   2.5,
            "interest_rate":  0.25,
            "debt_to_gdp":    263.0,
            "current_account": 3.9,
            "population":     124_000_000,
            "gdp_per_capita":  34_000,
            "currency":        "JPY",
        },
    },
    "india": {
        **COUNTRY_CODE_MAP["india"],
        "flag": "🇮🇳",
        "region": "Asia Pacific",
        "income_group": "Lower middle income",
        "summary_sentence": "India is the fastest-growing large economy, driven by infrastructure spend and a domestic consumption boom. Inflation management is the key policy challenge.",
        "indicators": {
            "gdp_value":      3_900_000_000_000,
            "gdp_growth":     6.8,
            "inflation":      4.6,
            "unemployment":   7.8,
            "interest_rate":  6.50,
            "debt_to_gdp":     84.0,
            "current_account":-1.2,
            "population":    1_450_000_000,
            "gdp_per_capita":   2_700,
            "currency":        "INR",
        },
    },
    "brazil": {
        **COUNTRY_CODE_MAP["brazil"],
        "flag": "🇧🇷",
        "region": "Latin America",
        "income_group": "Upper middle income",
        "summary_sentence": "Brazil's inflation is decelerating and the BCB has begun an easing cycle. Fiscal credibility is the key macro anchor; external debt is manageable but commodity exposure is high.",
        "indicators": {
            "gdp_value":      2_170_000_000_000,
            "gdp_growth":     2.9,
            "inflation":      4.1,
            "unemployment":   7.4,
            "interest_rate": 10.75,
            "debt_to_gdp":     88.0,
            "current_account":-2.5,
            "population":     220_000_000,
            "gdp_per_capita":   9_800,
            "currency":        "BRL",
        },
    },
    "australia": {
        **COUNTRY_CODE_MAP["australia"],
        "flag": "🇦🇺",
        "region": "Asia Pacific",
        "income_group": "High income",
        "summary_sentence": "Australia is experiencing a gentle growth slowdown as rate tightening works through the housing market. Commodity export revenues provide a buffer to the terms-of-trade shock.",
        "indicators": {
            "gdp_value":      1_760_000_000_000,
            "gdp_growth":     1.5,
            "inflation":      3.4,
            "unemployment":   4.2,
            "interest_rate":  4.35,
            "debt_to_gdp":     50.0,
            "current_account":-1.0,
            "population":      27_000_000,
            "gdp_per_capita":  65_000,
            "currency":        "AUD",
        },
    },
}


# ── Lookup helpers ────────────────────────────────────────────────────────────

def get_country_metadata(key: str) -> dict:
    return COUNTRY_METADATA[key]


def get_all_countries() -> list[str]:
    return list(COUNTRY_METADATA.keys())


def compute_risks(indicators: dict) -> dict[str, str]:
    """
    Classify each risk dimension as low / medium / high
    based on configured thresholds.
    """
    thresholds = RISK_THRESHOLDS
    results = {}

    inf = indicators.get("inflation", 0)
    results["inflation_risk"] = (
        "high" if inf >= thresholds["inflation_risk"]["high"]
        else "medium" if inf >= thresholds["inflation_risk"]["medium"]
        else "low"
    )

    debt = indicators.get("debt_to_gdp", 0)
    results["fiscal_risk"] = (
        "high" if debt >= thresholds["fiscal_risk"]["high"]
        else "medium" if debt >= thresholds["fiscal_risk"]["medium"]
        else "low"
    )

    ca = indicators.get("current_account", 0)
    results["external_risk"] = (
        "high" if ca <= thresholds["external_risk"]["high"]
        else "medium" if ca <= thresholds["external_risk"]["medium"]
        else "low"
    )

    growth = indicators.get("gdp_growth", 0)
    results["growth_momentum"] = (
        "high" if growth >= thresholds["growth_momentum"]["high"]
        else "medium" if growth >= thresholds["growth_momentum"]["medium"]
        else "low"
    )

    rate = indicators.get("interest_rate", 0)
    results["policy_stance"] = (
        "high" if rate >= thresholds["policy_stance"]["high"]
        else "medium" if rate >= thresholds["policy_stance"]["medium"]
        else "low"
    )

    return results


def get_regime_tag(indicators: dict) -> str:
    """Classify the macro regime based on indicator values."""
    inflation   = indicators.get("inflation", 0)
    growth      = indicators.get("gdp_growth", 0)
    interest    = indicators.get("interest_rate", 0)
    debt        = indicators.get("debt_to_gdp", 0)

    if debt > 100 and indicators.get("current_account", 0) < -4:
        return "Fiscal stress"
    if inflation > 5.0 and interest > 4.5:
        return "Policy tightening"
    if inflation < 2.0 and growth < 1.5 and interest < 4.0:
        return "Stagnation"
    if inflation > 3.5 and growth > 4.0 and interest > 4.0:
        return "Overheating"
    if inflation < 2.5 and 1.5 <= growth <= 4.0 and interest <= 4.5:
        return "Disinflation"
    if indicators.get("interest_rate_delta", 0) < -0.25:
        return "Policy easing"
    if growth > 4.5 and inflation > 3.0 and interest > 5.0:
        return "Reflation"
    return "Stable expansion"