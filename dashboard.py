#!/usr/bin/env python3
"""FOMC Participant Stance Tracker - Interactive Streamlit Dashboard."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

from fomc_tracker.participants import PARTICIPANTS, get_voters, get_alternates
from fomc_tracker.historical_data import load_history, get_latest_stance
from fomc_tracker.meeting_calendar import (
    get_next_meeting,
    get_previous_meeting,
    days_until_next_meeting,
    is_blackout_period,
    get_current_rate,
    get_meetings_in_range,
)
from fomc_tracker.policy_signal import (
    compute_weighted_signal,
    implied_rate_action,
    compute_meeting_drift,
    signal_vs_decisions,
)
from fomc_tracker import fred_data

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FOMC Stance Tracker",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Seal_of_the_United_States_Federal_Reserve_System.svg/240px-Seal_of_the_United_States_Federal_Reserve_System.svg.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main .block-container {
        padding: 2.5rem 2rem 3rem 2rem;
        max-width: 1280px;
    }
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* ── Hero Header ────────────────────────────────── */
    .hero {
        padding: 2rem 0 1rem 0;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin: 0;
        background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #64748b;
        margin: 0.6rem 0 0 0;
        font-weight: 400;
        line-height: 1.5;
    }
    .hero-date {
        display: inline-block;
        margin-top: 0.8rem;
        padding: 0.3rem 0.8rem;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 20px;
        color: #818cf8;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    /* ── Metric Cards ───────────────────────────────── */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0 2rem 0;
    }
    .m-card {
        flex: 1;
        background: linear-gradient(145deg, rgba(15,23,42,0.6) 0%, rgba(30,41,59,0.4) 100%);
        border: 1px solid rgba(148,163,184,0.08);
        border-radius: 16px;
        padding: 1.4rem 1rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: border-color 0.2s;
    }
    .m-card:hover { border-color: rgba(148,163,184,0.2); }
    .m-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #64748b;
        margin: 0 0 0.5rem 0;
    }
    .m-value {
        font-size: 2.6rem;
        font-weight: 800;
        margin: 0;
        line-height: 1;
    }
    .m-sub {
        font-size: 0.72rem;
        color: #475569;
        margin: 0.4rem 0 0 0;
        font-weight: 500;
    }
    .m-hawk .m-value { color: #f87171; }
    .m-neut .m-value { color: #94a3b8; }
    .m-dove .m-value { color: #60a5fa; }
    .m-bal .m-value { color: #fbbf24; }
    .m-avg .m-value { color: #a78bfa; font-size: 2.2rem; }

    /* ── Section Headers ────────────────────────────── */
    .section-hdr {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0 0 0.15rem 0;
        color: #f1f5f9;
    }
    .section-sub {
        font-size: 0.82rem;
        color: #64748b;
        margin: 0 0 1.2rem 0;
        font-weight: 400;
    }
    .divider {
        border: none;
        border-top: 1px solid rgba(148,163,184,0.08);
        margin: 2.5rem 0;
    }

    /* ── Sidebar ────────────────────────────────────── */
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
    .sidebar-brand {
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #f1f5f9;
        margin: 0 0 0.3rem 0;
    }
    .sidebar-desc {
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.5;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.35rem 0;
        font-size: 0.82rem;
        color: #94a3b8;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 3px;
        flex-shrink: 0;
    }

    /* ── Download row ───────────────────────────────── */
    .dl-row {
        display: flex;
        gap: 0.75rem;
        margin: 0.5rem 0 0 0;
    }

    /* ── Evidence Cards ─────────────────────────────── */
    .ev-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.5) 0%, rgba(30,41,59,0.3) 100%);
        border: 1px solid rgba(148,163,184,0.08);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .ev-card:hover { border-color: rgba(148,163,184,0.18); }
    .ev-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 0 0 0.3rem 0;
        line-height: 1.4;
    }
    .ev-title a {
        color: #818cf8;
        text-decoration: none;
    }
    .ev-title a:hover { text-decoration: underline; }
    .ev-quote {
        font-size: 0.8rem;
        color: #94a3b8;
        font-style: italic;
        margin: 0.4rem 0;
        padding-left: 0.8rem;
        border-left: 2px solid rgba(148,163,184,0.15);
        line-height: 1.5;
    }
    .ev-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-top: 0.4rem;
    }
    .ev-tag {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .ev-tag-hawk {
        background: rgba(248,113,113,0.12);
        color: #f87171;
        border: 1px solid rgba(248,113,113,0.2);
    }
    .ev-tag-dove {
        background: rgba(96,165,250,0.12);
        color: #60a5fa;
        border: 1px solid rgba(96,165,250,0.2);
    }
    .ev-tag-src {
        background: rgba(148,163,184,0.1);
        color: #94a3b8;
        border: 1px solid rgba(148,163,184,0.15);
    }
    .ev-tag-dim {
        background: rgba(167,139,250,0.12);
        color: #a78bfa;
        border: 1px solid rgba(167,139,250,0.2);
    }

    /* ── Policy Signal Panel ──────────────────────────── */
    .signal-panel {
        background: linear-gradient(145deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.5) 100%);
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 20px;
        padding: 2rem 2.2rem;
        margin: 0 0 1rem 0;
    }
    .signal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1.2rem;
    }
    .signal-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .signal-title-sub {
        font-size: 0.78rem;
        color: #64748b;
        margin: 0.2rem 0 0 0;
    }
    .signal-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .signal-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .signal-cell {
        background: rgba(15,23,42,0.5);
        border: 1px solid rgba(148,163,184,0.06);
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
    }
    .signal-cell-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #64748b;
        margin: 0 0 0.5rem 0;
    }
    .signal-cell-value {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
    }
    .signal-cell-sub {
        font-size: 0.7rem;
        color: #475569;
        margin: 0.3rem 0 0 0;
        font-weight: 500;
    }
    .signal-meeting-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0 0 0;
    }
    .signal-meeting-card {
        flex: 1;
        background: rgba(15,23,42,0.4);
        border: 1px solid rgba(148,163,184,0.06);
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }
    .signal-meeting-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin: 0 0 0.4rem 0;
    }
    .signal-meeting-val {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 0;
    }
    .signal-meeting-note {
        font-size: 0.72rem;
        color: #475569;
        margin: 0.25rem 0 0 0;
    }

    /* ── Footer ─────────────────────────────────────── */
    .foot {
        text-align: center;
        color: #475569;
        font-size: 0.75rem;
        padding: 1.5rem 0 0.5rem 0;
        line-height: 1.7;
    }
    .foot a { color: #818cf8; text-decoration: none; }
    .foot a:hover { text-decoration: underline; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Color Palette ──────────────────────────────────────────────────────────
HAWK = "#f87171"
DOVE = "#60a5fa"
NEUTRAL_C = "#64748b"
ACCENT = "#fbbf24"
BG = "rgba(0,0,0,0)"
GRID = "rgba(148,163,184,0.06)"
FONT = "#e2e8f0"
FONT_DIM = "#94a3b8"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family="Inter, -apple-system, sans-serif", color=FONT, size=12),
)

SOURCE_LABELS = {
    "duckduckgo": "News",
    "fed_rss": "Fed RSS",
    "bis_speeches": "BIS Speech",
    "fed_speeches": "Fed Speech",
    "fomc_minutes": "FOMC Statement",
    "regional_fed_blog": "Regional Fed",
}

DIM_LABELS = {
    "policy": "Policy",
    "balance_sheet": "Bal. Sheet",
}


def render_evidence_panel(name: str, history_data: dict, date: str | None = None):
    """Render evidence cards for a participant. If date is given, show that entry; otherwise latest."""
    entries = history_data.get(name, [])
    if not entries:
        st.caption(f"No history data for {name}.")
        return

    if date:
        entry = next((e for e in entries if e["date"] == date), None)
        if not entry:
            entry = entries[-1]
    else:
        entry = entries[-1]

    sc = entry.get("score", 0)
    stance_lbl = score_label(sc)
    stance_clr = score_color(sc)

    st.markdown(
        f'<div style="background:linear-gradient(145deg,rgba(15,23,42,0.7),rgba(30,41,59,0.5));'
        f'border:1px solid {stance_clr}40;border-radius:16px;padding:1.5rem 1.8rem;margin:1rem 0 0.5rem 0">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem">'
        f'<span style="font-size:1.15rem;font-weight:700;color:#f1f5f9">{name}</span>'
        f'<span style="font-size:0.8rem;padding:0.25rem 0.7rem;border-radius:20px;font-weight:600;'
        f'background:{stance_clr}18;color:{stance_clr};border:1px solid {stance_clr}30">'
        f'{stance_lbl} &nbsp; {sc:+.3f}</span>'
        f'</div>'
        f'<p style="font-size:0.78rem;color:#64748b;margin:0">{entry.get("date", "")}'
        f' &nbsp;&bull;&nbsp; Source: {entry.get("source", "n/a")}'
        f' &nbsp;&bull;&nbsp; Policy: {entry.get("policy_score", 0):+.2f} &nbsp;|&nbsp; '
        f'Balance Sheet: {entry.get("balance_sheet_score", 0):+.2f}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    ev_list = entry.get("evidence", [])
    if ev_list:
        for ev in ev_list:
            ev_title = ev.get("title", "Untitled")
            ev_url = ev.get("url", "")
            ev_quote = ev.get("quote", "")
            ev_kws = ev.get("keywords", [])
            ev_dirs = ev.get("directions", [])
            ev_dims = ev.get("dimensions", ["policy"] * len(ev_kws))
            ev_src = SOURCE_LABELS.get(ev.get("source_type", ""), ev.get("source_type", ""))
            ev_score = ev.get("score", 0)

            title_html = f'<a href="{ev_url}" target="_blank">{ev_title}</a>' if ev_url else ev_title
            quote_html = f'<p class="ev-quote">"{ev_quote}"</p>' if ev_quote else ""

            tags_html = ""
            for kw, direction, dim in zip(ev_kws, ev_dirs, ev_dims):
                tag_cls = "ev-tag-hawk" if direction == "hawkish" else "ev-tag-dove"
                dim_label = DIM_LABELS.get(dim, dim)
                tags_html += f'<span class="ev-tag {tag_cls}">{kw}</span>'
                tags_html += f'<span class="ev-tag ev-tag-dim">{dim_label}</span>'
            if ev_src:
                tags_html += f'<span class="ev-tag ev-tag-src">{ev_src}</span>'
            ev_score_clr = score_color(ev_score)
            tags_html += f'<span class="ev-tag" style="background:{ev_score_clr}18;color:{ev_score_clr};border:1px solid {ev_score_clr}30">{ev_score:+.1f}</span>'

            st.markdown(
                f'<div class="ev-card">'
                f'<p class="ev-title">{title_html}</p>'
                f'{quote_html}'
                f'<div class="ev-tags">{tags_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        source = entry.get("source", "")
        if source == "seed":
            st.caption("This is a seed/baseline data point — no news evidence available.")
        else:
            st.caption("No evidence articles stored for this data point.")


def score_color(s: float) -> str:
    if s > 1.5:
        return HAWK
    if s < -1.5:
        return DOVE
    return NEUTRAL_C


def score_label(s: float) -> str:
    if s > 1.5:
        return "Hawkish"
    if s < -1.5:
        return "Dovish"
    return "Neutral"


def last_name(full: str) -> str:
    return full.split()[-1]


# ── Stance dimension config ───────────────────────────────────────────────
DIMENSION_CONFIG = {
    "Overall": {"score_key": "score", "label_key": "label"},
    "Policy (Rates)": {"score_key": "policy_score", "label_key": "policy_label"},
    "Balance Sheet (QT/QE)": {"score_key": "balance_sheet_score", "label_key": "balance_sheet_label"},
}

# ── Load Data ──────────────────────────────────────────────────────────────
history = load_history()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-brand">FOMC Stance Tracker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sidebar-desc">Hawkish / dovish classification of Federal Reserve officials '
        "based on recent news, speeches, and public statements.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("**Stance Dimension**")
    stance_view = st.radio(
        "Select dimension",
        list(DIMENSION_CONFIG.keys()),
        index=0,
        label_visibility="collapsed",
    )
    dim_cfg = DIMENSION_CONFIG[stance_view]
    score_key = dim_cfg["score_key"]

    st.markdown("---")
    st.markdown("**Panels**")
    show_policy_signal = st.checkbox("Show Policy Signal", value=False)

    st.markdown("---")
    st.markdown("**Filters**")
    show_voters = st.checkbox("Voting members only", value=False)
    show_govs = st.checkbox("Governors only", value=False)

    st.markdown("---")
    st.markdown("**Legend**")
    st.markdown(
        f'<div class="legend-item"><div class="legend-dot" style="background:{HAWK}"></div>Hawkish (&gt; +1.5)</div>'
        f'<div class="legend-item"><div class="legend-dot" style="background:{NEUTRAL_C}"></div>Neutral (-1.5 to +1.5)</div>'
        f'<div class="legend-item"><div class="legend-dot" style="background:{DOVE}"></div>Dovish (&lt; -1.5)</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        '<p class="sidebar-desc">Scores range from <b>-5.0</b> (very dovish) '
        'to <b>+5.0</b> (very hawkish). Classification uses weighted keyword '
        "matching on news headlines, Fed speeches, and BIS central banker speeches.</p>",
        unsafe_allow_html=True,
    )

# ── Build DataFrame ───────────────────────────────────────────────────────
rows = []
for p in PARTICIPANTS:
    latest = get_latest_stance(p.name)
    sc = latest.get(score_key, latest.get("score", p.historical_lean)) if latest else p.historical_lean
    # Also grab all dimension scores for the 2D scatter
    sc_overall = latest.get("score", p.historical_lean) if latest else p.historical_lean
    sc_policy = latest.get("policy_score", sc_overall) if latest else p.historical_lean
    sc_bs = latest.get("balance_sheet_score", 0.0) if latest else p.historical_balance_sheet_lean
    rows.append(
        dict(
            name=p.name,
            short=last_name(p.name),
            inst=p.institution,
            title=p.title,
            voter=p.is_voter_2026,
            gov=p.is_governor,
            score=sc,
            label=score_label(sc),
            overall_score=sc_overall,
            policy_score=sc_policy,
            balance_sheet_score=sc_bs,
        )
    )

df = pd.DataFrame(rows).sort_values("score", ascending=True).reset_index(drop=True)
hawks = df[df.label == "Hawkish"]
neutrals = df[df.label == "Neutral"]
doves = df[df.label == "Dovish"]

avg_score = df["score"].mean()
voter_avg = df[df.voter]["score"].mean()

filtered = df.copy()
if show_voters:
    filtered = filtered[filtered.voter]
if show_govs:
    filtered = filtered[filtered.gov]

# ── Hero Header ────────────────────────────────────────────────────────────
dim_suffix = f" — {stance_view}" if stance_view != "Overall" else ""
st.markdown(
    f"""<div class="hero">
        <p class="hero-title">FOMC Participant<br>Stance Tracker</p>
        <p class="hero-sub">Real-time hawkish / dovish classification of Federal Reserve officials
        based on recent news, speeches, and public statements.</p>
        <span class="hero-date">Last updated {datetime.now().strftime('%B %d, %Y')}{dim_suffix}</span>
    </div>""",
    unsafe_allow_html=True,
)

# ── Metric Cards ───────────────────────────────────────────────────────────
hawk_pct = f"{len(hawks)/len(df)*100:.0f}%"
dove_pct = f"{len(doves)/len(df)*100:.0f}%"
balance = len(hawks) - len(doves)
bal_str = f"+{balance}" if balance > 0 else str(balance)

st.markdown(
    f"""<div class="metric-row">
        <div class="m-card m-hawk">
            <p class="m-label">Hawkish</p>
            <p class="m-value">{len(hawks)}</p>
            <p class="m-sub">{hawk_pct} of committee</p>
        </div>
        <div class="m-card m-neut">
            <p class="m-label">Neutral</p>
            <p class="m-value">{len(neutrals)}</p>
            <p class="m-sub">{len(df) - len(hawks) - len(doves) - len(neutrals) + len(neutrals)} centrist</p>
        </div>
        <div class="m-card m-dove">
            <p class="m-label">Dovish</p>
            <p class="m-value">{len(doves)}</p>
            <p class="m-sub">{dove_pct} of committee</p>
        </div>
        <div class="m-card m-bal">
            <p class="m-label">Hawk-Dove Balance</p>
            <p class="m-value">{bal_str}</p>
            <p class="m-sub">{"Hawks outnumber" if balance > 0 else "Doves outnumber" if balance < 0 else "Evenly split"}</p>
        </div>
        <div class="m-card m-avg">
            <p class="m-label">Committee Avg</p>
            <p class="m-value">{avg_score:+.2f}</p>
            <p class="m-sub">{score_label(avg_score).lower()} lean</p>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════
# Policy Signal Panel
# ══════════════════════════════════════════════════════════════════════════
if show_policy_signal:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    _signal = compute_weighted_signal(score_key)
    _action = implied_rate_action(_signal["weighted_score"])
    _drift = compute_meeting_drift(score_key)
    _next_mtg = get_next_meeting()
    _prev_mtg = get_previous_meeting()
    _days_until = days_until_next_meeting()
    _blackout = is_blackout_period()
    _current_rate = get_current_rate()

    # Action color
    _act_colors = {
        "easing": ("#60a5fa", "rgba(96,165,250,0.15)", "rgba(96,165,250,0.3)"),
        "tightening": ("#f87171", "rgba(248,113,113,0.15)", "rgba(248,113,113,0.3)"),
        "neutral": ("#fbbf24", "rgba(251,191,36,0.15)", "rgba(251,191,36,0.3)"),
    }
    _act_clr, _act_bg, _act_border = _act_colors.get(_action["direction"], _act_colors["neutral"])

    # Drift arrow
    _drift_str = ""
    if _drift:
        _d = _drift["drift"]
        if _d > 0:
            _drift_arrow = "&#9650;"  # ▲
            _drift_clr = HAWK
        elif _d < 0:
            _drift_arrow = "&#9660;"  # ▼
            _drift_clr = DOVE
        else:
            _drift_arrow = "&#9654;"  # ▶
            _drift_clr = NEUTRAL_C
        _drift_str = f'<span style="color:{_drift_clr};font-weight:700">{_drift_arrow} {_d:+.2f}</span>'

    # Blackout badge
    _blackout_html = ""
    if _blackout:
        _blackout_html = (
            '<span class="signal-badge" style="background:rgba(239,68,68,0.15);'
            'color:#ef4444;border:1px solid rgba(239,68,68,0.3);margin-left:0.8rem">'
            'Blackout Period</span>'
        )

    # Meeting countdown text
    _countdown_html = ""
    if _days_until is not None and _next_mtg:
        _mtg_date_str = _next_mtg.end_date.strftime("%B %d, %Y")
        if _days_until == 0:
            _countdown_html = f'<span style="color:#fbbf24;font-weight:700">Decision Day</span> &mdash; {_mtg_date_str}'
        elif _days_until <= 7:
            _countdown_html = f'<span style="color:#f87171;font-weight:700">{_days_until}d</span> to {_mtg_date_str}'
        else:
            _countdown_html = f'<span style="color:#e2e8f0;font-weight:700">{_days_until}d</span> to {_mtg_date_str}'

    # Rate range string
    _rate_str = ""
    if _current_rate:
        _rate_str = f"{_current_rate[0]:.2f}% &ndash; {_current_rate[1]:.2f}%"

    # Projected rate string
    _proj_str = ""
    if _action["projected_rate"]:
        _proj_str = f"{_action['projected_rate'][0]:.2f}% &ndash; {_action['projected_rate'][1]:.2f}%"
    elif _action["action"] == "Hold" and _rate_str:
        _proj_str = _rate_str

    # Build signal panel HTML in parts to avoid Streamlit rendering limits
    _prev_decision_str = _prev_mtg.decision.upper() if _prev_mtg and _prev_mtg.decision else "N/A"
    _prev_date_str = _prev_mtg.end_date.strftime("%b %d, %Y") if _prev_mtg else ""
    _prev_note_str = _prev_mtg.statement_note if _prev_mtg else ""
    _proj_note = f"Based on {_action['action'].lower()} from current {_rate_str}" if _proj_str and _rate_str else ""
    _voter_vs = "Voters more hawkish" if _signal["voter_average"] > _signal["simple_average"] + 0.1 else (
        "Voters more dovish" if _signal["voter_average"] < _signal["simple_average"] - 0.1 else "Closely aligned")
    _drift_val = _drift_str if _drift_str else '<span style="color:#64748b">N/A</span>'
    _drift_dir = _drift["drift_direction"] if _drift else ""
    _sig_clr = score_color(_signal["weighted_score"])
    _sig_title = f"Policy Signal — {stance_view}" if stance_view != "Overall" else "Policy Signal"
    _rate_sub = f"{_rate_str} current" if _rate_str else ""

    _signal_html = (
        f'<div class="signal-panel">'
        f'<div class="signal-header"><div>'
        f'<p class="signal-title">{_sig_title}</p>'
        f'<p class="signal-title-sub">Vote-weighted committee stance with implied rate action</p>'
        f'</div><div>'
        f'<span class="signal-badge" style="background:{_act_bg};color:{_act_clr};border:1px solid {_act_border}">{_action["action"]}</span>'
        f'{_blackout_html}'
        f'</div></div>'
        f'<div class="signal-grid">'
        f'<div class="signal-cell">'
        f'<p class="signal-cell-label">Weighted Signal</p>'
        f'<p class="signal-cell-value" style="color:{_sig_clr}">{_signal["weighted_score"]:+.2f}</p>'
        f'<p class="signal-cell-sub">Chair 3x, VC 1.5x, voters 1x</p></div>'
        f'<div class="signal-cell">'
        f'<p class="signal-cell-label">Implied Action</p>'
        f'<p class="signal-cell-value" style="color:{_act_clr};font-size:1.4rem">{_action["action"]}</p>'
        f'<p class="signal-cell-sub">{_action["confidence"]} confidence</p></div>'
        f'<div class="signal-cell">'
        f'<p class="signal-cell-label">Next Meeting</p>'
        f'<p class="signal-cell-value" style="color:#e2e8f0;font-size:1.4rem">{_countdown_html}</p>'
        f'<p class="signal-cell-sub">{_rate_sub}</p></div>'
        f'<div class="signal-cell">'
        f'<p class="signal-cell-label">Since Last Meeting</p>'
        f'<p class="signal-cell-value" style="font-size:1.4rem">{_drift_val}</p>'
        f'<p class="signal-cell-sub">{_drift_dir}</p></div>'
        f'</div></div>'
    )
    st.markdown(_signal_html, unsafe_allow_html=True)

    # Meeting context row (separate markdown call for reliability)
    _meeting_html = (
        f'<div class="signal-meeting-row">'
        f'<div class="signal-meeting-card">'
        f'<p class="signal-meeting-label">Last Decision</p>'
        f'<p class="signal-meeting-val">{_prev_decision_str} &mdash; {_prev_date_str}</p>'
        f'<p class="signal-meeting-note">{_prev_note_str}</p></div>'
        f'<div class="signal-meeting-card">'
        f'<p class="signal-meeting-label">Projected Rate (if acted)</p>'
        f'<p class="signal-meeting-val">{_proj_str if _proj_str else "N/A"}</p>'
        f'<p class="signal-meeting-note">{_proj_note}</p></div>'
        f'<div class="signal-meeting-card">'
        f'<p class="signal-meeting-label">Voter Avg vs Committee</p>'
        f'<p class="signal-meeting-val">{_signal["voter_average"]:+.2f}'
        f' <span style="color:#64748b;font-size:0.8rem">vs</span> '
        f'{_signal["simple_average"]:+.2f}</p>'
        f'<p class="signal-meeting-note">{_voter_vs}</p></div>'
        f'</div>'
    )
    st.markdown(_meeting_html, unsafe_allow_html=True)

    # ── Signal vs Decisions mini-table ────────────────────────────────────
    _hist_signals = signal_vs_decisions(score_key, n_meetings=6)
    if _hist_signals:
        st.markdown(
            '<p class="section-sub" style="margin-top:1rem">Historical signal accuracy: '
            'weighted stance at each meeting vs actual decision</p>',
            unsafe_allow_html=True,
        )
        _match_count = sum(1 for s in _hist_signals if s["match"])
        _total_count = len(_hist_signals)

        _hist_html = '<div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.5rem">'
        for s in _hist_signals:
            _s_clr = "#22c55e" if s["match"] else "#ef4444"
            _s_icon = "&#10003;" if s["match"] else "&#10007;"
            _s_date = datetime.strptime(s["meeting_date"], "%Y-%m-%d").strftime("%b '%y")
            _hist_html += (
                f'<div style="background:rgba(15,23,42,0.5);border:1px solid {_s_clr}30;'
                f'border-radius:10px;padding:0.5rem 0.7rem;text-align:center;min-width:80px">'
                f'<div style="font-size:0.65rem;color:#64748b;letter-spacing:0.5px">{_s_date}</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:#e2e8f0;margin:0.15rem 0">{s["decision"] or "?"}</div>'
                f'<div style="font-size:0.7rem;color:#94a3b8">Signal: {s["signal_score"]:+.1f}</div>'
                f'<div style="font-size:0.7rem;color:{_s_clr};font-weight:600">{_s_icon} {s["implied_action"]}</div>'
                f'</div>'
            )
        _hist_html += '</div>'
        _hist_html += (
            f'<div style="font-size:0.75rem;color:#64748b">'
            f'Direction match: <span style="color:#e2e8f0;font-weight:600">{_match_count}/{_total_count}</span>'
            f' ({_match_count/_total_count*100:.0f}%)</div>'
        )
        st.markdown(_hist_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# Economic Context Panel (FRED)
# ══════════════════════════════════════════════════════════════════════════
if fred_data.is_available():
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    _fred = fred_data.fetch_and_cache()
    if _fred:
        st.markdown('<p class="section-hdr">Economic Context</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-sub">Key macro indicators from FRED &mdash; context for interpreting stance shifts</p>',
            unsafe_allow_html=True,
        )

        # Pick the 4 headline indicators for metric cards
        _headline_ids = ["CPIAUCSL", "PCEPILFE", "UNRATE", "FEDFUNDS"]
        _fred_cards_html = '<div class="metric-row">'
        for _sid in _headline_ids:
            _ind = _fred.get(_sid)
            if not _ind or _ind.get("latest") is None:
                continue
            _val = _ind["latest"]
            _change = _ind.get("change")
            _unit = _ind.get("unit", "")
            _label = _ind.get("short_name", _sid)
            _last_date = _ind.get("last_date", "")

            # Color logic: inflation rising = red, falling = green; unemployment inverse
            if _change is not None:
                if _ind.get("icon") == "inflation":
                    _chg_clr = "#f87171" if _change > 0 else "#34d399"
                    _arrow = "&#9650;" if _change > 0 else "&#9660;"
                elif _ind.get("icon") == "employment":
                    _chg_clr = "#f87171" if _change > 0 else "#34d399"
                    _arrow = "&#9650;" if _change > 0 else "&#9660;"
                else:
                    _chg_clr = "#f87171" if _change > 0 else "#60a5fa"
                    _arrow = "&#9650;" if _change > 0 else "&#9660;"
                _chg_html = (
                    f'<span style="color:{_chg_clr};font-size:0.75rem;font-weight:600">'
                    f'{_arrow} {_change:+.2f}</span>'
                )
            else:
                _chg_html = ""

            _fred_cards_html += (
                f'<div class="m-card">'
                f'<p class="m-label">{_label}</p>'
                f'<p class="m-value" style="color:#e2e8f0;font-size:2.2rem">{_val:.2f}<span style="font-size:0.8rem;color:#64748b"> {_unit}</span></p>'
                f'<p class="m-sub">{_chg_html} &nbsp; <span style="color:#475569">{_last_date}</span></p>'
                f'</div>'
            )
        _fred_cards_html += '</div>'
        st.markdown(_fred_cards_html, unsafe_allow_html=True)

        # Sparkline charts for all indicators
        _spark_ids = ["CPIAUCSL", "PCEPILFE", "UNRATE", "FEDFUNDS", "T10Y2Y", "PAYEMS", "GDP", "DFF"]
        _spark_available = [_sid for _sid in _spark_ids if _fred.get(_sid, {}).get("observations")]
        if _spark_available:
            _n_cols = min(4, len(_spark_available))
            _spark_cols = st.columns(_n_cols)
            for _i, _sid in enumerate(_spark_available):
                _ind = _fred[_sid]
                _obs = _ind.get("observations", [])
                if len(_obs) < 2:
                    continue
                # Reverse so chronological order
                _obs_sorted = list(reversed(_obs[:12]))
                _dates = [o["date"] for o in _obs_sorted]
                _values = [o["value"] for o in _obs_sorted]

                _spark_fig = go.Figure()
                _spark_fig.add_trace(go.Scatter(
                    x=_dates, y=_values,
                    mode="lines",
                    line=dict(width=2, color="#818cf8"),
                    fill="tozeroy",
                    fillcolor="rgba(129,140,248,0.08)",
                    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>",
                ))
                _spark_fig.update_layout(
                    **PLOTLY_LAYOUT,
                    height=120,
                    margin=dict(l=5, r=5, t=20, b=5),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False, gridcolor=GRID),
                    showlegend=False,
                    title=dict(
                        text=_ind.get("short_name", _sid),
                        font=dict(size=10, color=FONT_DIM),
                        x=0.5, y=0.95,
                    ),
                )
                with _spark_cols[_i % _n_cols]:
                    st.plotly_chart(_spark_fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# Chart 1 — Hawk-Dove Spectrum
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown(f'<p class="section-hdr">Hawk-Dove Spectrum — {stance_view}</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">All participants ranked from most dovish to most hawkish &nbsp;&bull;&nbsp; '
    '<span style="color:#fbbf24">&#9733;</span> = 2026 voting member</p>',
    unsafe_allow_html=True,
)

labels_spectrum = [
    f"{'&#9733; ' if r.voter else ''}{r.short} <span style='color:#475569;font-size:0.75em'>({r.inst})</span>"
    for _, r in filtered.iterrows()
]

fig1 = go.Figure()

# Colored bars
fig1.add_trace(
    go.Bar(
        y=list(range(len(filtered))),
        x=filtered["score"],
        orientation="h",
        marker=dict(
            color=[score_color(s) for s in filtered["score"]],
            opacity=0.85,
            line=dict(width=0),
        ),
        text=[f"  {s:+.2f}" for s in filtered["score"]],
        textposition="outside",
        textfont=dict(size=11, color=FONT_DIM, family="Inter"),
        hovertemplate="<b>%{customdata[0]}</b><br>Score: %{x:+.3f}<br>%{customdata[1]}<extra></extra>",
        customdata=list(zip(filtered["name"], filtered["label"])),
    )
)

fig1.add_vline(x=0, line_width=1.5, line_color="rgba(148,163,184,0.25)")
fig1.add_vline(x=1.5, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.2)")
fig1.add_vline(x=-1.5, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.2)")

fig1.update_layout(
    **PLOTLY_LAYOUT,
    height=max(480, len(filtered) * 38),
    xaxis=dict(
        range=[-5.5, 5.5],
        gridcolor=GRID,
        zeroline=False,
        tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
        title=dict(text="← Dovish          Score          Hawkish →", font=dict(size=11, color=FONT_DIM)),
    ),
    yaxis=dict(
        tickvals=list(range(len(filtered))),
        ticktext=[f"{r.short}  ({r.inst})" for _, r in filtered.iterrows()],
        gridcolor=GRID,
    ),
    margin=dict(l=180, r=60, t=10, b=45),
    showlegend=False,
    bargap=0.35,
)

spectrum_selection = st.plotly_chart(fig1, use_container_width=True, on_select="rerun", key="spectrum_click")

# Click-to-inspect for spectrum chart
_spec_pts = spectrum_selection.get("selection", {}).get("points", []) if spectrum_selection else []
if _spec_pts:
    _sp = _spec_pts[0]
    _sp_idx = _sp.get("point_number", 0)
    if _sp_idx < len(filtered):
        _sp_name = filtered.iloc[_sp_idx]["name"]
        render_evidence_panel(_sp_name, history)

# ══════════════════════════════════════════════════════════════════════════
# Chart — 2D Stance Scatter (Policy vs Balance Sheet)
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">2D Stance Map — Policy vs Balance Sheet</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">Each participant plotted by interest rate stance (x) and balance sheet stance (y) '
    '&nbsp;&bull;&nbsp; Dot size indicates voter status</p>',
    unsafe_allow_html=True,
)

fig_scatter = go.Figure()

# Quadrant background shading
fig_scatter.add_shape(type="rect", x0=0, x1=5.25, y0=0, y1=5.25,
                      fillcolor="rgba(248,113,113,0.04)", line_width=0)
fig_scatter.add_shape(type="rect", x0=-5.25, x1=0, y0=0, y1=5.25,
                      fillcolor="rgba(167,139,250,0.04)", line_width=0)
fig_scatter.add_shape(type="rect", x0=0, x1=5.25, y0=-5.25, y1=0,
                      fillcolor="rgba(251,191,36,0.04)", line_width=0)
fig_scatter.add_shape(type="rect", x0=-5.25, x1=0, y0=-5.25, y1=0,
                      fillcolor="rgba(96,165,250,0.04)", line_width=0)

# Quadrant labels
for text, x, y in [
    ("Rate Hawk / BS Hawk", 3.75, 4.5),
    ("Rate Dove / BS Hawk", -3.75, 4.5),
    ("Rate Hawk / BS Dove", 3.75, -4.5),
    ("Rate Dove / BS Dove", -3.75, -4.5),
]:
    fig_scatter.add_annotation(
        text=text, x=x, y=y, showarrow=False,
        font=dict(size=9, color="rgba(148,163,184,0.4)"),
    )

# Plot participants
scatter_df = filtered.copy()
fig_scatter.add_trace(
    go.Scatter(
        x=scatter_df["policy_score"],
        y=scatter_df["balance_sheet_score"],
        mode="markers+text",
        marker=dict(
            size=[18 if v else 12 for v in scatter_df["voter"]],
            color=[score_color(s) for s in scatter_df["overall_score"]],
            line=dict(width=1.5, color="rgba(255,255,255,0.2)"),
            opacity=0.9,
        ),
        text=scatter_df["short"],
        textposition="top center",
        textfont=dict(size=9, color=FONT_DIM),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Policy: %{x:+.3f}<br>"
            "Balance Sheet: %{y:+.3f}<br>"
            "Overall: %{customdata[1]:+.3f}"
            "<extra></extra>"
        ),
        customdata=list(zip(scatter_df["name"], scatter_df["overall_score"])),
        showlegend=False,
    )
)

fig_scatter.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.2)")
fig_scatter.add_vline(x=0, line_width=1, line_color="rgba(148,163,184,0.2)")

fig_scatter.update_layout(
    **PLOTLY_LAYOUT,
    height=520,
    xaxis=dict(
        range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
        tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
        title=dict(text="← Dovish (Rates)     Policy Score     Hawkish (Rates) →", font=dict(size=11, color=FONT_DIM)),
    ),
    yaxis=dict(
        range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
        tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
        title=dict(text="← Dovish (QE/Slow QT)     BS Score     Hawkish (QT) →", font=dict(size=11, color=FONT_DIM)),
    ),
    margin=dict(l=70, r=30, t=10, b=55),
)

scatter_selection = st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", key="scatter_click")

# Click-to-inspect for 2D scatter
_scat_pts = scatter_selection.get("selection", {}).get("points", []) if scatter_selection else []
if _scat_pts:
    _scp = _scat_pts[0]
    _scp_idx = _scp.get("point_number", 0)
    if _scp_idx < len(scatter_df):
        _scp_name = scatter_df.iloc[_scp_idx]["name"]
        render_evidence_panel(_scp_name, history)

# ══════════════════════════════════════════════════════════════════════════
# Chart 2 & 3 — Composition + Voters vs Alternates (side by side)
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1], gap="large")

with col_l:
    st.markdown(f'<p class="section-hdr">Committee Composition — {stance_view}</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Stance breakdown across all participants</p>', unsafe_allow_html=True)

    fig2 = go.Figure(
        go.Pie(
            labels=["Hawkish", "Neutral", "Dovish"],
            values=[len(hawks), len(neutrals), len(doves)],
            hole=0.6,
            marker=dict(
                colors=[HAWK, NEUTRAL_C, DOVE],
                line=dict(color="rgba(15,23,42,0.9)", width=3),
            ),
            textinfo="label+value",
            textfont=dict(size=12, color="white", family="Inter"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
            pull=[0.02, 0, 0.02],
            sort=False,
        )
    )
    fig2.update_layout(
        **PLOTLY_LAYOUT,
        height=380,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[
            dict(
                text=f"<b style='font-size:1.8rem'>{len(df)}</b><br><span style='color:{FONT_DIM}'>members</span>",
                x=0.5, y=0.5,
                font=dict(size=14, color=FONT),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_r:
    st.markdown(f'<p class="section-hdr">Voters vs Alternates — {stance_view}</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-sub">Comparing stance distributions &nbsp;&bull;&nbsp; '
        '<span style="color:#fbbf24">&#9670;</span> = group average</p>',
        unsafe_allow_html=True,
    )

    vdf = df[df.voter]
    adf = df[~df.voter]
    va = vdf["score"].mean()
    aa = adf["score"].mean()

    fig3 = go.Figure()
    _va_trace_names = []  # Track full names per trace for click handling
    for group_df, label in [(vdf, "Voters"), (adf, "Alternates")]:
        _va_trace_names.append(list(group_df["name"]))
        fig3.add_trace(
            go.Scatter(
                x=group_df["score"],
                y=[label] * len(group_df),
                mode="markers+text",
                marker=dict(size=14, color=[score_color(s) for s in group_df["score"]], line=dict(width=1.5, color="rgba(255,255,255,0.15)")),
                text=group_df["short"],
                textposition="top center",
                textfont=dict(size=8, color=FONT_DIM),
                customdata=list(group_df["name"]),
                hovertemplate="<b>%{text}</b><br>Score: %{x:+.3f}<extra></extra>",
                showlegend=False,
            )
        )

    for avg, label in [(va, "Voters"), (aa, "Alternates")]:
        fig3.add_trace(
            go.Scatter(
                x=[avg], y=[label], mode="markers",
                marker=dict(size=20, color=ACCENT, symbol="diamond", line=dict(width=2, color="white")),
                hovertemplate=f"Avg: {avg:+.3f}<extra></extra>",
                showlegend=False,
            )
        )

    fig3.add_vline(x=0, line_width=1.5, line_color="rgba(148,163,184,0.2)")
    fig3.update_layout(
        **PLOTLY_LAYOUT,
        height=380,
        xaxis=dict(range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
                    title=dict(text="← Dovish     Score     Hawkish →", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID),
        margin=dict(l=90, r=30, t=10, b=45),
    )
    va_selection = st.plotly_chart(fig3, use_container_width=True, on_select="rerun", key="va_click")

    # Click-to-inspect for voters vs alternates
    _va_pts = va_selection.get("selection", {}).get("points", []) if va_selection else []
    if _va_pts:
        _vp = _va_pts[0]
        _vp_curve = _vp.get("curve_number", 0)
        _vp_idx = _vp.get("point_number", 0)
        # curve 0/1 = voters/alternates scatter, 2/3 = avg diamonds
        if _vp_curve < len(_va_trace_names) and _vp_idx < len(_va_trace_names[_vp_curve]):
            _vp_name = _va_trace_names[_vp_curve][_vp_idx]
            render_evidence_panel(_vp_name, history)

# ══════════════════════════════════════════════════════════════════════════
# Chart 4 — Stance Trends
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Stance Trends</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">How each participant\'s stance has evolved over recent months</p>', unsafe_allow_html=True)

all_names = [p.name for p in PARTICIPANTS]
defaults = [
    "Kevin M. Warsh", "Jerome H. Powell", "Michelle W. Bowman",
    "Christopher J. Waller", "Lisa D. Cook", "Austan D. Goolsbee", "Neel Kashkari",
]

trend_cols = st.columns([3, 1])
with trend_cols[0]:
    selected = st.multiselect("Select participants", all_names, default=[n for n in defaults if n in all_names])
with trend_cols[1]:
    trend_mode = st.radio("View", ["Aggregate", "Policy & Balance Sheet"], index=0, horizontal=True, key="trend_mode")

if selected:
    fig4 = go.Figure()

    fig4.add_hrect(y0=1.5, y1=5.0, fillcolor="rgba(248,113,113,0.05)", line_width=0,
                   annotation_text="Hawkish zone", annotation_position="top left",
                   annotation_font=dict(color="rgba(248,113,113,0.35)", size=10))
    fig4.add_hrect(y0=-5.0, y1=-1.5, fillcolor="rgba(96,165,250,0.05)", line_width=0,
                   annotation_text="Dovish zone", annotation_position="bottom left",
                   annotation_font=dict(color="rgba(96,165,250,0.35)", size=10))

    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2

    # Track which participants have traces (for mapping click → participant)
    trace_names = []

    if trend_mode == "Aggregate":
        for i, name in enumerate(selected):
            entries = history.get(name, [])
            if not entries:
                continue
            trace_names.append(name)
            c = palette[i % len(palette)]
            fig4.add_trace(go.Scatter(
                x=[e["date"] for e in entries],
                y=[e.get(score_key, e.get("score", 0)) for e in entries],
                mode="lines+markers",
                name=last_name(name),
                line=dict(width=2.5, color=c, shape="spline"),
                marker=dict(size=8, color=c, line=dict(width=1, color="rgba(255,255,255,0.2)")),
                hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
            ))
    else:
        # Two traces per participant: policy (solid) and balance sheet (dashed)
        for i, name in enumerate(selected):
            entries = history.get(name, [])
            if not entries:
                continue
            # Each participant produces two traces; record name for both
            trace_names.append(name)
            trace_names.append(name)
            c = palette[i % len(palette)]
            ln = last_name(name)
            fig4.add_trace(go.Scatter(
                x=[e["date"] for e in entries],
                y=[e.get("policy_score", e.get("score", 0)) for e in entries],
                mode="lines+markers",
                name=f"{ln} (Pol.)",
                line=dict(width=2.5, color=c, shape="spline"),
                marker=dict(size=8, color=c, symbol="circle",
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                hovertemplate=f"<b>{name}</b> — Policy<br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
            ))
            fig4.add_trace(go.Scatter(
                x=[e["date"] for e in entries],
                y=[e.get("balance_sheet_score", 0) for e in entries],
                mode="lines+markers",
                name=f"{ln} (B.S.)",
                line=dict(width=2.5, color=c, shape="spline", dash="dash"),
                marker=dict(size=8, color=c, symbol="diamond",
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                hovertemplate=f"<b>{name}</b> — Balance Sheet<br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
            ))

    fig4.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.2)")
    fig4.add_hline(y=1.5, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.15)")
    fig4.add_hline(y=-1.5, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.15)")

    # Add FOMC meeting date markers as vertical lines
    _trend_dates = sorted({e["date"] for name in selected for e in history.get(name, [])})
    if _trend_dates:
        from datetime import date as _dt
        _range_start = _dt.fromisoformat(_trend_dates[0])
        _range_end = _dt.fromisoformat(_trend_dates[-1])
        _trend_meetings = get_meetings_in_range(_range_start, _range_end)
        for _tm in _trend_meetings:
            _tm_label = _tm.decision.upper() if _tm.decision else "FOMC"
            _tm_x = _tm.end_date.isoformat()
            fig4.add_vline(
                x=_tm_x, line_width=1, line_dash="dash",
                line_color="rgba(251,191,36,0.3)",
            )
            fig4.add_annotation(
                x=_tm_x, y=4.8, text=_tm_label, showarrow=False,
                font=dict(size=8, color="rgba(251,191,36,0.5)"),
                yref="y",
            )

    fig4.update_layout(
        **PLOTLY_LAYOUT,
        height=480,
        xaxis=dict(gridcolor=GRID, title=dict(text="Date", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID, range=[-5.25, 5.25], tickvals=[-5, -3, -1.5, 0, 1.5, 3, 5],
                   title=dict(text="Stance Score", font=dict(size=11, color=FONT_DIM))),
        legend=dict(bgcolor="rgba(15,23,42,0.7)", bordercolor="rgba(148,163,184,0.1)", borderwidth=1,
                    font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=55, r=30, t=40, b=45),
    )
    trend_selection = st.plotly_chart(fig4, use_container_width=True, on_select="rerun", key="trend_click")

    # ── Click-to-inspect: show evidence for selected point ─────────────
    sel_points = trend_selection.get("selection", {}).get("points", []) if trend_selection else []
    if sel_points:
        pt = sel_points[0]
        curve_idx = pt.get("curve_number", 0)
        clicked_date = pt.get("x", "")

        if curve_idx < len(trace_names):
            clicked_name = trace_names[curve_idx]
            render_evidence_panel(clicked_name, history, date=clicked_date)
else:
    st.info("Select participants above to view trend lines.")

# ══════════════════════════════════════════════════════════════════════════
# Chart 5 — Heatmap
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown(f'<p class="section-hdr">Stance Heatmap — {stance_view}</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Monthly stance scores across all participants</p>', unsafe_allow_html=True)

all_dates = sorted({d for entries in history.values() for d in [e["date"] for e in entries]})
h_names = [last_name(p.name) for p in PARTICIPANTS]
f_names = [p.name for p in PARTICIPANTS]

z = np.full((len(f_names), len(all_dates)), np.nan)
for i, name in enumerate(f_names):
    ds = {e["date"]: e.get(score_key, e.get("score", 0)) for e in history.get(name, [])}
    for j, d in enumerate(all_dates):
        if d in ds:
            z[i][j] = ds[d]

fig5 = go.Figure(go.Heatmap(
    z=z.tolist(), x=all_dates, y=h_names,
    colorscale=[
        [0.0, "#1e3a8a"], [0.15, "#2563eb"], [0.3, "#60a5fa"], [0.42, "#bfdbfe"],
        [0.5, "#f1f5f9"],
        [0.58, "#fecaca"], [0.7, "#f87171"], [0.85, "#dc2626"], [1.0, "#7f1d1d"],
    ],
    zmid=0, zmin=-5, zmax=5, connectgaps=False,
    colorbar=dict(
        title=dict(text="Score", font=dict(color=FONT_DIM, size=11)),
        tickfont=dict(color=FONT_DIM, size=10),
        tickvals=[-5, -2.5, 0, 2.5, 5],
        ticktext=["-5 Dovish", "-2.5", "0", "+2.5", "+5 Hawkish"],
        thickness=14, len=0.6,
    ),
    hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Score: %{z}<extra></extra>",
    xgap=2, ygap=2,
))

fig5.update_layout(
    **PLOTLY_LAYOUT,
    height=max(450, len(PARTICIPANTS) * 30),
    xaxis=dict(gridcolor=GRID, side="top"),
    yaxis=dict(gridcolor=GRID, autorange="reversed"),
    margin=dict(l=110, r=30, t=30, b=20),
)
st.plotly_chart(fig5, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# Participant Details Table
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Participant Details</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Full roster with current stance scores across all dimensions</p>', unsafe_allow_html=True)

tbl = filtered[["name", "inst", "title", "score", "label", "policy_score", "balance_sheet_score", "voter"]].copy()
tbl.columns = ["Name", "Institution", "Title", "Score", "Stance", "Policy Score", "BS Score", "2026 Voter"]
tbl["Score"] = tbl["Score"].apply(lambda x: f"{x:+.3f}")
tbl["Policy Score"] = tbl["Policy Score"].apply(lambda x: f"{x:+.3f}")
tbl["BS Score"] = tbl["BS Score"].apply(lambda x: f"{x:+.3f}")
tbl["2026 Voter"] = tbl["2026 Voter"].map({True: "Yes", False: "No"})
tbl = tbl.sort_values("Score", ascending=False).reset_index(drop=True)

tbl_selection = st.dataframe(
    tbl,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="tbl_click",
    column_config={
        "Name": st.column_config.TextColumn(width="large"),
        "Institution": st.column_config.TextColumn(width="medium"),
        "Title": st.column_config.TextColumn(width="small"),
        "Score": st.column_config.TextColumn(width="small"),
        "Stance": st.column_config.TextColumn(width="small"),
        "Policy Score": st.column_config.TextColumn(width="small"),
        "BS Score": st.column_config.TextColumn(width="small"),
        "2026 Voter": st.column_config.TextColumn(width="small"),
    },
)

# Click-to-inspect for table row
_tbl_rows = tbl_selection.selection.rows if tbl_selection else []
if _tbl_rows:
    _tbl_name = tbl.iloc[_tbl_rows[0]]["Name"]
    render_evidence_panel(_tbl_name, history)

# ══════════════════════════════════════════════════════════════════════════
# Evidence & Sources
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Evidence &amp; Sources</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">News articles, speeches, and quotes supporting each participant\'s stance classification</p>',
    unsafe_allow_html=True,
)

# Build evidence lookup from history
for _, row in filtered.iterrows():
    entries = history.get(row["name"], [])
    latest = entries[-1] if entries else None
    ev_list = latest.get("evidence", []) if latest else []
    if not ev_list:
        continue

    with st.expander(f"{row['name']}  —  {row['label']} ({row['score']:+.3f})", expanded=False):
        for ev in ev_list:
            title_text = ev.get("title", "Untitled")
            url = ev.get("url", "")
            quote = ev.get("quote", "")
            keywords = ev.get("keywords", [])
            directions = ev.get("directions", [])
            dimensions = ev.get("dimensions", ["policy"] * len(keywords))
            src_type = SOURCE_LABELS.get(ev.get("source_type", ""), ev.get("source_type", ""))

            # Title with link
            if url:
                title_html = f'<a href="{url}" target="_blank">{title_text}</a>'
            else:
                title_html = title_text

            # Keyword tags with dimension labels
            tags_html = ""
            for kw, direction, dim in zip(keywords, directions, dimensions):
                tag_cls = "ev-tag-hawk" if direction == "hawkish" else "ev-tag-dove"
                dim_label = DIM_LABELS.get(dim, dim)
                tags_html += f'<span class="ev-tag {tag_cls}">{kw}</span>'
                tags_html += f'<span class="ev-tag ev-tag-dim">{dim_label}</span>'
            if src_type:
                tags_html += f'<span class="ev-tag ev-tag-src">{src_type}</span>'

            # Quote
            quote_html = f'<p class="ev-quote">"{quote}"</p>' if quote else ""

            st.markdown(
                f'<div class="ev-card">'
                f'<p class="ev-title">{title_html}</p>'
                f'{quote_html}'
                f'<div class="ev-tags">{tags_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════
# Downloads
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Export Data</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Download stance data as CSV for your own analysis</p>', unsafe_allow_html=True)

csv_current = df[["name", "inst", "title", "voter", "overall_score", "policy_score", "balance_sheet_score"]].copy()
csv_current["overall_label"] = csv_current["overall_score"].apply(score_label)
csv_current["policy_label"] = csv_current["policy_score"].apply(score_label)
csv_current["balance_sheet_label"] = csv_current["balance_sheet_score"].apply(score_label)
csv_current.columns = ["Name", "Institution", "Title", "2026 Voter",
                        "Overall Score", "Policy Score", "Balance Sheet Score",
                        "Overall Stance", "Policy Stance", "Balance Sheet Stance"]
csv_current = csv_current.sort_values("Overall Score", ascending=False)

hist_rows = []
for name, entries in history.items():
    p = next((p for p in PARTICIPANTS if p.name == name), None)
    for e in entries:
        hist_rows.append(dict(
            Name=name, Institution=p.institution if p else "", Date=e["date"],
            Score=e.get("score", 0), Stance=e.get("label", ""),
            Policy_Score=e.get("policy_score", e.get("score", 0)),
            Policy_Stance=e.get("policy_label", ""),
            Balance_Sheet_Score=e.get("balance_sheet_score", 0),
            Balance_Sheet_Stance=e.get("balance_sheet_label", ""),
            Source=e.get("source", ""),
        ))
csv_hist = pd.DataFrame(hist_rows).sort_values(["Date", "Name"])

dc1, dc2, _ = st.columns([1, 1, 2])
with dc1:
    st.download_button(
        "Download Current Stances",
        csv_current.to_csv(index=False),
        f"fomc_stances_{datetime.now():%Y-%m-%d}.csv",
        "text/csv",
    )
with dc2:
    st.download_button(
        "Download Full History",
        csv_hist.to_csv(index=False),
        "fomc_stance_history.csv",
        "text/csv",
    )

# ══════════════════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown(
    '<div class="foot">'
    "FOMC Stance Tracker &nbsp;&middot;&nbsp; "
    "Data from DuckDuckGo News, Federal Reserve RSS &amp; Speeches, "
    '<a href="https://www.bis.org/cbspeeches/index.htm">BIS Central Banker Speeches</a>, '
    "FOMC Statements/Minutes, Regional Fed Blogs &amp; "
    '<a href="https://fred.stlouisfed.org/">FRED</a>'
    " &nbsp;&middot;&nbsp; Keyword-based NLP classification<br>"
    "Dual-dimension analysis: Policy (rates) + Balance Sheet (QT/QE) &nbsp;&middot;&nbsp; "
    "Vote-weighted policy signal with FOMC meeting calendar<br>"
    "This tool is for informational purposes only and does not constitute financial advice."
    "</div>",
    unsafe_allow_html=True,
)
