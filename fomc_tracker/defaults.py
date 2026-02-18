"""Default configuration values for the FOMC Stance Tracker.

All extractable constants live here. Fork users override values
via ``local/config.py`` (see ``config.py`` for the merge logic).

Naming conventions
------------------
- UPPER_CASE  → scalar or dict that downstream code reads directly
- Dicts       → merged with local overrides (local keys added/replaced)
- Scalars     → replaced wholesale by local overrides
"""

# ── Score thresholds ─────────────────────────────────────────────────────

HAWKISH_THRESHOLD = 1.5
DOVISH_THRESHOLD = -1.5
SCORE_MIN = -5.0
SCORE_MAX = 5.0

# ── Blend weights ────────────────────────────────────────────────────────

# How much weight to give *news* vs *historical lean* when blending
NEWS_WEIGHT = 0.7
HISTORICAL_WEIGHT = 0.3

# How to combine policy and balance-sheet dimensions into an overall score
POLICY_VS_BS_WEIGHT = 0.7   # policy weight; balance sheet = 1 - this

# ── Role / influence weights (policy_signal.py) ─────────────────────────

ROLE_WEIGHTS = {
    "Chair": 3.0,
    "Vice Chair": 1.5,
    "Vice Chair for Supervision": 1.25,
    "Governor": 1.0,
    "President_voter": 1.0,
    "President_alt": 0.25,
}

# ── Implied rate-action thresholds (policy_signal.py) ────────────────────

ACTION_THRESHOLDS = [
    # (min_score, max_score, action_label, direction, magnitude_bp)
    (-5.0, -3.5, "Cut 50bp",   "easing",     50),
    (-3.5, -2.0, "Cut 25bp",   "easing",     25),
    (-2.0, -0.5, "Lean Cut",   "easing",     25),
    (-0.5,  0.5, "Hold",       "neutral",     0),
    ( 0.5,  2.0, "Lean Hike",  "tightening", 25),
    ( 2.0,  3.5, "Hike 25bp",  "tightening", 25),
    ( 3.5,  5.0, "Hike 50bp",  "tightening", 50),
]

# ── Drift detection (policy_signal.py) ───────────────────────────────────

HAWKISH_DRIFT_THRESHOLD = 0.3
DOVISH_DRIFT_THRESHOLD = -0.3

# ── FRED series (fred_data.py) ───────────────────────────────────────────

FRED_SERIES = {
    "CPIAUCSL": {
        "name": "CPI (All Urban Consumers)",
        "short_name": "CPI",
        "unit": "% YoY",
        "transform": "pct_change_year",
        "icon": "inflation",
    },
    "PCEPILFE": {
        "name": "Core PCE Price Index",
        "short_name": "Core PCE",
        "unit": "% YoY",
        "transform": "pct_change_year",
        "icon": "inflation",
    },
    "UNRATE": {
        "name": "Unemployment Rate",
        "short_name": "Unemployment",
        "unit": "%",
        "transform": "level",
        "icon": "employment",
    },
    "FEDFUNDS": {
        "name": "Effective Federal Funds Rate",
        "short_name": "Fed Funds",
        "unit": "%",
        "transform": "level",
        "icon": "rates",
    },
    "T10Y2Y": {
        "name": "10Y-2Y Treasury Spread",
        "short_name": "Yield Spread",
        "unit": "%",
        "transform": "level",
        "icon": "rates",
    },
    "PAYEMS": {
        "name": "Nonfarm Payrolls",
        "short_name": "Payrolls",
        "unit": "K jobs",
        "transform": "change",
        "icon": "employment",
    },
    "GDP": {
        "name": "Real GDP",
        "short_name": "GDP",
        "unit": "% QoQ",
        "transform": "pct_change_quarter",
        "icon": "growth",
    },
    "DFF": {
        "name": "Daily Fed Funds Rate",
        "short_name": "Daily FFR",
        "unit": "%",
        "transform": "level",
        "icon": "rates",
    },
}

FRED_CACHE_MAX_AGE_HOURS = 6
FRED_FETCH_LIMIT = 24

# ── Feed URLs (news_fetcher.py) ──────────────────────────────────────────

FED_RSS_FEEDS = [
    "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "https://www.federalreserve.gov/feeds/press_speech.xml",
    "https://www.federalreserve.gov/feeds/press_testimony.xml",
]

BIS_SPEECHES_RSS = "https://www.bis.org/doclist/cbspeeches.rss?paging_length=50"

REGIONAL_FED_BLOGS = {
    "FRB New York": [
        "https://libertystreeteconomics.newyorkfed.org/feed/",
    ],
    "FRB San Francisco": [
        "https://www.frbsf.org/research-and-insights/data/fed-views/rss.xml",
    ],
    "FRB Atlanta": [
        "https://www.atlantafed.org/rss/macroblog",
    ],
    "FRB Cleveland": [
        "https://www.clevelandfed.org/rss/forefront",
    ],
    "FRB Richmond": [
        "https://www.richmondfed.org/rss/feeds/research",
    ],
    "FRB Chicago": [
        "https://www.chicagofed.org/rss",
    ],
    "FRB St. Louis": [
        "https://research.stlouisfed.org/publications/feeds/",
    ],
    "FRB Dallas": [
        "https://www.dallasfed.org/rss",
    ],
    "FRB Minneapolis": [
        "https://www.minneapolisfed.org/rss",
    ],
    "FRB Kansas City": [
        "https://www.kansascityfed.org/rss/",
    ],
    "FRB Boston": [
        "https://www.bostonfed.org/rss",
    ],
    "FRB Philadelphia": [
        "https://www.philadelphiafed.org/rss",
    ],
}

# ── Rate limiting (news_fetcher.py) ──────────────────────────────────────

RATE_LIMIT_SECONDS = 1.5

# ── Fetch limits ─────────────────────────────────────────────────────────

DDGS_MAX_RESULTS = 10
FED_SPEECHES_MAX_RESULTS = 5
FOMC_MINUTES_MAX_RESULTS = 3
REGIONAL_BLOG_MAX_RESULTS = 5

# ── Evidence collection (fetch_data.py) ──────────────────────────────────

MAX_EVIDENCE_ITEMS = 8

# ── Quote extraction context (stance_classifier.py) ──────────────────────

QUOTE_CONTEXT_CHARS = 120

# ── UI colors ────────────────────────────────────────────────────────────

COLORS = {
    "hawk": "#f87171",
    "dove": "#60a5fa",
    "neutral": "#64748b",
    "accent": "#fbbf24",
    "bg": "rgba(0,0,0,0)",
    "grid": "rgba(148,163,184,0.06)",
    "font": "#e2e8f0",
    "font_dim": "#94a3b8",
}
