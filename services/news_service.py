from __future__ import annotations

from copy import deepcopy

from utils.country_utils import get_country_metadata

NEWS_DATES = [
    "2026-04-17",
    "2026-04-16",
    "2026-04-16",
    "2026-04-15",
    "2026-04-14",
    "2026-04-13",
    "2026-04-12",
    "2026-04-11",
]

COUNTRY_ANGLES = {
    "us": {
        "demand": "consumer spending and services activity",
        "trade": "tariff-sensitive supply chains and North American manufacturing",
        "fiscal": "Treasury issuance and deficit financing",
        "cbank": "Federal Reserve officials",
        "geopolitics": "shipping corridors and strategic technology controls",
        "growth": "business investment and a still-firm labor market",
    },
    "canada": {
        "demand": "household demand and mortgage-sensitive consumption",
        "trade": "energy exports and cross-border auto production",
        "fiscal": "provincial budget discipline and federal spending",
        "cbank": "Bank of Canada policymakers",
        "geopolitics": "commodity channels and North American trade",
        "growth": "population-led demand and weaker productivity",
    },
    "uk": {
        "demand": "services output and fragile consumer confidence",
        "trade": "post-Brexit customs frictions and export orders",
        "fiscal": "pre-budget spending tradeoffs",
        "cbank": "Bank of England speakers",
        "geopolitics": "energy security and Europe-facing trade links",
        "growth": "real wage gains and subdued manufacturing",
    },
    "germany": {
        "demand": "industrial orders and cautious household spending",
        "trade": "capital goods exports and China-facing demand",
        "fiscal": "constitutional debt-brake constraints",
        "cbank": "ECB rate expectations in core Europe",
        "geopolitics": "energy diversification and external demand",
        "growth": "manufacturing stabilization and weak construction",
    },
    "france": {
        "demand": "services resilience and household purchasing power",
        "trade": "euro area trade volumes and aerospace demand",
        "fiscal": "budget consolidation and debt metrics",
        "cbank": "ECB commentary filtered through domestic demand",
        "geopolitics": "European strategic policy and energy markets",
        "growth": "consumer services and investment moderation",
    },
    "china": {
        "demand": "consumer recovery and property-linked confidence",
        "trade": "export momentum in electronics and machinery",
        "fiscal": "local government financing and infrastructure spending",
        "cbank": "PBOC liquidity operations",
        "geopolitics": "technology restrictions and shipping routes",
        "growth": "industrial output and targeted stimulus",
    },
    "japan": {
        "demand": "wage pass-through and domestic consumption",
        "trade": "autos, semiconductors, and yen-sensitive exports",
        "fiscal": "supplementary support and debt-servicing optics",
        "cbank": "Bank of Japan normalization signals",
        "geopolitics": "regional security and energy import channels",
        "growth": "capex plans and inbound tourism",
    },
    "india": {
        "demand": "urban consumption and infrastructure-led investment",
        "trade": "electronics exports and energy import costs",
        "fiscal": "capital spending discipline ahead of state outlays",
        "cbank": "RBI liquidity calibration",
        "geopolitics": "shipping lanes and commodity exposure",
        "growth": "credit expansion and manufacturing capacity",
    },
    "brazil": {
        "demand": "credit conditions and consumer spending",
        "trade": "soy, iron ore, and China-linked exports",
        "fiscal": "primary balance targets and revenue measures",
        "cbank": "Banco Central guidance",
        "geopolitics": "commodity price swings and regional politics",
        "growth": "agribusiness strength and softer domestic industry",
    },
    "australia": {
        "demand": "household spending and rate-sensitive housing demand",
        "trade": "bulk commodity exports and Asia demand",
        "fiscal": "budget restraint and public investment",
        "cbank": "RBA communication",
        "geopolitics": "Asia-Pacific trade routes and commodity diplomacy",
        "growth": "migration support and softer retail volumes",
    },
}

SOURCES = {
    "inflation": "Macro Wire",
    "growth": "Global Economics Daily",
    "central_bank": "Policy Signal",
    "fiscal": "Sovereign Brief",
    "trade": "Trade Ledger",
    "geopolitics": "Frontier Risk",
}

TEMPLATES = [
    ("inflation", "{country} inflation pulse steadies as analysts track {demand}", "Fresh price readings suggest disinflation is improving, but core pressures remain uneven across the economy. Investors are watching whether softer goods pricing can offset persistent services inflation tied to {demand}."),
    ("growth", "{country} growth outlook firms on {growth}", "Economists say near-term activity is being supported by {growth}. The rebound remains uneven, leaving policymakers focused on whether demand can stay resilient without reopening inflation risks."),
    ("central_bank", "{cbank} signal patience as {country} policy debate stays live", "Officials indicated they still need clearer evidence before shifting the rate path materially. Markets read the remarks as a sign that domestic conditions and inflation persistence still outweigh hopes for a rapid easing cycle."),
    ("fiscal", "{country} fiscal debate intensifies around {fiscal}", "Budget discussions are increasingly centered on how to preserve credibility while protecting growth-sensitive spending lines. Strategists warn that any surprise slippage could tighten financial conditions through higher term premiums."),
    ("trade", "{country} exporters watch {trade} for next demand signal", "Trade-sensitive sectors are gauging whether external orders can remain firm as global goods demand rotates. Currency moves and freight costs are also shaping margin expectations for the next quarter."),
    ("geopolitics", "{country} markets price in macro risk from {geopolitics}", "Investors are reassessing how political and supply-chain risks could spill into inflation and trade flows. The immediate economic effect looks manageable, but the tail risk is keeping cross-asset volatility elevated."),
    ("inflation", "Sticky services prices keep {country} inflation narrative in focus", "Analysts note that recent disinflation has been concentrated in traded goods while domestic services remain firmer. That mix complicates the timing of policy easing and keeps rate sensitivity high across local assets."),
    ("growth", "{country} firms flag mixed momentum across {demand}", "Business surveys point to a split between resilient service activity and more hesitant goods demand. The composition matters because it shapes hiring, pricing power, and the durability of the broader expansion."),
]


def _build_news_item(country_key: str, index: int) -> dict:
    meta = get_country_metadata(country_key)
    angle = COUNTRY_ANGLES[country_key]
    category, headline_tmpl, summary_tmpl = TEMPLATES[index]
    headline = headline_tmpl.format(country=meta["name"], **angle)
    summary = summary_tmpl.format(country=meta["name"], **angle)
    return {
        "headline": headline,
        "summary": summary,
        "source": SOURCES[category],
        "date": NEWS_DATES[index],
        "category": category,
        "url": f"https://example.com/{country_key}/{category}/{index + 1}",
    }


def get_all_news(country_key: str) -> list[dict]:
    return [deepcopy(_build_news_item(country_key, index)) for index in range(len(TEMPLATES))]


def get_news(country_key: str, category: str = None) -> list[dict]:
    items = get_all_news(country_key)
    if category:
        return [item for item in items if item["category"] == category]
    return items
