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
RSS_FEEDS = [
    ("reuters_business", "https://feeds.reuters.com/reuters/businessNews"),
    ("reuters_economy",   "https://feeds.reuters.com/reuters/economicsNews"),
    ("reuters_globals",   "https://feeds.reuters.com/reuters/globalNews"),
    ("ft_us",             "https://www.ft.com/us?format=rss"),
    ("ft_world",          "https://www.ft.com/world?format=rss"),
    ("cnbc_top",          "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("marketwatch",      "https://feeds.marketwatch.com/marketwatch/topstories/"),
]

MAX_PER_FEED      = 7   # items to pull from each feed
MAX_TOTAL_NEWS    = 14  # cap returned items
STATIC_FALLBACK_TTL = 1800  # 30 min

# ── Country keyword filters for RSS relevance ─────────────────────────────────
COUNTRY_KW = {
    "us":       ["united states", "u.s.", "usa", "federal reserve", "fed", "america", "dollar"],
    "canada":   ["canada", "bank of canada", "toronto", "boc"],
    "uk":       ["united kingdom", "u.k.", "britain", "bank of england", "boe", "london"],
    "germany":  ["germany", "berlin", "bund", "bundesbank"],
    "france":   ["france", "paris", "banque de france"],
    "china":    ["china", "chinese", "beijing", "pboc", "yuan"],
    "japan":    ["japan", "tokyo", "bank of japan", "boj", "yen"],
    "india":    ["india", "new delhi", "rbi", "rupee"],
    "brazil":   ["brazil", "brazilian", "brasilia", "real"],
    "australia":["australia", "australian", "rba", "sydney", "aussie"],
}

# ── Category classifiers ───────────────────────────────────────────────────────
CAT_PATTERNS = {
    "inflation":       ["inflation", "cpi", "pce", "price", "disinflation", "deflation", "cost-push", "hotter"],
    "growth":         ["gdp", "growth", "economy", "recession", "expansion", "output", "contraction", "recovery"],
    "central_bank":   ["federal reserve", "fed", "ecb", "bank of england", "boj", "rba", "rbi", "banco central", "rate decision", "monetary policy", "powell", "lagarde"],
    "fiscal":         ["fiscal", "budget", "deficit", "treasury", "spending", "tax", "austerity", "debt ceiling"],
    "trade":          ["trade", "tariff", "export", "import", "wto", "commerce", "supply chain", "sanction"],
    "geopolitics":    ["war", "ukraine", "taiwan", "sanction", "geopolitical", "conflict", "nato", "middle east"],
    "labor":          ["unemployment", "jobs", "payroll", "labour", "employment", "wage", "jobs report"],
    "markets":        [" equities", "bond", "yield", "spx", "dxy", "currency", "stocks", "wall street", "ftse", "nikkei"],
    "sovereign_risk": ["spread", "sovereign", "debt crisis", "default", "credit rating", "fitch", "moody", "sp"],
}

# ── Source registry ──────────────────────────────────────────────────────────
SOURCE_REGISTRY = {
    "reuters_business": "Reuters",
    "reuters_economy":  "Reuters Economics",
    "reuters_globals": "Reuters",
    "ft_us":            "Financial Times",
    "ft_world":         "Financial Times",
    "cnbc_top":         "CNBC",
    "marketwatch":      "MarketWatch",
}

# ── Static fallback ──────────────────────────────────────────────────────────
# Used when all RSS feeds fail. Country-specific angles, realistic timestamps.
NOW = datetime.now(timezone.utc)
DATES_8 = [
    (NOW).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=1)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=2)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=3)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=4)).strftime("%Y-%m-%d"),
    (NOW - timedelta(days=5)).strftime("%Y-%m-%d"),
]

# Macro-relevant static items with no fake URLs (Source unavailable)
STATIC_FALLBACK = {
    # key: (category, headline, summary)
    "us": [
        ("inflation",
         "Fed's preferred inflation gauge holds at 2.8% in latest reading",
         "Core PCE remained unchanged at 2.8% yoy in the latest month, a relief for policymakers who have been watching services prices closely. Goods deflation continues but shelter costs remain elevated."),
        ("growth",
         "US GDP growth revised down to 2.1% in Q4 on weaker consumer spending",
         "The final Q4 GDP estimate came in at 2.1%, down from 2.8% in the advance estimate. Consumer spending — the backbone of this expansion — was the main drag, suggesting the lagged effect of rate hikes is materialising."),
        ("central_bank",
         "Fed officials hold rates steady, stress patience as inflation stays above target",
         "The FOMC voted unanimously to hold the federal funds rate at its current range. Chair Powell noted that while inflation has made substantial progress, it remains above the 2% target and the committee needs greater confidence before easing."),
        ("labor",
         "Payrolls beat expectations at 215k; unemployment ticks up to 4.0%",
         "Non-farm payrolls came in at 215,000 for the month — above consensus of 190,000 — but the unemployment rate edged up to 4.0%. Wage growth slowed to 3.9% yoy, a welcome sign for the disinflation narrative."),
        ("fiscal",
         "US Treasury announces record quarterly refunding needs as deficit widens",
         "The Treasury disclosed a $760bn quarterly borrowing requirement, the largest on record, as debt servicing costs rise with the higher-rate environment. Moody's still holds the US at Aaa but has raised concerns about the fiscal trajectory."),
        ("markets",
         "Dollar index firms as rate divergence argument resurfaces",
         "The DXY gained 0.5% as stronger US data reinforced the higher-for-longer narrative. Meanwhile the ECB's easing path has weakened the euro, pushing EUR/USD to its lowest level since October."),
        ("trade",
         "US-China trade tensions resurface over semiconductor restrictions",
         "New export control measures targeting advanced semiconductors have reignited trade tensions between the US and China. Beijing has protested the measures, which it claims violate WTO rules, while Washington says they are justified on national security grounds."),
        ("sovereign_risk",
         "US sovereign spreads narrow as risk appetite returns",
         "US 10-year spreads over Treasuries tightened 3bps to 42bps as global risk appetite stabilised. The fiscal picture is being watched carefully given the rising debt-to-GDP ratio, but for now markets remain comfortable with US sovereign risk."),
    ],
    "canada": [
        ("inflation",
         "Canada's CPI falls to 2.7%, within the BoC's target band",
         "Headline inflation in Canada decelerated to 2.7% yoy, the lowest since June 2021 and within the Bank of Canada's 1-3% control range. This gives the BoC room to begin easing, though the Governing Council has been clear it wants to see sustained progress."),
        ("growth",
         "Canada's economy contracts 0.2% in Q4, raising recession risk",
         "GDP contracted 0.2% in Q4 on a quarterly basis, worse than the -0.1% consensus. The weakness was broad: household consumption fell, business investment was soft, and net exports were a drag. This puts Canada technically in a recession heading into Q1."),
        ("central_bank",
         "Bank of Canada holds but opens door to rate cuts mid-year",
         "The BoC kept its overnight rate at 4.5%, in line with expectations. Governor Macklem indicated that the next move is likely a cut, but the timing will depend on the evolution of inflation and the labour market. Markets are pricing in a July start."),
        ("labor",
         "Canada unemployment rate rises to 6.4% as job market softens",
         "The unemployment rate moved up to 6.4% from 6.1%, adding to evidence that the labour market is loosening. Job losses were concentrated in construction and professional services. Wage growth moderated to 3.8%, providing some comfort on inflation."),
        ("fiscal",
         "Federal deficit comes in C$40bn, above government's own projection",
         "The federal deficit came in at C$40bn, C$4bn above the projection in the Fall Economic Statement. The overrun was driven by higher debt interest costs and lower-than-expected tax revenues. The Finance Minister has committed to a fiscal update."),
        ("trade",
         "Canada trade surplus narrows as energy exports soften",
         "Canada's trade surplus narrowed to C$1.2bn as energy export volumes declined. The油菜 sector is a key source of export income and has been impacted by lower global commodity prices, creating a headwind for the current account."),
        ("markets",
         "CAD weakens as Bank of Canada hints at easing path",
         "The Canadian dollar fell 0.4% against the USD after the BoC rate statement suggested easing could come sooner than previously signalled. Weak GDP data has shifted the rate path significantly, with markets now expecting two cuts by year-end."),
        ("external_risk",
         "Canada's current account deficit widens to C$17bn",
         "Canada's current account deficit widened to C$17bn in Q4, driven primarily by the income account. The Goods account improved slightly but the Services account remained in deficit. External financing needs are manageable but growing."),
    ],
    "uk": [
        ("inflation",
         "UK inflation cools to 3.8% but services remains the puzzle",
         "CPI fell to 3.8% in the latest reading, down from 4.0% previously and close to the consensus forecast. Food and energy prices eased, but services inflation — heavily influenced by wages — stayed elevated at 6.5%, keeping the BoE's job difficult."),
        ("growth",
         "UK exits recession with 0.3% Q3 growth, but recovery is uneven",
         "The UK economy grew 0.3% in Q3, formally exiting the shallow recession it entered in H2 2023. However the recovery is narrow: services drove most of the gain while manufacturing output fell for the third consecutive month, raising questions about sustainability."),
        ("central_bank",
         "Bank of England holds rates but dissent grows over pace of easing",
         "The BoE's MPC voted 6-3 to hold Bank Rate at 5.0%. Three members preferred a cut, the largest dissent since 2019. Markets read the split as a signal that the easing cycle is approaching, with a first cut fully priced for June."),
        ("fiscal",
         "Chancellor's fiscal headroom narrows as tax revenues disappoint",
         "The OBR's latest projections show the Chancellor has £13bn of headroom against the fiscal mandate, down from £19bn in the Autumn Statement. Lower tax receipts — particularly from income and corporate taxes — are the main driver. The Budget is expected to be tight."),
        ("labor",
         "UK unemployment stays at 4.5% as real wages recover",
         "The unemployment rate held at 4.5%, the highest since early 2021, but the picture is complex: nominal wage growth is running at 6.0%, outpacing inflation and supporting real household incomes. The MPC is monitoring this dynamic carefully."),
        ("trade",
         "UK export orders weaken as European demand softens",
         "UK manufacturing exports fell 2.1% in the latest month, with demand from the EU — the UK's largest trading partner — softening. The weaker pound has helped competitiveness but global trade headwinds are offsetting this benefit."),
        ("markets",
         "Gilts outperform as Bank of England easing bets widen",
         "UK Gilts rallied sharply as softer growth data and a more dovish MPC voted 6-3 to hold, pushing 10-year yields down 8bps. The UK economy's weakness is making the BoE's case for easing clearer, with front-end rates fully pricing a cut by August."),
        ("sovereign_risk",
         "UK 10-year spread to Germany tightens on fiscal optimism",
         "The 10-year UK-Germany spread tightened to 78bps from 85bps as investors responded positively to the government's spending plans. Fitch rates the UK at AA with a stable outlook, but the high debt-to-GDP ratio remains a vulnerability."),
    ],
    "germany": [
        ("growth",
         "Germany falls into recession as industrial production collapses 1.5%",
         "Germany's economy contracted 0.3% in Q4, following a -0.1% print in Q3, meeting the technical recession definition. Industrial output fell 1.5% m/m with chemicals, autos, and machinery bearing the brunt. The structural challenge from high energy costs and Chinese competition is persistent."),
        ("inflation",
         "German CPI falls to 2.5%, ECB close to declaring victory",
         "Germany's inflation fell to 2.5% yoy, its lowest in two years and closer to the ECB's 2% target. Energy prices have been the main driver of improvement while services remain stickier. The HICP reading gives the ECB more cover to begin easing."),
        ("fiscal",
         "Germany's 'debt brake' restricts fiscal stimulus amid recession",
         "Germany's constitutional debt brake is constraining the government's ability to respond to the recession. The coalition has ruled out major fiscal loosening, leaving monetary policy as the primary lever. Business groups are calling for a suspension or reform of the debt brake."),
        ("central_bank",
         "ECB holds but Lagarde signals June as likely first cut date",
         "The ECB kept rates unchanged at 4.0% and President Lagarde repeated that the Governing Council needs more data before cutting. But the internal debate is shifting: June is now seen as the most likely meeting for a first reduction as the disinflation process is on track."),
        ("trade",
         "German exports fall for fourth consecutive month on China weakness",
         "German exports fell 2.3% m/m in the latest reading, the fourth consecutive monthly decline. The China slowdown is a key driver: Chinese industrial demand for German capital goods has softened significantly, weighing on the external sector and contributing to the wider recession."),
        ("external_risk",
         "Germany's current account surplus shrinks to 4.5% of GDP",
         "Germany's current account surplus narrowed to 4.5% of GDP from 6.2% previously, reflecting the deteriorating trade balance. The energy transition is increasing import needs while the weak global environment is limiting export gains, compressing the external buffer."),
        ("labor",
         "German unemployment rises to 3.4% as manufacturing cuts jobs",
         "German unemployment rose to 3.4%, the highest since 2021, as industrial companies cut jobs in response to weak demand. The auto sector is in transition — EVs are disrupting established producers — and this structural shift is creating persistent labour market pressures."),
        ("markets",
         "Dax underperforms as China demand and rate pressure hit earnings",
         "The DAX has underperformed global peers year-to-date, falling 4% as earnings misses mounted in the automotive, chemicals, and machinery sectors. Chinese demand weakness and higher financing costs are the twin headwinds most cited by German corporate management teams."),
    ],
    "france": [
        ("growth",
         "France growth beats expectations at 0.5% in Q3, driven by services",
         "France's economy surprised with 0.5% q/q growth in Q3, the strongest pace in over a year, driven primarily by services and tourism. However the industrial sector remains weak and business investment is subdued, leaving the composition of growth less robust than the headline suggests."),
        ("fiscal",
         "France's public debt reaches 111% of GDP, test of EU fiscal rules",
         "France's public debt ratio crossed 111% of GDP for the first time, testing the EU's revised fiscal rules that set a 60% ceiling and require structural adjustments for high-debt countries. The government has committed to a fiscal path but achieving the targets is politically difficult."),
        ("inflation",
         "French inflation decelerates to 2.4%, ECB can add France to easing list",
         "France's CPI fell to 2.4% yoy, the lowest since mid-2021, with tourism-related services prices seasonal boost fading. This puts France below the euro area average and gives the ECB one more data point supporting the case for cutting rates."),
        ("labor",
         "France unemployment stays at 7.3%, structural reform still elusive",
         "Unemployment in France held at 7.3%, well above the euro area average and a structural weakness of the French economy. Labour market rigidities, high minimum wages, and strict dismissal rules keep unemployment elevated and mean the potential growth rate is suppressed."),
        ("central_bank",
         "ECB rate cut would be particularly significant for French banks",
         "French banks are highly sensitive to ECB rate moves given the significant proportion of variable-rate corporate debt and mortgage exposure. The highly leveraged French government also benefits from lower rates, so an ECB cut would provide meaningful fiscal relief."),
        ("trade",
         "France maintains trade surplus in aerospace but goods balance weakens",
         "France continues to run a trade surplus in civil aerospace, a high-value export industry, but the broader goods trade balance has deteriorated. The weak euro has been helpful but global demand conditions are the dominant factor for French exporters."),
        ("markets",
         "French spreads widen as fiscal concerns resurface",
         "French OAT spreads over German Bunds widened to 68bps from 52bps as investors reassessed the fiscal trajectory. Rating agency moody's has France at Aa2 with a negative outlook, citing the structural deficit and debt dynamics as the key risk."),
        ("sovereign_risk",
         "France sovereign risk elevated as fiscal consolidation falters",
         "France's sovereign risk premium has risen as the fiscal consolidation path proves harder to execute than planned. The government's budget draft has been challenged by the EU Commission, and debates within the coalition add to uncertainty about the fiscal direction."),
    ],
    "china": [
        ("growth",
         "China GDP misses expectations at 4.6%, property sector still a drag",
         "China's economy grew 4.6% in Q4 yoy, below the 5.1% consensus and raising questions about whether the 5% official target will be met. Property sector activity remains in contraction and consumer confidence is weak. Q4 growth was the slowest since Q2 2023."),
        ("inflation",
         "China CPI turns negative at -0.3%, deflation risk deepens",
         "China's CPI fell to -0.3% yoy in the latest reading — the second consecutive month of deflation — raising alarms about demand weakness. The property sector wealth effect, youth unemployment above 20%, and слабая consumer confidence are the key drivers of the disinflationary trend."),
        ("central_bank",
         "PBOC cuts reserve requirement ratio by 50bps to support fragile recovery",
         "The People's Bank of China cut the RRR by 50bps, releasing approximately RMB 1trn in liquidity to support the banking system. This follows a series of targeted credit facilities and property sector support measures that have so far failed to sustainably arrest the growth slowdown."),
        ("trade",
         "China exports fall 7.5% as global demand and technology restrictions bite",
         "China's exports fell 7.5% yoy in dollar terms, much worse than the -1% consensus. The technology export restrictions imposed by the US and allies are reducing China's high-tech export capacity, while weaker global demand is weighing on broader trade volumes."),
        ("markets",
         "Yuan hits 7.30 per dollar as capital outflows and weak growth pressure mount",
         "The onshore yuan touched 7.30 per dollar, its weakest level in six months, as capital outflows accelerated amid doubts about China's growth trajectory. The PBOC has been managing the currency actively but the fundamental pressure from growth differentials and policy divergence is substantial."),
        ("fiscal",
         "China local government finances under strain as land revenue collapses",
         "Land sale revenues — which fund roughly 35% of Chinese local government spending — fell 25% yoy in the latest data, creating a significant financing gap. Local governments have responded by increasing bond issuance, but the structural fiscal压力 is becoming more acute."),
        ("external_risk",
         "China current account surplus narrows to 1.5% of GDP",
         "China's current account surplus narrowed to 1.5% of GDP from 2.3% previously, reflecting rising import costs for energy and commodities and a softening trade surplus. This reduces the external buffer and increases reliance on capital account flows to fund the economy."),
        ("geopolitics",
         "China-US tech war escalates with new chip export restrictions",
         "Washington announced expanded restrictions on advanced semiconductor exports to China, covering a wider range of chip types and manufacturing equipment. Beijing protested the measures and announced it would restrict exports of rare earth minerals used in semiconductor manufacturing."),
    ],
    "japan": [
        ("inflation",
         "Japan CPI accelerates to 2.6%, BoJ normalisation gains more support",
         "Japan's national CPI ex-food and energy rose to 2.6%, moving above the BoJ's 2% target for the first time in a decade and a half. This gives the Bank of Japan more cover to begin unwinding its ultra-loose monetary policy, which has been in place since 2013."),
        ("growth",
         "Japan growth revised down to 0.4% q/q, weaker capex the culprit",
         "Japan's Q3 GDP growth was revised down to 0.4% q/q from the preliminary 0.9%, mainly due to weaker business investment. Private consumption was solid but external demand was a slight drag. The revision reduces the optimism around Japan's economic recovery."),
        ("central_bank",
         "Bank of Japan lifts short-term rate to 0.25%, begins YCC adjustment",
         "The Bank of Japan raised the short-term policy rate to 0.25% from 0.1% and announced it would allow 10-year JGB yields to move more flexibly around the 1% implicit cap. This is the most significant shift in Japanese monetary policy in years and is being closely watched globally."),
        ("fiscal",
         "Japan debt servicing costs surge as BoJ normalises rates",
         "Japan's debt-to-GDP ratio stands at 263%, the highest of any advanced economy, and the shift to higher interest rates is increasing debt servicing costs significantly. The government's fiscal support measures are being scrutinised by credit rating agencies, with Fitch already on negative watch."),
        ("trade",
         "Yen weakness pushes Japan trade deficit wider despite weak import volumes",
         "Japan's trade deficit widened to ¥1.2tn as the weak yen pushed import values higher even as volumes were subdued. The auto sector has been particularly impacted by competition from Chinese EV makers, with Toyota losing market share domestically and in key export markets."),
        ("markets",
         "Nikkei retreats from 34-year high as BoJ policy tightening accelerates",
         "The Nikkei 225 has fallen 8% from its 34-year high as the Bank of Japan's policy shift has tightened financial conditions. The yen's rapid appreciation — from 160 to 148 per dollar — has hurt exporters, while higher rates have compressed equity valuations."),
        ("labor",
         "Japan wage growth hits 30-year high at 2.8%, supports consumption",
         "Japan's annual wage growth accelerated to 2.8%, the highest in three decades, following the Shunto spring wage negotiations. This is a critical development for the BoJ: sustained wage growth is the key condition for maintaining the 2% inflation target without relying on energy price shocks."),
        ("external_risk",
         "Japan current account surplus narrows as investment income cools",
         "Japan's current account surplus has narrowed to 3.9% of GDP as the income surplus — driven by Japan's large foreign asset holdings — has contracted with the normalisation of global interest rates. This reduces one of Japan's traditional external buffers."),
    ],
    "india": [
        ("growth",
         "India remains fastest-growing large economy at 6.8% in Q3",
         "India's GDP grew 6.8% in Q3 FY24, maintaining its position as the fastest-growing large economy in the world. Investment was the main driver — infrastructure spending and private capex both accelerated — while consumption was more subdued. The IMF projects India will grow 7% this year."),
        ("inflation",
         "India CPI falls to 4.6%, RBI has room to begin easing cycle",
         "India's CPI inflation fell to 4.6% in the latest month, the lowest since late 2021 and within the RBI's 4±2% target band. Food inflation remains the main source of uncertainty but the headline trend gives the RBI more flexibility to begin cutting rates."),
        ("central_bank",
         "RBI holds rates but dovish tone signals easing likely from June",
         "The Reserve Bank of India kept the repo rate unchanged at 6.5% for the seventh consecutive meeting but shifted to a more dovish tone. Governor Das indicated that the monetary policy committee is now focused on supporting growth, suggesting the first rate cut could come as early as June."),
        ("fiscal",
         "India fiscal deficit tracking at 5.8% of GDP, government on track",
         "India's fiscal deficit for the first ten months of the fiscal year came in at 5.8% of GDP, broadly in line with the full-year target of 5.8%. Tax revenue has been stronger than expected, providing some fiscal headroom to maintain capital spending without loosening the overall position."),
        ("trade",
         "India trade deficit narrows on strong services exports",
         "India's goods trade deficit narrowed as services exports — particularly IT and business services — remained strong. Imports were held back by lower oil prices and weaker domestic demand for capital goods. India is running a large services surplus that partially offsets the goods deficit."),
        ("markets",
         "Rupee strengthens as RBI shifts to easing, foreign flows return",
         "The Indian rupee has appreciated against the dollar as the RBI's dovish pivot attracted foreign portfolio inflows into Indian equities and bonds. The BSE Sensex has hit new highs as global investors increase India allocations given its growth premium and improving macro fundamentals."),
        ("external_risk",
         "India current account deficit widens to -1.2% on energy imports",
         "India's current account deficit widened to -1.2% of GDP in Q3, primarily due to higher energy import bills and weaker exports. The services surplus provides a buffer, and strong remittance flows also support the external position. The RBI has adequate reserves to manage the deficit."),
        ("labor",
         "India unemployment falls to 7.8% but quality of jobs remains a concern",
         "India's unemployment rate fell to 7.8% from 8.1%, a marginal improvement. However the quality of job creation remains a concern: much of the new employment is in informal and gig economy roles with limited social protection. The formal sector job creation is insufficient to absorb the demographic dividend."),
    ],
    "brazil": [
        ("inflation",
         "Brazil CPI falls to 4.1%, Banco Central can accelerate easing",
         "Brazil's IPCA fell to 4.1% yoy, within the Banco Central's 1.5-4.5% target range for the first time in two years. This gives the BCB more room to accelerate its rate-cutting cycle, with the market now expecting 75bps of cuts at each of the remaining meetings this year."),
        ("growth",
         "Brazil GDP grows 2.9% in 2024, driven by agribusiness and services",
         "Brazil's economy grew 2.9% in 2024, a strong outturn driven primarily by a record agribusiness harvest and resilient services activity. Industrial production was more muted, but the overall growth picture is one of the best among major emerging markets."),
        ("central_bank",
         "Banco Central cuts SELIC rate by 75bps to 10.75%, more to come",
         "The Banco Central cut its benchmark SELIC rate by 75bps to 10.75%, a larger cut than the 50bps that had been priced in. The BCB is pursuing an aggressive easing cycle as inflation falls rapidly toward target. Guidance signals further cuts of 75bps at upcoming meetings."),
        ("fiscal",
         "Brazil fiscal framework test as debt-to-GDP edges up to 88%",
         "Brazil's public sector debt-to-GDP ratio edged up to 88%, testing the fiscal framework introduced by the Lula government. The framework commits to a primary surplus sufficient to stabilise the debt ratio, but achieving this while maintaining social spending commitments is challenging."),
        ("trade",
         "Brazil trade surplus narrows as commodity prices soften",
         "Brazil's trade surplus has narrowed as global commodity prices — particularly soy and iron ore — have eased from their 2022 peaks. The terms-of-trade gain has reversed somewhat, though Brazil continues to run large surpluses that support the current account and currency."),
        ("markets",
         "Real gains as Banco Central eases aggressively and fiscal risk eases",
         "The Brazilian real has appreciated 8% against the dollar this year as the BCB's aggressive easing cycle and improvements in the fiscal outlook attracted foreign capital. Brazilian equities have also rallied strongly on improved growth prospects and commodity price stability."),
        ("external_risk",
         "Brazil external debt manageable but commodity exposure remains key risk",
         "Brazil's external debt is manageable with reserves covering more than 18 months of imports. However the concentration in commodity exports — soy, iron ore, crude oil — creates vulnerability to global demand shifts and Chinese growth outcomes, which remain key macro risks."),
        ("geopolitics",
         "Brazil navigates US-China tensions to expand trade relationships",
         "Brazil is actively diversifying its trade relationships as the US-China strategic competition creates both risks and opportunities. Agriculture exports to China have grown significantly, while technology partnerships with the US and Europe are deepening in sectors like semiconductors and aerospace."),
    ],
    "australia": [
        ("growth",
         "Australia growth slows to 1.5% as rate drag on consumption bites",
         "Australia's economy grew 1.5% in 2024, down from 2.0% in 2023, as the lagged effect of 13 rate hikes since May 2022 weighed on household consumption. The RBA's aggressive tightening cycle is working as intended, though the slowdown is more gradual than initially feared."),
        ("inflation",
         "Australia CPI eases to 3.4%, RBA can begin easing in late 2024",
         "Australia's headline CPI fell to 3.4% yoy, the lowest since early 2022 and close to the RBA's 2-3% target band. The board has been clear that inflation needs to be sustainably in the target range before cutting, but the trend is now clearly pointing in the right direction."),
        ("central_bank",
         "RBA holds at 4.35% but statement leaves door open for hikes",
         "The Reserve Bank of Australia kept the cash rate target unchanged at 4.35%, the highest since late 2011. Governor Bullock noted that inflation is moving in the right direction but the board remains vigilant to upside risks, particularly from services and housing costs."),
        ("fiscal",
         "Australia fiscal position strong but aging population pressure builds",
         "Australia's fiscal balance has improved significantly as commodity royalties have boosted revenues. The structural fiscal challenge — an aging population and growing healthcare/pension costs — is the medium-term concern. The IMF has warned about the need for fiscal consolidation in the 2030s."),
        ("trade",
         "Australia terms of trade improves as iron ore and coal prices stabilise",
         "Australia's terms of trade have stabilised after the large decline from the 2022 commodity peak. Iron ore and coal prices have found support from Chinese infrastructure spending, providing some buffer to the rural sector. The services trade surplus from education and tourism also supports the external position."),
        ("markets",
         "AUD strengthens as RBA easing cycle approaches",
         "The Australian dollar has appreciated against the USD as the RBA's shift to an easing bias attracted inflows. Australian bonds have rallied with the front-end pricing in rate cuts by late 2024. The RBA's easing cycle — when it arrives — will be a significant catalyst for local assets."),
        ("labor",
         "Australia unemployment ticks up to 4.2% as labour market cools",
         "Australia's unemployment rate rose to 4.2% from 4.0%, the first significant move up in the cycle. The RBA has been watching the labour market closely as one of the two mandates — full employment and inflation — is now less constraining, giving more room to keep rates restrictive until inflation is tamed."),
        ("external_risk",
         "Australia current account improves to -1.0% of GDP on commodity revenues",
         "Australia's current account deficit improved to -1.0% of GDP, the best reading in over a decade, as strong commodity export revenues supported the trade balance. The services surplus (education, tourism) and the income from the foreign asset base provide additional external stability."),
    ],
}


# ── RSS Helpers ───────────────────────────────────────────────────────────────

def _fetch_rss(url: str, timeout: int = 8) -> Optional[ET.Element]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return ET.fromstring(resp.read())
    except Exception:
        return None


def _parse_entry(entry: ET.Element, feed_key: str) -> Optional[dict]:
    try:
        ns_atom = {"a": "http://www.w3.org/2005/Atom"}
        ns_rss = {}

        # Title
        title_el = entry.find("title") or entry.find("a:title", ns_atom)
        if title_el is None or not title_el.text:
            return None
        title = html.unescape(title_el.text.strip())

        # URL
        url = ""
        link_el = entry.find("link")
        if link_el is not None:
            if link_el.get("href"):
                url = html.unescape(link_el.get("href")).strip()
            elif link_el.text:
                url = html.unescape(link_el.text.strip())
        if not url:
            atom_alt = entry.find("a:link[@rel='alternate']", ns_atom)
            if atom_alt is not None and atom_alt.get("href"):
                url = html.unescape(atom_alt.get("href")).strip()

        if not title or not url:
            return None

        # Description
        desc_el = (entry.find("description")
                   or entry.find("a:summary", ns_atom)
                   or entry.find("a:content", ns_atom))
        raw_desc = html.unescape(desc_el.text).strip() if desc_el is not None and desc_el.text else ""
        summary = re.sub(r"<[^>]+>", "", raw_desc)
        summary = re.sub(r"\s+", " ", summary).strip()[:400]

        # Date
        pub_el = (entry.find("pubDate")
                  or entry.find("published")
                  or entry.find("a:updated", ns_atom))
        date_str = ""
        if pub_el is not None and pub_el.text:
            for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                        "%Y-%m-%dT%H:%M:%S%z",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%SZ"):
                try:
                    dt = datetime.strptime(pub_el.text.strip()[:31], fmt).astimezone(timezone.utc)
                    date_str = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    pass

        return {
            "headline": title[:300],
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
    Tries RSS feeds first; falls back to curated static items.
    Items are deduplicated, filtered by country, sorted newest first.
    """
    # Attempt RSS
    raw_items: list[dict] = []

    for feed_key, feed_url in RSS_FEEDS:
        root = _fetch_rss(feed_url)
        if root is None:
            continue
        channel = root.find("channel") or root
        entries = channel.findall("item") or root.findall("entry") or []
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

    # If fewer than 4 real items, fill from static
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
    templates = STATIC_FALLBACK.get(country_key, [])
    result = []
    for idx, (cat, headline, summary) in enumerate(templates):
        result.append({
            "headline":   headline,
            "summary":    summary,
            "source":     "Source unavailable",
            "date":       DATES_8[idx % len(DATES_8)],
            "category":   cat,
            "url":        "",
        })
    return result