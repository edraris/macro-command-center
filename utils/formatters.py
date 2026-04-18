from __future__ import annotations

from datetime import datetime, timezone

from config import COLORS


def format_currency(value: float, compact: bool = True) -> str:
    if value is None:
        return "N/A"
    if not compact:
        return f"${value:,.0f}"
    absolute = abs(value)
    if absolute >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


def format_number(value: float, decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1, show_sign: bool = False) -> str:
    if value is None:
        return "N/A"
    if show_sign:
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def format_delta(value: float, decimals: int = 1) -> tuple[str, str]:
    if value is None:
        return "Flat", COLORS["text_secondary"]
    if value > 0.05:
        return f"+{value:.{decimals}f} pts", COLORS["positive_green"]
    if value < -0.05:
        return f"{value:.{decimals}f} pts", COLORS["negative_red"]
    return "Flat", COLORS["text_secondary"]


def format_date(date_str: str) -> str:
    if not date_str:
        return "N/A"
    try:
        value = datetime.fromisoformat(date_str[:10])
        return value.strftime("%b %d, %Y")
    except Exception:
        return date_str[:10]


def truncate(text: str, max_chars: int = 120) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1].rstrip()}…"
