"""
Sentiment analysis — derives macro regime from indicator values.
Kept as a separate module for backwards compatibility.
Delegates to data.country_data.get_regime_tag().
"""
from __future__ import annotations

from config import SENTIMENT_TAGS
from data.country_data import get_regime_tag as _get_regime_tag


def get_market_sentiment(country_key: str, indicators: dict) -> tuple[str, str]:
    """
    Returns (regime_tag, description) for a given country + indicators.
    """
    tag   = _get_regime_tag(indicators)
    desc  = SENTIMENT_TAGS.get(tag, "The macro backdrop remains fluid.")
    return tag, desc