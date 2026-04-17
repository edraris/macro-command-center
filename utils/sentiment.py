from __future__ import annotations

from config import SENTIMENT_TAGS


def get_market_sentiment(country_key: str, indicators: dict) -> tuple[str, str]:
    growth = indicators.get("gdp_growth", 0.0)
    inflation = indicators.get("inflation", 0.0)
    rates = indicators.get("interest_rate", 0.0)
    unemployment = indicators.get("unemployment", 0.0)

    if inflation > 4.0 and rates >= 4.5:
        tag = "Hawkish policy"
    elif growth < 1.0 and unemployment > 6.0:
        tag = "Growth slowdown"
    elif inflation < 2.5 and rates <= 3.5 and 1.0 <= growth <= 4.5:
        tag = "Cooling inflation"
    elif growth > 4.0 and unemployment < 4.5 and inflation >= 3.0:
        tag = "Overheating risks"
    elif 2.0 <= growth <= 4.0 and inflation < 3.0 and unemployment < 6.0:
        tag = "Stable expansion"
    elif growth > 1.5 and inflation <= 4.0 and unemployment >= 6.0:
        tag = "Recovery phase"
    else:
        tag = "External vulnerability" if country_key in {"germany", "china", "brazil"} else "Stable expansion"
    return tag, SENTIMENT_TAGS[tag]
