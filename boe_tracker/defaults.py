"""Default configuration values for the BOE MPC Stance Tracker.

All extractable constants live here. Fork users override values
via ``local/boe_config.py`` (see ``config.py`` for the merge logic).

Naming conventions
------------------
- UPPER_CASE  -> scalar or dict that downstream code reads directly
- Dicts       -> merged with local overrides (local keys added/replaced)
- Scalars     -> replaced wholesale by local overrides
"""

# -- Score thresholds (same as FOMC) ----------------------------------------

HAWKISH_THRESHOLD = 1.5
DOVISH_THRESHOLD = -1.5
SCORE_MIN = -5.0
SCORE_MAX = 5.0

# -- Blend weights -----------------------------------------------------------

NEWS_WEIGHT = 0.7
HISTORICAL_WEIGHT = 0.3

POLICY_VS_BS_WEIGHT = 0.7  # policy weight; balance sheet = 1 - this

# -- Role / influence weights ------------------------------------------------

ROLE_WEIGHTS = {
    "Governor": 3.0,
    "Deputy Governor": 1.5,
    "Chief Economist": 1.25,
    "External Member": 1.0,
}

# -- Implied rate-action thresholds -------------------------------------------

ACTION_THRESHOLDS = [
    # (min_score, max_score, action_label, direction, magnitude_bp)
    (-5.0, -3.5, "Cut 50bp", "easing", 50),
    (-3.5, -2.0, "Cut 25bp", "easing", 25),
    (-2.0, -0.5, "Lean Cut", "easing", 25),
    (-0.5,  0.5, "Hold", "neutral", 0),
    ( 0.5,  2.0, "Lean Hike", "tightening", 25),
    ( 2.0,  3.5, "Hike 25bp", "tightening", 25),
    ( 3.5,  5.0, "Hike 50bp", "tightening", 50),
]

# -- Drift detection ----------------------------------------------------------

HAWKISH_DRIFT_THRESHOLD = 0.3
DOVISH_DRIFT_THRESHOLD = -0.3

# -- BOE data source URLs ----------------------------------------------------

BOE_SPEECHES_RSS = "https://www.bankofengland.co.uk/rss/speeches"
BOE_NEWS_RSS = "https://www.bankofengland.co.uk/rss/news"
MPC_MINUTES_URL = "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes"
TREASURY_COMMITTEE_URL = (
    "https://committees.parliament.uk/committee/158/"
    "treasury-committee/publications/oral-evidence/"
)

# -- BOE Statistics series (IADB) --------------------------------------------

BOE_STATS_SERIES = {
    "IUDBEDR": {
        "name": "Bank Rate",
        "short_name": "Bank Rate",
        "unit": "%",
        "transform": "level",
        "icon": "rates",
    },
    "D7BT": {
        "name": "CPI Annual Rate",
        "short_name": "CPI",
        "unit": "% YoY",
        "transform": "level",
        "icon": "inflation",
    },
    "MGSX": {
        "name": "Unemployment Rate (16+)",
        "short_name": "Unemployment",
        "unit": "%",
        "transform": "level",
        "icon": "employment",
    },
    "IHYQ": {
        "name": "Real GDP Quarterly Growth",
        "short_name": "GDP",
        "unit": "% QoQ",
        "transform": "level",
        "icon": "growth",
    },
}

BOE_STATS_CACHE_MAX_AGE_HOURS = 6

# -- Rate limiting ------------------------------------------------------------

RATE_LIMIT_SECONDS = 1.5

# -- Fetch limits -------------------------------------------------------------

DDGS_MAX_RESULTS = 10
BOE_SPEECHES_MAX_RESULTS = 5
MPC_MINUTES_MAX_RESULTS = 3

# -- Evidence collection ------------------------------------------------------

MAX_EVIDENCE_ITEMS = 8

# -- Quote extraction context --------------------------------------------------

QUOTE_CONTEXT_CHARS = 120

# -- UI colors ----------------------------------------------------------------

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

# -- BOE-specific hawkish/dovish keywords (augment FOMC classifier) -----------

BOE_HAWKISH_TERMS = {
    "bank rate increase": 1.0,
    "raise bank rate": 1.0,
    "tighten policy": 0.8,
    "gilt sales": 0.8,
    "sell gilts": 0.7,
    "reduce balance sheet": 0.8,
    "above target inflation": 0.7,
    "inflation persistence": 0.7,
    "second-round effects": 0.6,
    "embedded inflation": 0.7,
    "wage-price spiral": 0.8,
    "services inflation": 0.6,
    "domestic price pressures": 0.6,
    "further tightening": 0.9,
    "insufficiently restrictive": 0.7,
}

BOE_DOVISH_TERMS = {
    "bank rate cut": 1.0,
    "cut bank rate": 1.0,
    "reduce bank rate": 0.9,
    "lower bank rate": 0.8,
    "quantitative easing": 0.9,
    "gilt purchases": 0.8,
    "buy gilts": 0.7,
    "support growth": 0.6,
    "below target": 0.5,
    "demand weakness": 0.6,
    "economic slack": 0.6,
    "output gap": 0.5,
    "disinflationary": 0.7,
    "restrictive stance": 0.5,
    "scope to ease": 0.8,
    "gradual removal": 0.6,
}
