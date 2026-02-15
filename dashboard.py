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


def score_color(s: float) -> str:
    if s > 0.3:
        return HAWK
    if s < -0.3:
        return DOVE
    return NEUTRAL_C


def score_label(s: float) -> str:
    if s > 0.3:
        return "Hawkish"
    if s < -0.3:
        return "Dovish"
    return "Neutral"


def last_name(full: str) -> str:
    return full.split()[-1]


# ── Load Data ──────────────────────────────────────────────────────────────
history = load_history()

rows = []
for p in PARTICIPANTS:
    latest = get_latest_stance(p.name)
    sc = latest["score"] if latest else p.historical_lean
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
        )
    )

df = pd.DataFrame(rows).sort_values("score", ascending=True).reset_index(drop=True)
hawks = df[df.label == "Hawkish"]
neutrals = df[df.label == "Neutral"]
doves = df[df.label == "Dovish"]

avg_score = df["score"].mean()
voter_avg = df[df.voter]["score"].mean()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-brand">FOMC Stance Tracker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sidebar-desc">Hawkish / dovish classification of Federal Reserve officials '
        "based on recent news, speeches, and public statements.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("**Filters**")
    show_voters = st.checkbox("Voting members only", value=False)
    show_govs = st.checkbox("Governors only", value=False)

    st.markdown("---")
    st.markdown("**Legend**")
    st.markdown(
        f'<div class="legend-item"><div class="legend-dot" style="background:{HAWK}"></div>Hawkish (&gt; +0.3)</div>'
        f'<div class="legend-item"><div class="legend-dot" style="background:{NEUTRAL_C}"></div>Neutral (-0.3 to +0.3)</div>'
        f'<div class="legend-item"><div class="legend-dot" style="background:{DOVE}"></div>Dovish (&lt; -0.3)</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        '<p class="sidebar-desc">Scores range from <b>-1.0</b> (very dovish) '
        'to <b>+1.0</b> (very hawkish). Classification uses weighted keyword '
        "matching on news headlines, Fed speeches, and BIS central banker speeches.</p>",
        unsafe_allow_html=True,
    )

filtered = df.copy()
if show_voters:
    filtered = filtered[filtered.voter]
if show_govs:
    filtered = filtered[filtered.gov]

# ── Hero Header ────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="hero">
        <p class="hero-title">FOMC Participant<br>Stance Tracker</p>
        <p class="hero-sub">Real-time hawkish / dovish classification of Federal Reserve officials
        based on recent news, speeches, and public statements.</p>
        <span class="hero-date">Last updated {datetime.now().strftime('%B %d, %Y')}</span>
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
# Chart 1 — Hawk-Dove Spectrum
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Hawk-Dove Spectrum</p>', unsafe_allow_html=True)
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
fig1.add_vline(x=0.3, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.2)")
fig1.add_vline(x=-0.3, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.2)")

fig1.update_layout(
    **PLOTLY_LAYOUT,
    height=max(480, len(filtered) * 38),
    xaxis=dict(
        range=[-1.15, 1.15],
        gridcolor=GRID,
        zeroline=False,
        tickvals=[-1.0, -0.5, -0.3, 0, 0.3, 0.5, 1.0],
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

st.plotly_chart(fig1, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# Chart 2 & 3 — Composition + Voters vs Alternates (side by side)
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1], gap="large")

with col_l:
    st.markdown('<p class="section-hdr">Committee Composition</p>', unsafe_allow_html=True)
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
    st.markdown('<p class="section-hdr">Voters vs Alternates</p>', unsafe_allow_html=True)
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
    for group_df, label in [(vdf, "Voters"), (adf, "Alternates")]:
        fig3.add_trace(
            go.Scatter(
                x=group_df["score"],
                y=[label] * len(group_df),
                mode="markers+text",
                marker=dict(size=14, color=[score_color(s) for s in group_df["score"]], line=dict(width=1.5, color="rgba(255,255,255,0.15)")),
                text=group_df["short"],
                textposition="top center",
                textfont=dict(size=8, color=FONT_DIM),
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
        xaxis=dict(range=[-1.05, 1.05], gridcolor=GRID, zeroline=False,
                    title=dict(text="← Dovish     Score     Hawkish →", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID),
        margin=dict(l=90, r=30, t=10, b=45),
    )
    st.plotly_chart(fig3, use_container_width=True)

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
selected = st.multiselect("Select participants", all_names, default=[n for n in defaults if n in all_names])

if selected:
    fig4 = go.Figure()

    fig4.add_hrect(y0=0.3, y1=1.0, fillcolor="rgba(248,113,113,0.05)", line_width=0,
                   annotation_text="Hawkish zone", annotation_position="top left",
                   annotation_font=dict(color="rgba(248,113,113,0.35)", size=10))
    fig4.add_hrect(y0=-1.0, y1=-0.3, fillcolor="rgba(96,165,250,0.05)", line_width=0,
                   annotation_text="Dovish zone", annotation_position="bottom left",
                   annotation_font=dict(color="rgba(96,165,250,0.35)", size=10))

    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2

    for i, name in enumerate(selected):
        entries = history.get(name, [])
        if not entries:
            continue
        c = palette[i % len(palette)]
        fig4.add_trace(go.Scatter(
            x=[e["date"] for e in entries],
            y=[e["score"] for e in entries],
            mode="lines+markers",
            name=last_name(name),
            line=dict(width=2.5, color=c, shape="spline"),
            marker=dict(size=6, color=c, line=dict(width=1, color="rgba(255,255,255,0.2)")),
            hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Score: %{{y:+.3f}}<extra></extra>",
        ))

    fig4.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.2)")
    fig4.add_hline(y=0.3, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.15)")
    fig4.add_hline(y=-0.3, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.15)")

    fig4.update_layout(
        **PLOTLY_LAYOUT,
        height=480,
        xaxis=dict(gridcolor=GRID, title=dict(text="Date", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID, range=[-1.05, 1.05], tickvals=[-1, -0.5, -0.3, 0, 0.3, 0.5, 1],
                   title=dict(text="Stance Score", font=dict(size=11, color=FONT_DIM))),
        legend=dict(bgcolor="rgba(15,23,42,0.7)", bordercolor="rgba(148,163,184,0.1)", borderwidth=1,
                    font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=55, r=30, t=40, b=45),
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Select participants above to view trend lines.")

# ══════════════════════════════════════════════════════════════════════════
# Chart 5 — Heatmap
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Stance Heatmap</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Monthly stance scores across all participants</p>', unsafe_allow_html=True)

all_dates = sorted({d for entries in history.values() for d in [e["date"] for e in entries]})
h_names = [last_name(p.name) for p in PARTICIPANTS]
f_names = [p.name for p in PARTICIPANTS]

z = np.full((len(f_names), len(all_dates)), np.nan)
for i, name in enumerate(f_names):
    ds = {e["date"]: e["score"] for e in history.get(name, [])}
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
    zmid=0, zmin=-1, zmax=1, connectgaps=False,
    colorbar=dict(
        title=dict(text="Score", font=dict(color=FONT_DIM, size=11)),
        tickfont=dict(color=FONT_DIM, size=10),
        tickvals=[-1, -0.5, 0, 0.5, 1],
        ticktext=["-1 Dovish", "-0.5", "0", "+0.5", "+1 Hawkish"],
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
st.markdown('<p class="section-sub">Full roster with current stance scores</p>', unsafe_allow_html=True)

tbl = filtered[["name", "inst", "title", "score", "label", "voter"]].copy()
tbl.columns = ["Name", "Institution", "Title", "Score", "Stance", "2026 Voter"]
tbl["Score"] = tbl["Score"].apply(lambda x: f"{x:+.3f}")
tbl["2026 Voter"] = tbl["2026 Voter"].map({True: "Yes", False: "No"})
tbl = tbl.sort_values("Score", ascending=False).reset_index(drop=True)

st.dataframe(
    tbl,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Name": st.column_config.TextColumn(width="large"),
        "Institution": st.column_config.TextColumn(width="medium"),
        "Title": st.column_config.TextColumn(width="small"),
        "Score": st.column_config.TextColumn(width="small"),
        "Stance": st.column_config.TextColumn(width="small"),
        "2026 Voter": st.column_config.TextColumn(width="small"),
    },
)

# ══════════════════════════════════════════════════════════════════════════
# Evidence & Sources
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<p class="section-hdr">Evidence &amp; Sources</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="section-sub">News articles, speeches, and quotes supporting each participant\'s stance classification</p>',
    unsafe_allow_html=True,
)

SOURCE_LABELS = {
    "duckduckgo": "News",
    "fed_rss": "Fed RSS",
    "bis_speeches": "BIS Speech",
}

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
            src_type = SOURCE_LABELS.get(ev.get("source_type", ""), ev.get("source_type", ""))

            # Title with link
            if url:
                title_html = f'<a href="{url}" target="_blank">{title_text}</a>'
            else:
                title_html = title_text

            # Keyword tags
            tags_html = ""
            for kw, direction in zip(keywords, directions):
                tag_cls = "ev-tag-hawk" if direction == "hawkish" else "ev-tag-dove"
                tags_html += f'<span class="ev-tag {tag_cls}">{kw}</span>'
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

csv_current = df[["name", "inst", "title", "voter", "score", "label"]].copy()
csv_current.columns = ["Name", "Institution", "Title", "2026 Voter", "Score", "Stance"]
csv_current = csv_current.sort_values("Score", ascending=False)

hist_rows = []
for name, entries in history.items():
    p = next((p for p in PARTICIPANTS if p.name == name), None)
    for e in entries:
        hist_rows.append(dict(Name=name, Institution=p.institution if p else "", Date=e["date"],
                              Score=e["score"], Stance=e["label"], Source=e.get("source", "")))
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
    "Data from DuckDuckGo News, Federal Reserve RSS &amp; "
    '<a href="https://www.bis.org/cbspeeches/index.htm">BIS Central Banker Speeches</a>'
    " &nbsp;&middot;&nbsp; Keyword-based NLP classification<br>"
    "This tool is for informational purposes only and does not constitute financial advice."
    "</div>",
    unsafe_allow_html=True,
)
