from __future__ import annotations

from config import COUNTRY_CODE_MAP

COUNTRY_METADATA = {
    "us": {
        **COUNTRY_CODE_MAP["us"],
        "flag": "🇺🇸",
        "region": "North America",
        "income_group": "High income",
        "summary_sentence": "US demand is holding up, but policy remains restrictive as disinflation progresses unevenly.",
        "indicators": {"gdp_value": 28_400_000_000_000, "gdp_growth": 2.3, "inflation": 3.2, "unemployment": 4.0, "interest_rate": 5.25},
    },
    "canada": {
        **COUNTRY_CODE_MAP["canada"],
        "flag": "🇨🇦",
        "region": "North America",
        "income_group": "High income",
        "summary_sentence": "Canada is navigating softer consumption and housing sensitivity while inflation edges closer to target.",
        "indicators": {"gdp_value": 2_300_000_000_000, "gdp_growth": 1.4, "inflation": 2.8, "unemployment": 6.2, "interest_rate": 4.75},
    },
    "uk": {
        **COUNTRY_CODE_MAP["uk"],
        "flag": "🇬🇧",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "The UK is stabilizing after a weak growth patch, though services inflation still complicates easing.",
        "indicators": {"gdp_value": 3_600_000_000_000, "gdp_growth": 0.8, "inflation": 3.9, "unemployment": 4.3, "interest_rate": 5.0},
    },
    "germany": {
        **COUNTRY_CODE_MAP["germany"],
        "flag": "🇩🇪",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "Germany faces a shallow industrial drag, with exports and energy costs still shaping the outlook.",
        "indicators": {"gdp_value": 4_700_000_000_000, "gdp_growth": 0.3, "inflation": 2.6, "unemployment": 3.4, "interest_rate": 4.5},
    },
    "france": {
        **COUNTRY_CODE_MAP["france"],
        "flag": "🇫🇷",
        "region": "Europe",
        "income_group": "High income",
        "summary_sentence": "France is seeing resilient services demand, but fiscal consolidation questions remain in focus.",
        "indicators": {"gdp_value": 3_300_000_000_000, "gdp_growth": 1.0, "inflation": 2.4, "unemployment": 7.2, "interest_rate": 4.5},
    },
    "china": {
        **COUNTRY_CODE_MAP["china"],
        "flag": "🇨🇳",
        "region": "Asia Pacific",
        "income_group": "Upper middle income",
        "summary_sentence": "China is leaning on targeted support as property weakness offsets better export momentum.",
        "indicators": {"gdp_value": 18_200_000_000_000, "gdp_growth": 4.8, "inflation": 1.1, "unemployment": 5.2, "interest_rate": 3.45},
    },
    "japan": {
        **COUNTRY_CODE_MAP["japan"],
        "flag": "🇯🇵",
        "region": "Asia Pacific",
        "income_group": "High income",
        "summary_sentence": "Japan is balancing stronger wage dynamics with a gradual normalization in monetary settings.",
        "indicators": {"gdp_value": 4_300_000_000_000, "gdp_growth": 1.1, "inflation": 2.5, "unemployment": 2.6, "interest_rate": 0.25},
    },
    "india": {
        **COUNTRY_CODE_MAP["india"],
        "flag": "🇮🇳",
        "region": "Asia Pacific",
        "income_group": "Lower middle income",
        "summary_sentence": "India remains one of the fastest-growing major economies, supported by investment and domestic demand.",
        "indicators": {"gdp_value": 4_100_000_000_000, "gdp_growth": 6.5, "inflation": 4.9, "unemployment": 7.6, "interest_rate": 6.5},
    },
    "brazil": {
        **COUNTRY_CODE_MAP["brazil"],
        "flag": "🇧🇷",
        "region": "Latin America",
        "income_group": "Upper middle income",
        "summary_sentence": "Brazil is benefiting from better disinflation, though fiscal credibility remains a macro anchor.",
        "indicators": {"gdp_value": 2_400_000_000_000, "gdp_growth": 2.2, "inflation": 4.5, "unemployment": 7.4, "interest_rate": 10.5},
    },
    "australia": {
        **COUNTRY_CODE_MAP["australia"],
        "flag": "🇦🇺",
        "region": "Asia Pacific",
        "income_group": "High income",
        "summary_sentence": "Australia is slowing modestly as higher rates cool demand, but labor conditions remain constructive.",
        "indicators": {"gdp_value": 1_900_000_000_000, "gdp_growth": 1.8, "inflation": 3.5, "unemployment": 4.2, "interest_rate": 4.35},
    },
}


def get_country_metadata(key: str) -> dict:
    return COUNTRY_METADATA[key]


def get_all_countries() -> list[str]:
    return list(COUNTRY_METADATA.keys())
