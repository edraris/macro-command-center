from __future__ import annotations

from datetime import datetime

from config import COLORS


def format_currency(value: float, compact: bool = True) -> str:
    if value is None:
        return "N/A"
    if not compact:
        return f"${value:,.0f}"
    absolute = abs(value)
    if absolute >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.1f}T"
    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def format_number(value: float, decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_delta(value: float) -> tuple[str, str]:
    if value is None:
        return ("Flat vs prior", COLORS["text_secondary"])
    if value > 0:
        return (f"Up {value:.1f} pts", COLORS["positive_green"])
    if value < 0:
        return (f"Down {abs(value):.1f} pts", COLORS["negative_red"])
    return ("Flat vs prior", COLORS["text_secondary"])


def format_date(date_str: str) -> str:
    value = datetime.fromisoformat(date_str)
    return value.strftime("%b %d, %Y")


def truncate(text: str, max_chars: int = 120) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1].rstrip()}…"
