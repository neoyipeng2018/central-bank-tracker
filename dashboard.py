#!/usr/bin/env python3
"""FOMC Participant Stance Tracker - Interactive Streamlit Dashboard."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from fomc_tracker.participants import PARTICIPANTS, get_voters, get_alternates
from fomc_tracker.historical_data import load_history, get_latest_stance

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FOMC Stance Tracker",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .metric-card h3 {
        color: #8892b0;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 0 0 0.4rem 0;
    }
    .metric-card .value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .hawk-val { color: #ef4444; }
    .dove-val { color: #3b82f6; }
    .neutral-val { color: #a3a3a3; }
    .balance-val { color: #f59e0b; }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Color Palette ──────────────────────────────────────────────────────────
HAWK_COLOR = "#ef4444"
DOVE_COLOR = "#3b82f6"
NEUTRAL_COLOR = "#6b7280"
HAWK_GRADIENT = ["#fca5a5", "#ef4444", "#991b1b"]
DOVE_GRADIENT = ["#93c5fd", "#3b82f6", "#1e3a8a"]
BG_COLOR = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.06)"
FONT_COLOR = "#e2e8f0"


def score_to_color(score: float) -> str:
    """Map a -1..+1 score to a hawk/dove color."""
    if score > 0.3:
        return HAWK_COLOR
    elif score < -0.3:
        return DOVE_COLOR
    return NEUTRAL_COLOR


def score_to_label(score: float) -> str:
    if score > 0.3:
        return "Hawkish"
    elif score < -0.3:
        return "Dovish"
    return "Neutral"


def short_name(full_name: str) -> str:
    """'Jerome H. Powell' -> 'Powell'"""
    return full_name.split()[-1]


# ── Load Data ──────────────────────────────────────────────────────────────
history = load_history()

# Build a DataFrame of latest stances
rows = []
for p in PARTICIPANTS:
    latest = get_latest_stance(p.name)
    score = latest["score"] if latest else p.historical_lean
    rows.append(
        {
            "name": p.name,
            "short_name": short_name(p.name),
            "institution": p.institution,
            "title": p.title,
            "voter": p.is_voter_2026,
            "governor": p.is_governor,
            "score": score,
            "label": score_to_label(score),
            "color": score_to_color(score),
        }
    )

df = pd.DataFrame(rows).sort_values("score", ascending=True).reset_index(drop=True)

hawks = df[df["label"] == "Hawkish"]
doves = df[df["label"] == "Dovish"]
neutrals = df[df["label"] == "Neutral"]

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ FOMC Tracker")
    st.markdown(f"**Last updated:** {datetime.now().strftime('%B %d, %Y')}")
    st.markdown("---")

    st.markdown("### Filter")
    show_voters_only = st.checkbox("Voting members only", value=False)
    show_governors = st.checkbox("Governors only", value=False)

    st.markdown("---")
    st.markdown("### Legend")
    st.markdown(
        f'<span style="color:{HAWK_COLOR}">■</span> **Hawkish** (score > 0.3)',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span style="color:{NEUTRAL_COLOR}">■</span> **Neutral** (-0.3 to 0.3)',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span style="color:{DOVE_COLOR}">■</span> **Dovish** (score < -0.3)',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<small>Scores: -1.0 (very dovish) to +1.0 (very hawkish)<br>"
        "Based on keyword analysis of recent speeches and news.</small>",
        unsafe_allow_html=True,
    )

# Apply filters
filtered = df.copy()
if show_voters_only:
    filtered = filtered[filtered["voter"]]
if show_governors:
    filtered = filtered[filtered["governor"]]

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("# FOMC Participant Stance Tracker")
st.markdown(
    "Real-time hawkish/dovish classification of Federal Reserve officials "
    "based on recent news, speeches, and public statements."
)

# ── Top Metrics ────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""<div class="metric-card">
            <h3>Hawkish</h3>
            <p class="value hawk-val">{len(hawks)}</p>
        </div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div class="metric-card">
            <h3>Neutral</h3>
            <p class="value neutral-val">{len(neutrals)}</p>
        </div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div class="metric-card">
            <h3>Dovish</h3>
            <p class="value dove-val">{len(doves)}</p>
        </div>""",
        unsafe_allow_html=True,
    )
with col4:
    balance = len(hawks) - len(doves)
    balance_text = f"+{balance}" if balance > 0 else str(balance)
    st.markdown(
        f"""<div class="metric-card">
            <h3>Hawk-Dove Balance</h3>
            <p class="value balance-val">{balance_text}</p>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart 1: Hawk-Dove Spectrum (Horizontal Diverging Bar) ────────────────
st.markdown("## Hawk-Dove Spectrum")
st.caption("All FOMC participants ranked from most dovish to most hawkish")

fig_spectrum = go.Figure()

fig_spectrum.add_trace(
    go.Bar(
        y=filtered["short_name"],
        x=filtered["score"],
        orientation="h",
        marker=dict(
            color=[score_to_color(s) for s in filtered["score"]],
            line=dict(width=0),
            opacity=0.9,
        ),
        text=[f"{s:+.2f}" for s in filtered["score"]],
        textposition="outside",
        textfont=dict(size=11, color=FONT_COLOR),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score: %{x:+.3f}<br>"
            "<extra></extra>"
        ),
    )
)

# Add voter indicators
for i, row in filtered.iterrows():
    if row["voter"]:
        fig_spectrum.add_annotation(
            x=max(filtered["score"]) + 0.15,
            y=row["short_name"],
            text="★",
            showarrow=False,
            font=dict(size=12, color="#f59e0b"),
        )

# Center line
fig_spectrum.add_vline(x=0, line_width=2, line_color="rgba(255,255,255,0.3)")

# Threshold lines
fig_spectrum.add_vline(
    x=0.3, line_width=1, line_dash="dot", line_color="rgba(239,68,68,0.3)"
)
fig_spectrum.add_vline(
    x=-0.3, line_width=1, line_dash="dot", line_color="rgba(59,130,246,0.3)"
)

fig_spectrum.update_layout(
    height=max(500, len(filtered) * 36),
    paper_bgcolor=BG_COLOR,
    plot_bgcolor=BG_COLOR,
    font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
    xaxis=dict(
        title="← Dovish          Score          Hawkish →",
        range=[-1.1, 1.1],
        gridcolor=GRID_COLOR,
        zeroline=False,
        tickvals=[-1.0, -0.5, -0.3, 0, 0.3, 0.5, 1.0],
    ),
    yaxis=dict(gridcolor=GRID_COLOR),
    margin=dict(l=100, r=60, t=20, b=50),
    showlegend=False,
)

st.plotly_chart(fig_spectrum, use_container_width=True)
st.caption("★ = 2026 voting member")

# ── Chart 2: Stance Distribution (Donut Chart) ────────────────────────────
st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("## Committee Composition")
    st.caption("Distribution of stances across all participants")

    labels = ["Hawkish", "Neutral", "Dovish"]
    values = [len(hawks), len(neutrals), len(doves)]
    colors = [HAWK_COLOR, NEUTRAL_COLOR, DOVE_COLOR]

    fig_donut = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#0f172a", width=3)),
            textinfo="label+value",
            textfont=dict(size=13, color="white"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
            pull=[0.03, 0, 0.03],
        )
    )

    fig_donut.update_layout(
        height=350,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        annotations=[
            dict(
                text=f"<b>{len(df)}</b><br>Members",
                x=0.5,
                y=0.5,
                font=dict(size=18, color=FONT_COLOR),
                showarrow=False,
            )
        ],
    )

    st.plotly_chart(fig_donut, use_container_width=True)

# ── Chart 3: Voters vs Alternates Comparison ──────────────────────────────
with col_right:
    st.markdown("## Voters vs Alternates")
    st.caption("Comparing stance distribution between voting and non-voting members")

    voter_df = df[df["voter"]]
    alt_df = df[~df["voter"]]

    voter_avg = voter_df["score"].mean()
    alt_avg = alt_df["score"].mean()

    fig_compare = go.Figure()

    # Voter dots
    fig_compare.add_trace(
        go.Scatter(
            x=voter_df["score"],
            y=["Voters"] * len(voter_df),
            mode="markers+text",
            marker=dict(
                size=16,
                color=[score_to_color(s) for s in voter_df["score"]],
                line=dict(width=2, color="rgba(255,255,255,0.2)"),
            ),
            text=voter_df["short_name"],
            textposition="top center",
            textfont=dict(size=9, color=FONT_COLOR),
            hovertemplate="<b>%{text}</b><br>Score: %{x:+.3f}<extra></extra>",
            showlegend=False,
        )
    )

    # Alternate dots
    fig_compare.add_trace(
        go.Scatter(
            x=alt_df["score"],
            y=["Alternates"] * len(alt_df),
            mode="markers+text",
            marker=dict(
                size=16,
                color=[score_to_color(s) for s in alt_df["score"]],
                line=dict(width=2, color="rgba(255,255,255,0.2)"),
            ),
            text=alt_df["short_name"],
            textposition="top center",
            textfont=dict(size=9, color=FONT_COLOR),
            hovertemplate="<b>%{text}</b><br>Score: %{x:+.3f}<extra></extra>",
            showlegend=False,
        )
    )

    # Average markers
    fig_compare.add_trace(
        go.Scatter(
            x=[voter_avg],
            y=["Voters"],
            mode="markers",
            marker=dict(size=22, color="#f59e0b", symbol="diamond", line=dict(width=2, color="white")),
            hovertemplate=f"Voter Avg: {voter_avg:+.3f}<extra></extra>",
            showlegend=False,
        )
    )
    fig_compare.add_trace(
        go.Scatter(
            x=[alt_avg],
            y=["Alternates"],
            mode="markers",
            marker=dict(size=22, color="#f59e0b", symbol="diamond", line=dict(width=2, color="white")),
            hovertemplate=f"Alternate Avg: {alt_avg:+.3f}<extra></extra>",
            showlegend=False,
        )
    )

    fig_compare.add_vline(x=0, line_width=2, line_color="rgba(255,255,255,0.3)")

    fig_compare.update_layout(
        height=350,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
        xaxis=dict(
            title="← Dovish     Score     Hawkish →",
            range=[-1.0, 1.0],
            gridcolor=GRID_COLOR,
            zeroline=False,
        ),
        yaxis=dict(gridcolor=GRID_COLOR),
        margin=dict(l=100, r=40, t=20, b=50),
    )

    st.plotly_chart(fig_compare, use_container_width=True)
    st.caption("◆ = group average score")

# ── Chart 4: Historical Stance Trends ─────────────────────────────────────
st.markdown("---")
st.markdown("## Stance Trends Over Time")
st.caption("How each participant's stance has evolved over recent months")

# Let user pick participants to show
all_names = [p.name for p in PARTICIPANTS]
default_names = [
    "Kevin M. Warsh",
    "Jerome H. Powell",
    "Michelle W. Bowman",
    "Christopher J. Waller",
    "Lisa D. Cook",
    "Austan D. Goolsbee",
    "Neel Kashkari",
]
selected_names = st.multiselect(
    "Select participants to display",
    all_names,
    default=[n for n in default_names if n in all_names],
)

if selected_names:
    fig_trends = go.Figure()

    # Shaded hawk/dove zones
    fig_trends.add_hrect(
        y0=0.3, y1=1.0,
        fillcolor="rgba(239,68,68,0.07)",
        line_width=0,
        annotation_text="Hawkish",
        annotation_position="top left",
        annotation_font=dict(color="rgba(239,68,68,0.4)", size=11),
    )
    fig_trends.add_hrect(
        y0=-1.0, y1=-0.3,
        fillcolor="rgba(59,130,246,0.07)",
        line_width=0,
        annotation_text="Dovish",
        annotation_position="bottom left",
        annotation_font=dict(color="rgba(59,130,246,0.4)", size=11),
    )

    # Color palette for lines
    line_colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1

    for i, name in enumerate(selected_names):
        entries = history.get(name, [])
        if not entries:
            continue

        dates = [e["date"] for e in entries]
        scores = [e["score"] for e in entries]
        color = line_colors[i % len(line_colors)]

        fig_trends.add_trace(
            go.Scatter(
                x=dates,
                y=scores,
                mode="lines+markers",
                name=short_name(name),
                line=dict(width=2.5, color=color),
                marker=dict(size=7, color=color, line=dict(width=1, color="rgba(255,255,255,0.3)")),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Date: %{x}<br>"
                    "Score: %{y:+.3f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig_trends.add_hline(y=0, line_width=1, line_color="rgba(255,255,255,0.3)")
    fig_trends.add_hline(y=0.3, line_width=1, line_dash="dot", line_color="rgba(239,68,68,0.25)")
    fig_trends.add_hline(y=-0.3, line_width=1, line_dash="dot", line_color="rgba(59,130,246,0.25)")

    fig_trends.update_layout(
        height=450,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
        xaxis=dict(gridcolor=GRID_COLOR, title="Date"),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            title="Stance Score",
            range=[-1.05, 1.05],
            tickvals=[-1.0, -0.5, -0.3, 0, 0.3, 0.5, 1.0],
        ),
        legend=dict(
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=40, t=20, b=50),
    )

    st.plotly_chart(fig_trends, use_container_width=True)
else:
    st.info("Select participants above to view trend lines.")

# ── Chart 5: Stance Heatmap ───────────────────────────────────────────────
st.markdown("---")
st.markdown("## Stance Heatmap")
st.caption("Monthly stance scores for all participants (red = hawkish, blue = dovish)")

# Build heatmap matrix using numpy for proper NaN handling
import numpy as np

all_dates = sorted(set(d for entries in history.values() for d in [e["date"] for e in entries]))
heatmap_names = [short_name(p.name) for p in PARTICIPANTS]
full_names = [p.name for p in PARTICIPANTS]

z_data = np.full((len(full_names), len(all_dates)), np.nan)
for i, name in enumerate(full_names):
    entries = history.get(name, [])
    date_score = {e["date"]: e["score"] for e in entries}
    for j, d in enumerate(all_dates):
        if d in date_score:
            z_data[i][j] = date_score[d]

fig_heatmap = go.Figure(
    go.Heatmap(
        z=z_data.tolist(),
        x=all_dates,
        y=heatmap_names,
        colorscale=[
            [0.0, "#1e3a8a"],
            [0.2, "#3b82f6"],
            [0.35, "#93c5fd"],
            [0.5, "#f5f5f5"],
            [0.65, "#fca5a5"],
            [0.8, "#ef4444"],
            [1.0, "#991b1b"],
        ],
        zmid=0,
        zmin=-1,
        zmax=1,
        connectgaps=False,
        colorbar=dict(
            title=dict(text="Score", font=dict(color=FONT_COLOR)),
            tickfont=dict(color=FONT_COLOR),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["Dovish -1", "-0.5", "Neutral", "+0.5", "Hawkish +1"],
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Date: %{x}<br>"
            "Score: %{z}<br>"
            "<extra></extra>"
        ),
    )
)

fig_heatmap.update_layout(
    height=max(450, len(PARTICIPANTS) * 28),
    paper_bgcolor=BG_COLOR,
    plot_bgcolor=BG_COLOR,
    font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
    xaxis=dict(title="Date", gridcolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
    margin=dict(l=120, r=40, t=20, b=50),
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ── Detailed Table ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## Participant Details")

display_df = filtered[["name", "institution", "title", "score", "label", "voter"]].copy()
display_df.columns = ["Name", "Institution", "Title", "Score", "Stance", "2026 Voter"]
display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:+.3f}")
display_df["2026 Voter"] = display_df["2026 Voter"].apply(lambda x: "Yes" if x else "No")
display_df = display_df.sort_values("Score", ascending=False).reset_index(drop=True)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Name": st.column_config.TextColumn(width="large"),
        "Institution": st.column_config.TextColumn(width="medium"),
        "Title": st.column_config.TextColumn(width="medium"),
        "Score": st.column_config.TextColumn(width="small"),
        "Stance": st.column_config.TextColumn(width="small"),
        "2026 Voter": st.column_config.TextColumn(width="small"),
    },
)

# ── Download Buttons ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## Download Data")

dl_col1, dl_col2 = st.columns(2)

# Current stances CSV
current_csv_df = df[["name", "institution", "title", "voter", "score", "label"]].copy()
current_csv_df.columns = ["Name", "Institution", "Title", "2026 Voter", "Score", "Stance"]
current_csv_df = current_csv_df.sort_values("Score", ascending=False).reset_index(drop=True)

with dl_col1:
    st.download_button(
        label="Download Current Stances (CSV)",
        data=current_csv_df.to_csv(index=False),
        file_name=f"fomc_stances_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )

# Full history CSV
history_rows = []
for name, entries in history.items():
    for entry in entries:
        p = next((p for p in PARTICIPANTS if p.name == name), None)
        history_rows.append(
            {
                "Name": name,
                "Institution": p.institution if p else "",
                "Date": entry["date"],
                "Score": entry["score"],
                "Stance": entry["label"],
                "Source": entry.get("source", ""),
            }
        )
history_csv_df = pd.DataFrame(history_rows).sort_values(["Date", "Name"]).reset_index(drop=True)

with dl_col2:
    st.download_button(
        label="Download Full History (CSV)",
        data=history_csv_df.to_csv(index=False),
        file_name="fomc_stance_history.csv",
        mime="text/csv",
    )

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#64748b; font-size:0.85rem;'>"
    "FOMC Stance Tracker | Data from DuckDuckGo News, Federal Reserve RSS &amp; BIS Speeches | "
    "Keyword-based NLP classification | Not financial advice"
    "</div>",
    unsafe_allow_html=True,
)
