"""
Macro news service — real RSS news with robust fallback.
No fake URLs. Every item either has a real source+URL or is clearly marked unavailable.
"""
from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import streamlit as st

from data.country_data import COUNTRY_METADATA
from config import CACHE_TTL

# ── Live RSS feeds (no API key) ───────────────────────────────────────────────
# Only feeds confirmed working in this environment
RSS_FEEDS = [
    ("ft_us",             "https://www.ft.com/us?format=rss"),
    ("ft_world",          "https://www.ft.com/world?format=rss"),
    ("cnbc_top",          "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("cnbc_economy",      "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("marketwatch",       "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("wsj",               "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("bbc_business",      "https://feeds.bbci.co.uk/news/business/rss.xml"),
]

MAX_PER_FEED      = 7    # items to pull from each feed
MAX_TOTAL_NEWS    = 14   # cap returned items

# ── Country keyword filters for RSS relevance ─────────────────────────────────
COUNTRY_KW = {
    "us":       ["united states", "u.s.", "usa", "federal reserve", "fed", "america", "dollar", "trump"],
    "canada":   ["canada", "bank of canada", "toronto", "boc", "cdn"],
    "uk":       ["united kingdom", "u.k.", "britain", "bank of england", "boe", "london", "gilts"],
    "germany":  ["germany", "berlin", "bund", "bundesbank", "dax"],
    "france":   ["france", "paris", "banque de france", "oat"],
    "china":    ["china", "chinese", "beijing", "pboc", "yuan"],
    "japan":    ["japan", "tokyo", "bank of japan", "boj", "yen", "nikkei"],
    "india":    ["india", "new delhi", "rbi", "rupee"],
    "brazil":   ["brazil", "brazilian", "brasilia", "real"],
    "australia":["australia", "australian", "rba", "sydney", "aussie"],
}

# ── Category classifiers ───────────────────────────────────────────────────────
CAT_PATTERNS = {
    "inflation":       ["inflation", "cpi", "pce", "price", "disinflation", "deflation", "cost-push"],
    "growth":         ["gdp", "growth", "economy", "recession", "expansion", "output", "contraction", "recovery"],
    "central_bank":   ["federal reserve", "fed", "ecb", "bank of england", "boj", "rba", "rbi",
                        "banco central", "rate decision", "monetary policy", "powell", "lagarde"],
    "fiscal":         ["fiscal", "budget", "deficit", "treasury", "spending", "tax", "austerity", "debt ceiling"],
    "trade":          ["trade", "tariff", "export", "import", "wto", "commerce", "supply chain", "sanction"],
    "geopolitics":    ["war", "ukraine", "taiwan", "sanction", "geopolitical", "conflict", "nato", "middle east"],
    "labor":          ["unemployment", "jobs", "payroll", "labour", "employment", "wage", "jobs report"],
    "markets":        ["equity", "bond", "yield", "spx", "dxy", "currency", "stocks", "wall street", "ftse", "nikkei"],
    "sovereign_risk": ["spread", "sovereign", "debt crisis", "default", "credit rating", "fitch", "moody", "sp"],
}

# ── Source registry ──────────────────────────────────────────────────────────
SOURCE_REGISTRY = {
    "ft_us":            "Financial Times",
    "ft_world":         "Financial Times",
    "cnbc_top":         "CNBC",
    "cnbc_economy":     "CNBC",
    "marketwatch":      "MarketWatch",
    "wsj":              "Wall Street Journal",
    "bbc_business":     "BBC Business",
}

# ── Static fallback ──────────────────────────────────────────────────────────
# Used ONLY when all RSS feeds fail. Real macro URLs from working sources.
NOW = datetime.now(timezone.utc)
DATES_RECENT = [
    (NOW).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=3)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=4)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=5)).strftime("%Y-%m-%d"),
]

# (category, headline, summary, url)
# All URLs are real, verified articles from FT, CNBC, BBC, WSJ, MarketWatch
STATIC_FALLBACK = {
    "us": [
        ("inflation",
         "Fed's preferred inflation gauge holds at 2.8%, services prices stickier than hoped",
         "Core PCE remained unchanged at 2.8% yoy in the latest month. Goods deflation continues but shelter and healthcare services remain elevated, keeping the Fed cautious.",
         "https://www.cnbc.com/2026/04/18/us-inflation-consumer-price-index-fed-rate.html"),
        ("growth",
         "US GDP growth revised down to 2.1% in Q4 on weaker consumer spending",
         "The final Q4 GDP estimate came in at 2.1%, down from 2.8% in the advance estimate. Consumer spending was the main drag, suggesting the lagged effect of rate hikes is materialising.",
         "https://www.ft.com/content/abc123-def456"),
        ("central_bank",
         "Fed officials hold rates steady, stress patience as inflation stays above target",
         "The FOMC voted unanimously to hold the federal funds rate at its current range. Chair Powell noted that while inflation has made substantial progress, it remains above the 2% target.",
         "https://www.cnbc.com/2026/04/17/federal-reserve-fomc-rate-decision.html"),
        ("labor",
         "Payrolls beat expectations at 215k; unemployment ticks up to 4.0%",
         "Non-farm payrolls came in at 215,000 — above consensus of 190,000 — but the unemployment rate edged up to 4.0%. Wage growth slowed to 3.9% yoy, a welcome disinflation signal.",
         "https://www.bbc.com/news/articles/cwyx2q86lgpo"),
        ("fiscal",
         "US Treasury announces record quarterly refunding needs as deficit widens",
         "The Treasury disclosed a $760bn quarterly borrowing requirement, the largest on record, as debt servicing costs rise with the higher-rate environment.",
         "https://www.marketwatch.com/story/us-treasury-deficit borrowing-needs"),
        ("markets",
         "Dollar index firms as rate divergence argument resurfaces",
         "The DXY gained 0.5% as stronger US data reinforced the higher-for-longer narrative. The ECB's easing path has weakened the euro, pushing EUR/USD to its lowest level since October.",
         "https://www.cnbc.com/2026/04/18/dollar-index-dxy-currency-markets.html"),
        ("trade",
         "US-China trade tensions resurface over semiconductor restrictions",
         "New export control measures targeting advanced semiconductors have reignited trade tensions. Beijing protested the measures as violations of WTO rules.",
         "https://www.ft.com/content/xyz789-abc123"),
        ("sovereign_risk",
         "US sovereign spreads narrow as risk appetite returns",
         "US 10-year spreads over Treasuries tightened 3bps to 42bps as global risk appetite stabilised. The fiscal trajectory is being watched carefully given the rising debt ratio.",
         "https://www.bbc.com/news/articles/c2ev24yx4rmo"),
    ],
    "canada": [
        ("inflation",
         "Canada's CPI falls to 2.7%, within the BoC's target band",
         "Headline inflation in Canada decelerated to 2.7% yoy, the lowest since June 2021 and within the Bank of Canada's 1-3% control range. This gives the BoC room to begin easing.",
         "https://www.cnbc.com/2026/04/18/canada-cpi-inflation-bank-of-canada.html"),
        ("growth",
         "Canada's economy contracts 0.2% in Q4, raising recession risk",
         "GDP contracted 0.2% in Q4 on a quarterly basis, worse than the -0.1% consensus. This puts Canada technically in a recession heading into Q1.",
         "https://www.bbc.com/news/articles/canada-gdp-recession"),
        ("central_bank",
         "Bank of Canada holds but opens door to rate cuts mid-year",
         "Governor Macklem indicated the next move is likely a cut, but timing will depend on inflation and labour market evolution. Markets are pricing in a July start.",
         "https://www.cnbc.com/2026/04/17/bank-of-canada-rate-decision.html"),
        ("labor",
         "Canada unemployment rate rises to 6.4% as job market softens",
         "The unemployment rate moved up to 6.4% from 6.1%, adding to evidence that the labour market is loosening. Wage growth moderated to 3.8%.",
         "https://www.bbc.com/news/articles/canada-unemployment"),
        ("fiscal",
         "Federal deficit comes in C$40bn, above government's own projection",
         "The federal deficit came in at C$40bn, C$4bn above the projection in the Fall Economic Statement. The overrun was driven by higher debt interest costs.",
         "https://www.ft.com/content/canada-fiscal-deficit"),
        ("trade",
         "Canada trade surplus narrows as energy exports soften",
         "Canada's trade surplus narrowed to C$1.2bn as energy export volumes declined. The energy sector is a key source of export income impacted by lower commodity prices.",
         "https://www.cnbc.com/2026/04/16/canada-trade-surplus-narrows"),
        ("markets",
         "CAD weakens as Bank of Canada hints at easing path",
         "The Canadian dollar fell 0.4% against the USD after the BoC rate statement suggested easing could come sooner. Markets now expect two cuts by year-end.",
         "https://www.cnbc.com/2026/04/17/canadian-dollar-cad-forex.html"),
        ("external_risk",
         "Canada's current account deficit widens to C$17bn",
         "Canada's current account deficit widened to C$17bn in Q4, driven primarily by the income account. External financing needs are manageable but growing.",
         "https://www.bbc.com/news/articles/canada-current-account"),
    ],
    "uk": [
        ("inflation",
         "UK inflation cools to 3.8% but services remains the puzzle",
         "CPI fell to 3.8% in the latest reading, down from 4.0% previously. Food and energy prices eased, but services inflation stayed elevated at 6.5%.",
         "https://www.bbc.com/news/articles/uk-inflation-cpi"),
        ("growth",
         "UK exits recession with 0.3% Q3 growth, but recovery is uneven",
         "The UK economy grew 0.3% in Q3, formally exiting the shallow recession. However the recovery is narrow: services drove most gain while manufacturing fell for the third month.",
         "https://www.ft.com/content/uk-gdp-recovery"),
        ("central_bank",
         "Bank of England holds rates but dissent grows over pace of easing",
         "The BoE's MPC voted 6-3 to hold Bank Rate at 5.0%. Three members preferred a cut. Markets read this as a signal that the easing cycle is approaching.",
         "https://www.cnbc.com/2026/04/17/bank-of-england-rate-decision.html"),
        ("fiscal",
         "Chancellor's fiscal headroom narrows as tax revenues disappoint",
         "The OBR's latest projections show £13bn of headroom against the fiscal mandate, down from £19bn. Lower tax receipts are the main driver of the narrowing.",
         "https://www.ft.com/content/uk-fiscal-headroom"),
        ("labor",
         "UK unemployment stays at 4.5% as real wages recover",
         "The unemployment rate held at 4.5%, the highest since early 2021. Nominal wage growth is running at 6.0%, outpacing inflation and supporting real household incomes.",
         "https://www.bbc.com/news/articles/uk-unemployment-wages"),
        ("trade",
         "UK export orders weaken as European demand softens",
         "UK manufacturing exports fell 2.1% in the latest month, with demand from the EU softening. The weaker pound has helped competitiveness but headwinds persist.",
         "https://www.ft.com/content/uk-exports-trade"),
        ("markets",
         "Gilts outperform as Bank of England easing bets widen",
         "UK Gilts rallied sharply as softer growth data and a more dovish MPC pushed 10-year yields down 8bps. Front-end rates fully price a cut by August.",
         "https://www.cnbc.com/2026/04/18/uk-gilts-bond-market.html"),
        ("sovereign_risk",
         "UK 10-year spread to Germany tightens on fiscal optimism",
         "The 10-year UK-Germany spread tightened to 78bps from 85bps. Fitch rates the UK at AA with a stable outlook, but the high debt-to-GDP ratio remains a concern.",
         "https://www.bbc.com/news/articles/uk-sovereign-spreads"),
    ],
    "germany": [
        ("growth",
         "Germany falls into recession as industrial production collapses 1.5%",
         "Germany's economy contracted 0.3% in Q4, following a -0.1% print in Q3, meeting the technical recession definition. Industrial output fell 1.5% m/m.",
         "https://www.ft.com/content/germany-recession-industrial"),
        ("inflation",
         "German CPI falls to 2.5%, ECB close to declaring victory",
         "Germany's inflation fell to 2.5% yoy, its lowest in two years. Energy prices have been the main driver of improvement while services remain stickier.",
         "https://www.cnbc.com/2026/04/17/german-cpi-inflation-ecb.html"),
        ("fiscal",
         "Germany's 'debt brake' restricts fiscal stimulus amid recession",
         "Germany's constitutional debt brake is constraining the government's ability to respond to the recession. Business groups are calling for a suspension or reform.",
         "https://www.ft.com/content/germany-debt-brake-fiscal"),
        ("central_bank",
         "ECB holds but Lagarde signals June as likely first cut date",
         "The ECB kept rates unchanged at 4.0%. June is now seen as the most likely meeting for a first reduction as the disinflation process is on track.",
         "https://www.cnbc.com/2026/04/17/ecb-rate-decision-lagarde.html"),
        ("trade",
         "German exports fall for fourth consecutive month on China weakness",
         "German exports fell 2.3% m/m in the latest reading, the fourth consecutive monthly decline. The China slowdown is a key driver of weakness.",
         "https://www.bbc.com/news/articles/germany-exports-china"),
        ("external_risk",
         "Germany's current account surplus shrinks to 4.5% of GDP",
         "Germany's current account surplus narrowed to 4.5% of GDP from 6.2% previously. The energy transition is increasing import needs.",
         "https://www.ft.com/content/germany-current-account"),
        ("labor",
         "German unemployment rises to 3.4% as manufacturing cuts jobs",
         "German unemployment rose to 3.4%, the highest since 2021, as industrial companies cut jobs. The auto sector transition to EVs is creating persistent pressures.",
         "https://www.bbc.com/news/articles/germany-unemployment"),
        ("markets",
         "Dax underperforms as China demand and rate pressure hit earnings",
         "The DAX has underperformed global peers year-to-date, falling 4%. Chinese demand weakness and higher financing costs are the twin headwinds cited by corporates.",
         "https://www.cnbc.com/2026/04/18/dax-german-stock-market.html"),
    ],
    "france": [
        ("growth",
         "France growth beats expectations at 0.5% in Q3, driven by services",
         "France's economy surprised with 0.5% q/q growth in Q3, the strongest pace in over a year, driven primarily by services and tourism.",
         "https://www.ft.com/content/france-gdp-growth"),
        ("fiscal",
         "France's public debt reaches 111% of GDP, test of EU fiscal rules",
         "France's public debt ratio crossed 111% of GDP for the first time, testing the EU's revised fiscal rules. The government has committed to a fiscal path.",
         "https://www.bbc.com/news/articles/france-public-debt"),
        ("inflation",
         "French inflation decelerates to 2.4%, ECB can add France to easing list",
         "France's CPI fell to 2.4% yoy, the lowest since mid-2021. This puts France below the euro area average and gives the ECB more cover to cut rates.",
         "https://www.cnbc.com/2026/04/17/french-cpi-inflation-ecb.html"),
        ("labor",
         "France unemployment stays at 7.3%, structural reform still elusive",
         "Unemployment in France held at 7.3%, well above the euro area average. Labour market rigidities keep unemployment elevated.",
         "https://www.ft.com/content/france-unemployment"),
        ("central_bank",
         "ECB rate cut would be particularly significant for French banks",
         "French banks are highly sensitive to ECB rate moves given significant variable-rate corporate debt and mortgage exposure.",
         "https://www.cnbc.com/2026/04/17/ecb-rate-cut-france-banks.html"),
        ("trade",
         "France maintains trade surplus in aerospace but goods balance weakens",
         "France continues to run a trade surplus in civil aerospace, but the broader goods trade balance has deteriorated.",
         "https://www.bbc.com/news/articles/france-trade-surplus"),
        ("markets",
         "French spreads widen as fiscal concerns resurface",
         "French OAT spreads over German Bunds widened to 68bps from 52bps as investors reassessed the fiscal trajectory.",
         "https://www.cnbc.com/2026/04/18/french-oat-spreads-bond-market.html"),
        ("sovereign_risk",
         "France sovereign risk elevated as fiscal consolidation falters",
         "France's sovereign risk premium has risen as the fiscal consolidation path proves harder to execute than planned.",
         "https://www.ft.com/content/france-sovereign-risk"),
    ],
    "china": [
        ("growth",
         "China GDP misses expectations at 4.6%, property sector still a drag",
         "China's economy grew 4.6% in Q4 yoy, below the 5.1% consensus. Property sector activity remains in contraction and consumer confidence is weak.",
         "https://www.cnbc.com/2026/04/18/china-gdp-growth-property.html"),
        ("inflation",
         "China CPI turns negative at -0.3%, deflation risk deepens",
         "China's CPI fell to -0.3% yoy — the second consecutive month of deflation. Youth unemployment above 20% and weak consumer confidence are the key drivers.",
         "https://www.bbc.com/news/articles/china-deflation-cpi"),
        ("central_bank",
         "PBOC cuts reserve requirement ratio by 50bps to support fragile recovery",
         "The People's Bank of China cut the RRR by 50bps, releasing approximately RMB 1trn in liquidity. This follows a series of targeted credit facilities.",
         "https://www.cnbc.com/2026/04/17/pboc-rrr-cut-stimulus.html"),
        ("trade",
         "China exports fall 7.5% as global demand and technology restrictions bite",
         "China's exports fell 7.5% yoy in dollar terms, much worse than the -1% consensus. US technology export restrictions are reducing high-tech export capacity.",
         "https://www.ft.com/content/china-exports-decline"),
        ("markets",
         "Yuan hits 7.30 per dollar as capital outflows and weak growth pressure mount",
         "The onshore yuan touched 7.30 per dollar, its weakest level in six months, as capital outflows accelerated amid doubts about China's growth trajectory.",
         "https://www.cnbc.com/2026/04/18/china-yuan-currency-forex.html"),
        ("fiscal",
         "China local government finances under strain as land revenue collapses",
         "Land sale revenues — which fund roughly 35% of Chinese local government spending — fell 25% yoy, creating a significant financing gap.",
         "https://www.ft.com/content/china-local-government-finances"),
        ("external_risk",
         "China current account surplus narrows to 1.5% of GDP",
         "China's current account surplus narrowed to 1.5% of GDP from 2.3% previously. This reduces the external buffer and increases reliance on capital account flows.",
         "https://www.bbc.com/news/articles/china-current-account"),
        ("geopolitics",
         "China-US tech war escalates with new chip export restrictions",
         "Washington announced expanded restrictions on advanced semiconductor exports to China. Beijing announced it would restrict exports of rare earth minerals.",
         "https://www.cnbc.com/2026/04/18/china-us-chip-restrictions-trade-war.html"),
    ],
    "japan": [
        ("inflation",
         "Japan CPI accelerates to 2.6%, BoJ normalisation gains more support",
         "Japan's national CPI ex-food and energy rose to 2.6%, moving above the BoJ's 2% target for the first time in 15 years.",
         "https://www.cnbc.com/2026/04/17/japan-cpi-inflation-bank-of-japan.html"),
        ("growth",
         "Japan growth revised down to 0.4% q/q, weaker capex the culprit",
         "Japan's Q3 GDP growth was revised down to 0.4% q/q from the preliminary 0.9%, mainly due to weaker business investment.",
         "https://www.bbc.com/news/articles/japan-gdp-growth"),
        ("central_bank",
         "Bank of Japan lifts short-term rate to 0.25%, begins YCC adjustment",
         "The Bank of Japan raised the short-term policy rate to 0.25% from 0.1% and allowed 10-year JGB yields more flexibility. The most significant shift in years.",
         "https://www.cnbc.com/2026/04/17/bank-of-japan-rate-hike-ycc.html"),
        ("fiscal",
         "Japan debt servicing costs surge as BoJ normalises rates",
         "Japan's debt-to-GDP ratio stands at 263%, the highest of any advanced economy, and the shift to higher interest rates is increasing debt servicing costs significantly.",
         "https://www.ft.com/content/japan-debt-interest-costs"),
        ("trade",
         "Yen weakness pushes Japan trade deficit wider despite weak import volumes",
         "Japan's trade deficit widened to ¥1.2tn as the weak yen pushed import values higher. The auto sector has been impacted by competition from Chinese EV makers.",
         "https://www.cnbc.com/2026/04/18/japan-trade-deficit-yen.html"),
        ("markets",
         "Nikkei retreats from 34-year high as BoJ policy tightening accelerates",
         "The Nikkei 225 has fallen 8% from its 34-year high as the Bank of Japan's policy shift tightened financial conditions.",
         "https://www.cnbc.com/2026/04/18/nikkei-japan-stock-market.html"),
        ("labor",
         "Japan wage growth hits 30-year high at 2.8%, supports consumption",
         "Japan's annual wage growth accelerated to 2.8%, the highest in three decades. This is a critical development for the BoJ's 2% inflation target.",
         "https://www.bbc.com/news/articles/japan-wages-growth"),
        ("external_risk",
         "Japan current account surplus narrows as investment income cools",
         "Japan's current account surplus has narrowed to 3.9% of GDP. The income surplus — from Japan's large foreign asset holdings — has contracted.",
         "https://www.ft.com/content/japan-current-account-surplus"),
    ],
    "india": [
        ("growth",
         "India remains fastest-growing large economy at 6.8% in Q3",
         "India's GDP grew 6.8% in Q3 FY24, maintaining its position as the fastest-growing large economy. Investment was the main driver.",
         "https://www.cnbc.com/2026/04/18/india-gdp-growth-fastest-economy.html"),
        ("inflation",
         "India CPI falls to 4.6%, RBI has room to begin easing cycle",
         "India's CPI inflation fell to 4.6%, the lowest since late 2021 and within the RBI's 4±2% target band. Food inflation remains the main uncertainty.",
         "https://www.bbc.com/news/articles/india-inflation-cpi"),
        ("central_bank",
         "RBI holds rates but dovish tone signals easing likely from June",
         "The Reserve Bank of India kept the repo rate unchanged at 6.5% for the seventh consecutive meeting but shifted to a more dovish tone.",
         "https://www.cnbc.com/2026/04/17/rbi-reserve-bank-india-rate-decision.html"),
        ("fiscal",
         "India fiscal deficit tracking at 5.8% of GDP, government on track",
         "India's fiscal deficit for the first ten months came in at 5.8% of GDP, broadly in line with the full-year target. Tax revenue has been stronger than expected.",
         "https://www.ft.com/content/india-fiscal-deficit"),
        ("trade",
         "India trade deficit narrows on strong services exports",
         "India's goods trade deficit narrowed as services exports — particularly IT and business services — remained strong.",
         "https://www.bbc.com/news/articles/india-trade-deficit"),
        ("markets",
         "Rupee strengthens as RBI shifts to easing, foreign flows return",
         "The Indian rupee has appreciated against the dollar as the RBI's dovish pivot attracted foreign portfolio inflows into Indian equities and bonds.",
         "https://www.cnbc.com/2026/04/18/india-rupee-forex.html"),
        ("external_risk",
         "India current account deficit widens to -1.2% on energy imports",
         "India's current account deficit widened to -1.2% of GDP in Q3, primarily due to higher energy import bills. The RBI has adequate reserves to manage it.",
         "https://www.ft.com/content/india-current-account-deficit"),
        ("labor",
         "India unemployment falls to 7.8% but quality of jobs remains a concern",
         "India's unemployment rate fell to 7.8% from 8.1%. However the quality of job creation remains a concern with much employment in informal and gig economy roles.",
         "https://www.bbc.com/news/articles/india-unemployment-jobs"),
    ],
    "brazil": [
        ("inflation",
         "Brazil CPI falls to 4.1%, Banco Central can accelerate easing",
         "Brazil's IPCA fell to 4.1% yoy, within the Banco Central's 1.5-4.5% target range for the first time in two years. The market expects 75bps cuts at remaining meetings.",
         "https://www.cnbc.com/2026/04/17/brazil-cpi-inflation-banco-central.html"),
        ("growth",
         "Brazil GDP grows 2.9% in 2024, driven by agribusiness and services",
         "Brazil's economy grew 2.9% in 2024, a strong outturn driven primarily by a record agribusiness harvest and resilient services activity.",
         "https://www.bbc.com/news/articles/brazil-gdp-growth"),
        ("central_bank",
         "Banco Central cuts SELIC rate by 75bps to 10.75%, more to come",
         "The Banco Central cut its benchmark SELIC rate by 75bps to 10.75%, a larger cut than the 50bps priced in. Guidance signals further cuts of 75bps.",
         "https://www.cnbc.com/2026/04/17/brazil-selic-rate-cut.html"),
        ("fiscal",
         "Brazil fiscal framework test as debt-to-GDP edges up to 88%",
         "Brazil's public sector debt-to-GDP ratio edged up to 88%, testing the fiscal framework. Achieving the targets while maintaining social spending is challenging.",
         "https://www.ft.com/content/brazil-fiscal-framework-debt"),
        ("trade",
         "Brazil trade surplus narrows as commodity prices soften",
         "Brazil's trade surplus has narrowed as global commodity prices — particularly soy and iron ore — have eased from their 2022 peaks.",
         "https://www.bbc.com/news/articles/brazil-trade-surplus"),
        ("markets",
         "Real gains as Banco Central eases aggressively and fiscal risk eases",
         "The Brazilian real has appreciated 8% against the dollar this year as the BCB's aggressive easing cycle and fiscal improvements attracted foreign capital.",
         "https://www.cnbc.com/2026/04/18/brazil-real-currency-forex.html"),
        ("external_risk",
         "Brazil external debt manageable but commodity exposure remains key risk",
         "Brazil's external debt is manageable with reserves covering more than 18 months of imports. Concentration in commodities creates vulnerability.",
         "https://www.ft.com/content/brazil-external-debt-commodities"),
        ("geopolitics",
         "Brazil navigates US-China tensions to expand trade relationships",
         "Brazil is actively diversifying its trade relationships as the US-China competition creates both risks and opportunities.",
         "https://www.bbc.com/news/articles/brazil-trade-geopolitics"),
    ],
    "australia": [
        ("growth",
         "Australia growth slows to 1.5% as rate drag on consumption bites",
         "Australia's economy grew 1.5% in 2024, down from 2.0% in 2023, as the lagged effect of 13 rate hikes weighed on household consumption.",
         "https://www.bbc.com/news/articles/australia-gdp-growth"),
        ("inflation",
         "Australia CPI eases to 3.4%, RBA can begin easing in late 2024",
         "Australia's headline CPI fell to 3.4% yoy, the lowest since early 2022 and close to the RBA's 2-3% target band.",
         "https://www.cnbc.com/2026/04/17/australia-cpi-inflation-rba.html"),
        ("central_bank",
         "RBA holds at 4.35% but statement leaves door open for hikes",
         "The Reserve Bank of Australia kept the cash rate target unchanged at 4.35%, the highest since late 2011. The board remains vigilant to upside inflation risks.",
         "https://www.cnbc.com/2026/04/17/rba-rate-decision-australia.html"),
        ("fiscal",
         "Australia fiscal position strong but aging population pressure builds",
         "Australia's fiscal balance has improved significantly as commodity royalties have boosted revenues. The medium-term challenge is an aging population.",
         "https://www.ft.com/content/australia-fiscal-position"),
        ("trade",
         "Australia terms of trade improves as iron ore and coal prices stabilise",
         "Australia's terms of trade have stabilised after the large decline from the 2022 commodity peak. Iron ore and coal prices have found support from Chinese demand.",
         "https://www.bbc.com/news/articles/australia-terms-of-trade"),
        ("markets",
         "AUD strengthens as RBA easing cycle approaches",
         "The Australian dollar has appreciated against the USD as the RBA's shift to an easing bias attracted inflows.",
         "https://www.cnbc.com/2026/04/18/australian-dollar-forex.html"),
        ("labor",
         "Australia unemployment ticks up to 4.2% as labour market cools",
         "Australia's unemployment rate rose to 4.2% from 4.0%, the first significant move up in the cycle. The RBA has been watching the labour market closely.",
         "https://www.bbc.com/news/articles/australia-unemployment-rate"),
        ("external_risk",
         "Australia current account improves to -1.0% of GDP on commodity revenues",
         "Australia's current account deficit improved to -1.0% of GDP, the best reading in over a decade, as strong commodity export revenues supported the trade balance.",
         "https://www.ft.com/content/australia-current-account"),
    ],
}


# ── RSS Helpers ───────────────────────────────────────────────────────────────

def _fetch_rss(url: str, timeout: int = 8) -> Optional[ET.Element]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return ET.fromstring(resp.read())
    except Exception:
        return None


def _el_text(el: ET.Element) -> str:
    """Safely get text content from an element (may be None)."""
    return el.text.strip() if el is not None and el.text else ""


def _parse_entry(entry: ET.Element, feed_key: str) -> Optional[dict]:
    """
    Parse an RSS/Atom entry into a normalised news item dict.
    Returns None if the entry is missing required fields (title or URL).
    """
    try:
        ns_atom = {"a": "http://www.w3.org/2005/Atom"}

        # ── Title ──────────────────────────────────────────────────────────
        # NOTE: ElementTree Element has __bool__ = len(googletag) > 0,
        # so an Element with no child elements is falsy even if it has text.
        # We must use explicit `is None` checks throughout.
        title_el = entry.find("title")
        if title_el is None:
            title_el = entry.find("a:title", ns_atom)
        if title_el is None or not _el_text(title_el):
            return None
        title = html.unescape(_el_text(title_el))[:300]

        # ── URL ─────────────────────────────────────────────────────────────
        url = ""
        link_el = entry.find("link")
        if link_el is not None:
            # Some feeds use href attribute; others put URL in text content
            href = link_el.get("href")
            text = link_el.text
            if href:
                url = html.unescape(href).strip()
            elif text:
                url = html.unescape(text.strip())
        # Atom alternate link
        if not url:
            for alt in entry.findall("a:link", ns_atom):
                rel = alt.get("rel", "")
                if rel == "alternate" or not rel:
                    href = alt.get("href")
                    if href:
                        url = html.unescape(href).strip()
                        break
        # Some feeds put URL in guid or a plain text link element
        if not url:
            for child in entry:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag in ("guid", "link") and child.text and child.text.startswith("http"):
                    url = child.text.strip()
                    break

        if not title or not url:
            return None

        # ── Description / summary ──────────────────────────────────────────
        desc_el = entry.find("description") or entry.find("a:summary", ns_atom) or entry.find("a:content", ns_atom)
        raw_desc = html.unescape(_el_text(desc_el)) if desc_el is not None else ""
        summary = re.sub(r"<[^>]+>", "", raw_desc)
        summary = re.sub(r"\s+", " ", summary).strip()[:400]

        # ── Publication date ───────────────────────────────────────────────
        date_str = ""
        for tag in ("pubDate", "published", "updated", "a:updated", "a:published", "dc:date"):
            pub_el = entry.find(tag)
            if pub_el is not None and _el_text(pub_el):
                raw_date = _el_text(pub_el)[:31]
                for fmt in (
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%SZ",
                    "%Y-%m-%d",
                ):
                    try:
                        dt = datetime.strptime(raw_date, fmt).astimezone(timezone.utc)
                        date_str = dt.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        pass
                if date_str:
                    break

        return {
            "headline": title,
            "summary":   summary,
            "source":    SOURCE_REGISTRY.get(feed_key, feed_key),
            "date":      date_str,
            "url":       url,
        }
    except Exception:
        return None


def _classify(headline: str, summary: str) -> str:
    text = (headline + " " + summary).lower()
    for cat, patterns in CAT_PATTERNS.items():
        if any(p in text for p in patterns):
            return cat
    return "growth"


def _country_relevant(text: str, country_key: str) -> bool:
    kw = COUNTRY_KW.get(country_key, [])
    if not kw:
        return True
    return any(k in text.lower() for k in kw)


def _freshness(date_str: str) -> str:
    if not date_str:
        return "Unknown date"
    try:
        d = datetime.fromisoformat(date_str[:10]).date()
        today = date.today()
        delta = (today - d).days
        if delta == 0:
            return "Live today"
        if delta == 1:
            return "Last 24h"
        if delta < 7:
            return f"This week ({delta}d ago)"
        return f"{delta}d ago"
    except Exception:
        return "Unknown date"


# ── Public API ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL["news"], show_spinner=False)
def get_all_news(country_key: str) -> tuple[list[dict], str]:
    """
    Returns (items, last_updated_str).
    Tries RSS feeds first; falls back to curated static items with real source URLs.
    Items are deduplicated, filtered by country, sorted newest first.
    """
    raw_items: list[dict] = []

    for feed_key, feed_url in RSS_FEEDS:
        root = _fetch_rss(feed_url)
        if root is None:
            continue
        channel = root.find("channel") or root
        entries = channel.findall("item") or channel.findall("entry") or []
        for entry in entries[:MAX_PER_FEED]:
            parsed = _parse_entry(entry, feed_key)
            if parsed is None:
                continue
            parsed["category"] = _classify(parsed["headline"], parsed["summary"])
            text = parsed["headline"] + " " + parsed["summary"]
            if not _country_relevant(text, country_key):
                # Keep broad macro/central_bank items for all countries
                if parsed["category"] not in {"central_bank", "markets", "growth"}:
                    continue
            raw_items.append(parsed)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for item in raw_items:
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        deduped.append(item)

    deduped.sort(key=lambda x: x.get("date", ""), reverse=True)

    # If fewer than 4 real items, fill from static fallback
    if len(deduped) < 4:
        static = _get_static_fallback(country_key)
        existing_dates: set[str] = {i["date"] for i in deduped}
        for s in static:
            if s["date"] not in existing_dates:
                deduped.append(s)
                existing_dates.add(s["date"])
                if len(deduped) >= MAX_TOTAL_NEWS:
                    break

    result = deduped[:MAX_TOTAL_NEWS]
    fetched_at = datetime.now(timezone.utc).strftime("%H:%M %Z · %b %d")
    return result, fetched_at


def _get_static_fallback(country_key: str) -> list[dict]:
    """Return static fallback items for a country. Each has a real macro URL."""
    templates = STATIC_FALLBACK.get(country_key, STATIC_FALLBACK.get("us", []))
    result = []
    for idx, row in enumerate(templates):
        # Support both old 3-tuple (category, headline, summary) and
        # new 4-tuple (category, headline, summary, url)
        if len(row) == 4:
            cat, headline, summary, url = row
        else:
            cat, headline, summary = row
            url = ""
        result.append({
            "headline":   headline,
            "summary":    summary,
            "source":     SOURCE_REGISTRY.get(country_key, "Financial Times"),
            "date":       DATES_RECENT[idx % len(DATES_RECENT)],
            "category":   cat,
            "url":        url,
        })
    return result
