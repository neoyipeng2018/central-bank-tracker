"""Local configuration overrides.

Copy this file to ``local/config.py`` and uncomment the values you want
to customise.  Dict values are **merged** with defaults (your keys add to
or replace default keys); scalar values **replace** the default wholesale.

See ``fomc_tracker/defaults.py`` for the full list of available settings.
"""

# ── Score thresholds ─────────────────────────────────────────────────────
# HAWKISH_THRESHOLD = 2.0
# DOVISH_THRESHOLD = -2.0

# ── Blend weights ────────────────────────────────────────────────────────
# NEWS_WEIGHT = 0.8
# HISTORICAL_WEIGHT = 0.2
# POLICY_VS_BS_WEIGHT = 0.6

# ── Role weights ─────────────────────────────────────────────────────────
# ROLE_WEIGHTS = {
#     "Chair": 4.0,            # increase Chair influence
#     "President_alt": 0.10,   # further reduce non-voters
# }

# ── FRED series (add or replace indicators) ──────────────────────────────
# FRED_SERIES = {
#     "WALCL": {
#         "name": "Fed Balance Sheet",
#         "short_name": "Balance Sheet",
#         "unit": "$T",
#         "transform": "level",
#         "icon": "rates",
#     },
# }

# ── Feed URLs (add extra feeds) ─────────────────────────────────────────
# FED_RSS_FEEDS = [
#     "https://your-company.com/feeds/custom.xml",
# ]

# ── UI colors ────────────────────────────────────────────────────────────
# COLORS = {
#     "hawk": "#ef4444",
#     "dove": "#3b82f6",
# }
