#!/usr/bin/env python3
"""Generate a standalone HTML report of the FOMC Stance Tracker dashboard.

Usage:
    python generate_html.py                 # writes fomc_report_YYYY-MM-DD.html
    python generate_html.py -o report.html  # custom output path
"""

import argparse
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from fomc_tracker.participants import PARTICIPANTS
from fomc_tracker.historical_data import load_history

# ── Color Palette (mirrors dashboard.py) ────────────────────────────────
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
}
DIM_LABELS = {"policy": "Policy", "balance_sheet": "Bal. Sheet"}


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


def build_dataframe(history):
    """Build the main participant DataFrame."""
    rows = []
    for p in PARTICIPANTS:
        latest = None
        entries = history.get(p.name, [])
        if entries:
            latest = entries[-1]
        sc = latest.get("score", p.historical_lean) if latest else p.historical_lean
        sc_overall = latest.get("score", p.historical_lean) if latest else p.historical_lean
        sc_policy = latest.get("policy_score", sc_overall) if latest else p.historical_lean
        sc_bs = latest.get("balance_sheet_score", 0.0) if latest else p.historical_balance_sheet_lean
        rows.append(dict(
            name=p.name, short=last_name(p.name), inst=p.institution,
            title=p.title, voter=p.is_voter_2026, gov=p.is_governor,
            score=sc, label=score_label(sc),
            overall_score=sc_overall, policy_score=sc_policy,
            balance_sheet_score=sc_bs,
        ))
    df = pd.DataFrame(rows).sort_values("score", ascending=True).reset_index(drop=True)
    return df


def fig_spectrum(df):
    """Chart 1: Hawk-Dove Spectrum bar chart."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=list(range(len(df))),
        x=df["score"],
        orientation="h",
        marker=dict(color=[score_color(s) for s in df["score"]], opacity=0.85, line=dict(width=0)),
        text=[f"  {s:+.2f}" for s in df["score"]],
        textposition="outside",
        textfont=dict(size=11, color=FONT_DIM, family="Inter"),
        hovertemplate="<b>%{customdata[0]}</b><br>Score: %{x:+.3f}<br>%{customdata[1]}<extra></extra>",
        customdata=list(zip(df["name"], df["label"])),
    ))
    fig.add_vline(x=0, line_width=1.5, line_color="rgba(148,163,184,0.25)")
    fig.add_vline(x=1.5, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.2)")
    fig.add_vline(x=-1.5, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.2)")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=max(480, len(df) * 38),
        xaxis=dict(range=[-5.5, 5.5], gridcolor=GRID, zeroline=False,
                    tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
                    title=dict(text="← Dovish          Score          Hawkish →", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(tickvals=list(range(len(df))),
                   ticktext=[f"{r.short}  ({r.inst})" for _, r in df.iterrows()],
                   gridcolor=GRID),
        margin=dict(l=180, r=60, t=10, b=45),
        showlegend=False, bargap=0.35,
    )
    return fig


def fig_scatter_2d(df):
    """Chart: 2D Stance Map (Policy vs Balance Sheet)."""
    fig = go.Figure()
    # Quadrant shading
    fig.add_shape(type="rect", x0=0, x1=5.25, y0=0, y1=5.25, fillcolor="rgba(248,113,113,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=-5.25, x1=0, y0=0, y1=5.25, fillcolor="rgba(167,139,250,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=5.25, y0=-5.25, y1=0, fillcolor="rgba(251,191,36,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=-5.25, x1=0, y0=-5.25, y1=0, fillcolor="rgba(96,165,250,0.04)", line_width=0)
    for text, x, y in [
        ("Rate Hawk / BS Hawk", 3.75, 4.5), ("Rate Dove / BS Hawk", -3.75, 4.5),
        ("Rate Hawk / BS Dove", 3.75, -4.5), ("Rate Dove / BS Dove", -3.75, -4.5),
    ]:
        fig.add_annotation(text=text, x=x, y=y, showarrow=False,
                           font=dict(size=9, color="rgba(148,163,184,0.4)"))
    fig.add_trace(go.Scatter(
        x=df["policy_score"], y=df["balance_sheet_score"],
        mode="markers+text",
        marker=dict(size=[18 if v else 12 for v in df["voter"]],
                    color=[score_color(s) for s in df["overall_score"]],
                    line=dict(width=1.5, color="rgba(255,255,255,0.2)"), opacity=0.9),
        text=df["short"], textposition="top center", textfont=dict(size=9, color=FONT_DIM),
        hovertemplate="<b>%{customdata[0]}</b><br>Policy: %{x:+.3f}<br>Balance Sheet: %{y:+.3f}<br>Overall: %{customdata[1]:+.3f}<extra></extra>",
        customdata=list(zip(df["name"], df["overall_score"])),
        showlegend=False,
    ))
    fig.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.2)")
    fig.add_vline(x=0, line_width=1, line_color="rgba(148,163,184,0.2)")
    fig.update_layout(
        **PLOTLY_LAYOUT, height=520,
        xaxis=dict(range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
                    tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
                    title=dict(text="← Dovish (Rates)     Policy Score     Hawkish (Rates) →", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
                    tickvals=[-5.0, -3.0, -1.5, 0, 1.5, 3.0, 5.0],
                    title=dict(text="← Dovish (QE/Slow QT)     BS Score     Hawkish (QT) →", font=dict(size=11, color=FONT_DIM))),
        margin=dict(l=70, r=30, t=10, b=55),
    )
    return fig


def fig_composition(df):
    """Donut chart of committee composition."""
    hawks = len(df[df.label == "Hawkish"])
    neutrals = len(df[df.label == "Neutral"])
    doves = len(df[df.label == "Dovish"])
    fig = go.Figure(go.Pie(
        labels=["Hawkish", "Neutral", "Dovish"], values=[hawks, neutrals, doves], hole=0.6,
        marker=dict(colors=[HAWK, NEUTRAL_C, DOVE], line=dict(color="rgba(15,23,42,0.9)", width=3)),
        textinfo="label+value", textfont=dict(size=12, color="white", family="Inter"),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        pull=[0.02, 0, 0.02], sort=False,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, height=380, showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(
            text=f"<b style='font-size:1.8rem'>{len(df)}</b><br><span style='color:{FONT_DIM}'>members</span>",
            x=0.5, y=0.5, font=dict(size=14, color=FONT), showarrow=False,
        )],
    )
    return fig


def fig_voters_vs_alts(df):
    """Voters vs Alternates scatter. Returns (fig, va_trace_names)."""
    vdf = df[df.voter]
    adf = df[~df.voter]
    va = vdf["score"].mean()
    aa = adf["score"].mean()
    fig = go.Figure()
    va_trace_names = []
    for group_df, label in [(vdf, "Voters"), (adf, "Alternates")]:
        va_trace_names.append(list(group_df["name"]))
        fig.add_trace(go.Scatter(
            x=group_df["score"], y=[label] * len(group_df),
            mode="markers+text",
            marker=dict(size=14, color=[score_color(s) for s in group_df["score"]],
                        line=dict(width=1.5, color="rgba(255,255,255,0.15)")),
            text=group_df["short"], textposition="top center",
            textfont=dict(size=8, color=FONT_DIM),
            customdata=list(group_df["name"]),
            hovertemplate="<b>%{text}</b><br>Score: %{x:+.3f}<extra></extra>",
            showlegend=False,
        ))
    for avg, label in [(va, "Voters"), (aa, "Alternates")]:
        fig.add_trace(go.Scatter(
            x=[avg], y=[label], mode="markers",
            marker=dict(size=20, color=ACCENT, symbol="diamond", line=dict(width=2, color="white")),
            hovertemplate=f"Avg: {avg:+.3f}<extra></extra>", showlegend=False,
        ))
    fig.add_vline(x=0, line_width=1.5, line_color="rgba(148,163,184,0.2)")
    fig.update_layout(
        **PLOTLY_LAYOUT, height=380,
        xaxis=dict(range=[-5.25, 5.25], gridcolor=GRID, zeroline=False,
                    title=dict(text="← Dovish     Score     Hawkish →", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID),
        margin=dict(l=90, r=30, t=10, b=45),
    )
    return fig, va_trace_names


def _trends_base_layout():
    """Shared layout properties for trend charts."""
    return dict(
        **PLOTLY_LAYOUT, height=520,
        xaxis=dict(gridcolor=GRID, title=dict(text="Date", font=dict(size=11, color=FONT_DIM))),
        yaxis=dict(gridcolor=GRID, range=[-5.25, 5.25], tickvals=[-5, -3, -1.5, 0, 1.5, 3, 5],
                   title=dict(text="Stance Score", font=dict(size=11, color=FONT_DIM))),
        legend=dict(bgcolor="rgba(15,23,42,0.7)", bordercolor="rgba(148,163,184,0.1)", borderwidth=1,
                    font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=55, r=30, t=40, b=45),
    )


def _trends_base_fig():
    """Create a trend figure with background zones and reference lines."""
    fig = go.Figure()
    fig.add_hrect(y0=1.5, y1=5.0, fillcolor="rgba(248,113,113,0.05)", line_width=0,
                  annotation_text="Hawkish zone", annotation_position="top left",
                  annotation_font=dict(color="rgba(248,113,113,0.35)", size=10))
    fig.add_hrect(y0=-5.0, y1=-1.5, fillcolor="rgba(96,165,250,0.05)", line_width=0,
                  annotation_text="Dovish zone", annotation_position="bottom left",
                  annotation_font=dict(color="rgba(96,165,250,0.35)", size=10))
    return fig


def _trends_add_ref_lines(fig):
    fig.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.2)")
    fig.add_hline(y=1.5, line_width=1, line_dash="dot", line_color="rgba(248,113,113,0.15)")
    fig.add_hline(y=-1.5, line_width=1, line_dash="dot", line_color="rgba(96,165,250,0.15)")


def fig_trends(history):
    """Aggregate stance trends line chart.

    Returns (fig, trace_names) where trace_names maps curve index to full name.
    """
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2
    fig = _trends_base_fig()
    names = [p.name for p in PARTICIPANTS]
    trace_names = []
    i = 0
    for name in names:
        entries = history.get(name, [])
        if not entries:
            continue
        trace_names.append(name)
        c = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=[e["date"] for e in entries],
            y=[e.get("score", 0) for e in entries],
            mode="lines+markers", name=last_name(name),
            line=dict(width=2.5, color=c, shape="spline"),
            marker=dict(size=8, color=c, line=dict(width=1, color="rgba(255,255,255,0.2)")),
            hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
        ))
        i += 1
    _trends_add_ref_lines(fig)
    fig.update_layout(**_trends_base_layout())
    return fig, trace_names


def fig_trends_dimensions(history):
    """Policy & Balance Sheet stance trends (two lines per participant).

    Returns (fig, trace_names) where trace_names maps curve index to full name
    (both traces for a participant map to the same name).
    """
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Set2
    fig = _trends_base_fig()
    names = [p.name for p in PARTICIPANTS]
    trace_names = []
    i = 0
    for name in names:
        entries = history.get(name, [])
        if not entries:
            continue
        trace_names.append(name)
        trace_names.append(name)
        c = palette[i % len(palette)]
        ln = last_name(name)
        fig.add_trace(go.Scatter(
            x=[e["date"] for e in entries],
            y=[e.get("policy_score", e.get("score", 0)) for e in entries],
            mode="lines+markers", name=f"{ln} (Pol.)",
            line=dict(width=2.5, color=c, shape="spline"),
            marker=dict(size=8, color=c, symbol="circle",
                        line=dict(width=1, color="rgba(255,255,255,0.2)")),
            hovertemplate=f"<b>{name}</b> — Policy<br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[e["date"] for e in entries],
            y=[e.get("balance_sheet_score", 0) for e in entries],
            mode="lines+markers", name=f"{ln} (B.S.)",
            line=dict(width=2.5, color=c, shape="spline", dash="dash"),
            marker=dict(size=8, color=c, symbol="diamond",
                        line=dict(width=1, color="rgba(255,255,255,0.2)")),
            hovertemplate=f"<b>{name}</b> — Balance Sheet<br>Date: %{{x}}<br>Score: %{{y:+.3f}}<br><i>Click for details</i><extra></extra>",
        ))
        i += 1
    _trends_add_ref_lines(fig)
    fig.update_layout(**_trends_base_layout())
    return fig, trace_names


def fig_heatmap(history):
    """Stance heatmap across all participants and dates."""
    all_dates = sorted({d for entries in history.values() for d in [e["date"] for e in entries]})
    h_names = [last_name(p.name) for p in PARTICIPANTS]
    f_names = [p.name for p in PARTICIPANTS]
    z = np.full((len(f_names), len(all_dates)), np.nan)
    for i, name in enumerate(f_names):
        ds = {e["date"]: e.get("score", 0) for e in history.get(name, [])}
        for j, d in enumerate(all_dates):
            if d in ds:
                z[i][j] = ds[d]
    fig = go.Figure(go.Heatmap(
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
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=max(450, len(PARTICIPANTS) * 30),
        xaxis=dict(gridcolor=GRID, side="top"),
        yaxis=dict(gridcolor=GRID, autorange="reversed"),
        margin=dict(l=110, r=30, t=30, b=20),
    )
    return fig


def build_evidence_html(df, history):
    """Build HTML for evidence cards."""
    sections = []
    for _, row in df.iterrows():
        entries = history.get(row["name"], [])
        latest = entries[-1] if entries else None
        ev_list = latest.get("evidence", []) if latest else []
        if not ev_list:
            continue

        clr = score_color(row["score"])
        cards_html = ""
        for ev in ev_list:
            title_text = ev.get("title", "Untitled")
            url = ev.get("url", "")
            quote = ev.get("quote", "")
            keywords = ev.get("keywords", [])
            directions = ev.get("directions", [])
            dimensions = ev.get("dimensions", ["policy"] * len(keywords))
            src_type = SOURCE_LABELS.get(ev.get("source_type", ""), ev.get("source_type", ""))
            ev_score = ev.get("score", 0)

            title_html = f'<a href="{url}" target="_blank">{title_text}</a>' if url else title_text
            quote_html = f'<p class="ev-quote">&ldquo;{quote}&rdquo;</p>' if quote else ""
            tags_html = ""
            for kw, direction, dim in zip(keywords, directions, dimensions):
                tag_cls = "ev-tag-hawk" if direction == "hawkish" else "ev-tag-dove"
                dim_label = DIM_LABELS.get(dim, dim)
                tags_html += f'<span class="ev-tag {tag_cls}">{kw}</span>'
                tags_html += f'<span class="ev-tag ev-tag-dim">{dim_label}</span>'
            if src_type:
                tags_html += f'<span class="ev-tag ev-tag-src">{src_type}</span>'
            ev_clr = score_color(ev_score)
            tags_html += f'<span class="ev-tag" style="background:{ev_clr}18;color:{ev_clr};border:1px solid {ev_clr}30">{ev_score:+.1f}</span>'

            cards_html += f"""<div class="ev-card">
                <p class="ev-title">{title_html}</p>
                {quote_html}
                <div class="ev-tags">{tags_html}</div>
            </div>"""

        sections.append(f"""
        <details class="ev-details">
            <summary style="cursor:pointer;padding:0.6rem 0;font-weight:600;color:#e2e8f0;font-size:0.95rem;
                border-bottom:1px solid rgba(148,163,184,0.08);list-style:none">
                <span style="margin-right:0.5rem;color:{clr}">&#9679;</span>
                {row['name']} &mdash; {row['label']} ({row['score']:+.3f})
            </summary>
            <div style="padding:0.5rem 0">{cards_html}</div>
        </details>""")
    return "\n".join(sections)


def build_table_html(df):
    """Build the participant details table."""
    tbl = df[["name", "inst", "title", "score", "label", "policy_score", "balance_sheet_score", "voter"]].copy()
    tbl = tbl.sort_values("score", ascending=False).reset_index(drop=True)
    rows_html = ""
    for _, r in tbl.iterrows():
        clr = score_color(r["score"])
        voter_badge = '<span style="color:#fbbf24;font-weight:700">Yes</span>' if r["voter"] else '<span style="color:#475569">No</span>'
        rows_html += f"""<tr>
            <td style="font-weight:600">{r['name']}</td>
            <td>{r['inst']}</td>
            <td>{r['title']}</td>
            <td style="color:{clr};font-weight:700;font-variant-numeric:tabular-nums">{r['score']:+.3f}</td>
            <td style="color:{clr}">{r['label']}</td>
            <td style="font-variant-numeric:tabular-nums">{r['policy_score']:+.3f}</td>
            <td style="font-variant-numeric:tabular-nums">{r['balance_sheet_score']:+.3f}</td>
            <td>{voter_badge}</td>
        </tr>"""
    return f"""<table class="data-table">
        <thead><tr>
            <th>Name</th><th>Institution</th><th>Title</th>
            <th>Score</th><th>Stance</th><th>Policy</th><th>BS Score</th><th>2026 Voter</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>"""


def generate_html(output_path: str):
    """Generate the full standalone HTML report."""
    history = load_history()
    df = build_dataframe(history)
    hawks = df[df.label == "Hawkish"]
    neutrals = df[df.label == "Neutral"]
    doves = df[df.label == "Dovish"]
    avg_score = df["score"].mean()

    hawk_pct = f"{len(hawks)/len(df)*100:.0f}%"
    dove_pct = f"{len(doves)/len(df)*100:.0f}%"
    balance = len(hawks) - len(doves)
    bal_str = f"+{balance}" if balance > 0 else str(balance)

    # Generate Plotly chart HTML (with CDN for plotly.js — first chart includes it)
    chart_spectrum = fig_spectrum(df).to_html(full_html=False, include_plotlyjs="cdn", div_id="spectrum-chart")
    chart_scatter = fig_scatter_2d(df).to_html(full_html=False, include_plotlyjs=False, div_id="scatter-chart")
    chart_composition = fig_composition(df).to_html(full_html=False, include_plotlyjs=False)
    voters_fig, va_trace_names = fig_voters_vs_alts(df)
    chart_voters = voters_fig.to_html(full_html=False, include_plotlyjs=False, div_id="voters-chart")
    trends_fig, trace_names = fig_trends(history)
    chart_trends = trends_fig.to_html(full_html=False, include_plotlyjs=False, div_id="trends-chart")
    trends_dim_fig, trace_names_dim = fig_trends_dimensions(history)
    chart_trends_dim = trends_dim_fig.to_html(full_html=False, include_plotlyjs=False, div_id="trends-chart-dim")
    chart_heatmap = fig_heatmap(history).to_html(full_html=False, include_plotlyjs=False, div_id="heatmap-chart")

    evidence_html = build_evidence_html(df, history)
    table_html = build_table_html(df)
    date_str = datetime.now().strftime("%B %d, %Y")

    bal_text = "Hawks outnumber" if balance > 0 else "Doves outnumber" if balance < 0 else "Evenly split"

    # Build history JSON for click-to-inspect (only entries with evidence)
    history_json = json.dumps(history, default=str)
    trace_names_json = json.dumps(trace_names)
    trace_names_dim_json = json.dumps(trace_names_dim)
    source_labels_json = json.dumps(SOURCE_LABELS)
    dim_labels_json = json.dumps(DIM_LABELS)

    # Spectrum: ordered names matching bar indices
    spectrum_names_json = json.dumps(list(df["name"]))
    # Scatter: ordered names matching point indices
    scatter_names_json = json.dumps(list(df["name"]))
    # Voters/Alternates: nested list of names per trace
    va_trace_names_json = json.dumps(va_trace_names)
    # Heatmap: last_name → full_name mapping
    heatmap_name_map = {last_name(p.name): p.name for p in PARTICIPANTS}
    heatmap_name_map_json = json.dumps(heatmap_name_map)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FOMC Stance Tracker — {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0f172a; color: #e2e8f0;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{
    max-width: 1280px; margin: 0 auto;
    padding: 2.5rem 2rem 3rem 2rem;
  }}
  h1, h2, h3, h4 {{ font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }}

  /* Hero */
  .hero {{ padding: 2rem 0 1rem 0; }}
  .hero-title {{
    font-size: 2.4rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; margin: 0;
    background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .hero-sub {{ font-size: 1.05rem; color: #64748b; margin: 0.6rem 0 0 0; font-weight: 400; line-height: 1.5; }}
  .hero-date {{
    display: inline-block; margin-top: 0.8rem; padding: 0.3rem 0.8rem;
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px; color: #818cf8; font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.03em; text-transform: uppercase;
  }}

  /* Metric Cards */
  .metric-row {{ display: flex; gap: 1rem; margin: 1.5rem 0 2rem 0; flex-wrap: wrap; }}
  .m-card {{
    flex: 1; min-width: 140px;
    background: linear-gradient(145deg, rgba(15,23,42,0.6) 0%, rgba(30,41,59,0.4) 100%);
    border: 1px solid rgba(148,163,184,0.08); border-radius: 16px; padding: 1.4rem 1rem;
    text-align: center; backdrop-filter: blur(10px);
  }}
  .m-label {{ font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin: 0 0 0.5rem 0; }}
  .m-value {{ font-size: 2.6rem; font-weight: 800; margin: 0; line-height: 1; }}
  .m-sub {{ font-size: 0.72rem; color: #475569; margin: 0.4rem 0 0 0; font-weight: 500; }}
  .m-hawk .m-value {{ color: #f87171; }}
  .m-neut .m-value {{ color: #94a3b8; }}
  .m-dove .m-value {{ color: #60a5fa; }}
  .m-bal .m-value {{ color: #fbbf24; }}
  .m-avg .m-value {{ color: #a78bfa; font-size: 2.2rem; }}

  /* Section Headers */
  .section-hdr {{ font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; margin: 0 0 0.15rem 0; color: #f1f5f9; }}
  .section-sub {{ font-size: 0.82rem; color: #64748b; margin: 0 0 1.2rem 0; font-weight: 400; }}
  .divider {{ border: none; border-top: 1px solid rgba(148,163,184,0.08); margin: 2.5rem 0; }}

  /* Side-by-side */
  .row-2col {{ display: flex; gap: 2rem; flex-wrap: wrap; }}
  .row-2col > div {{ flex: 1; min-width: 400px; }}

  /* Legend */
  .legend {{ display: flex; gap: 1.5rem; margin: 0.5rem 0 0 0; }}
  .legend-item {{ display: flex; align-items: center; gap: 0.4rem; font-size: 0.82rem; color: #94a3b8; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }}

  /* Evidence */
  .ev-card {{
    background: linear-gradient(145deg, rgba(15,23,42,0.5) 0%, rgba(30,41,59,0.3) 100%);
    border: 1px solid rgba(148,163,184,0.08); border-radius: 12px; padding: 1rem 1.2rem; margin: 0.5rem 0;
  }}
  .ev-title {{ font-size: 0.88rem; font-weight: 600; color: #e2e8f0; margin: 0 0 0.3rem 0; line-height: 1.4; }}
  .ev-title a {{ color: #818cf8; text-decoration: none; }}
  .ev-title a:hover {{ text-decoration: underline; }}
  .ev-quote {{
    font-size: 0.8rem; color: #94a3b8; font-style: italic; margin: 0.4rem 0;
    padding-left: 0.8rem; border-left: 2px solid rgba(148,163,184,0.15); line-height: 1.5;
  }}
  .ev-tags {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.4rem; }}
  .ev-tag {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.02em; }}
  .ev-tag-hawk {{ background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.2); }}
  .ev-tag-dove {{ background: rgba(96,165,250,0.12); color: #60a5fa; border: 1px solid rgba(96,165,250,0.2); }}
  .ev-tag-src {{ background: rgba(148,163,184,0.1); color: #94a3b8; border: 1px solid rgba(148,163,184,0.15); }}
  .ev-tag-dim {{ background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.2); }}

  .ev-details {{ margin: 0.3rem 0; }}
  .ev-details summary::-webkit-details-marker {{ display: none; }}
  .ev-details summary::before {{ content: "▸ "; color: #475569; }}
  .ev-details[open] summary::before {{ content: "▾ "; }}

  /* Click-to-inspect detail panels */
  #trend-detail, #spectrum-detail, #scatter-detail, #voters-detail, #heatmap-detail {{
    margin: 1rem 0 0.5rem 0;
    transition: opacity 0.2s;
  }}
  #trend-detail:empty, #spectrum-detail:empty, #scatter-detail:empty,
  #voters-detail:empty, #heatmap-detail:empty {{ display: none; }}
  .td-header {{
    background: linear-gradient(145deg, rgba(15,23,42,0.7), rgba(30,41,59,0.5));
    border-radius: 16px; padding: 1.5rem 1.8rem; margin-bottom: 0.5rem;
  }}
  .td-header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }}
  .td-name {{ font-size: 1.15rem; font-weight: 700; color: #f1f5f9; }}
  .td-badge {{
    font-size: 0.8rem; padding: 0.25rem 0.7rem; border-radius: 20px; font-weight: 600;
  }}
  .td-meta {{ font-size: 0.78rem; color: #64748b; margin: 0; }}
  .td-hint {{ font-size: 0.75rem; color: #475569; text-align: center; margin: 0.5rem 0; font-style: italic; }}

  /* Trend toggle */
  .trend-toggle {{
    display: inline-flex; gap: 0; border-radius: 8px; overflow: hidden;
    border: 1px solid rgba(148,163,184,0.15); margin-bottom: 0.8rem;
  }}
  .trend-toggle button {{
    padding: 0.4rem 1rem; font-size: 0.8rem; font-weight: 600; cursor: pointer;
    border: none; font-family: inherit; transition: all 0.15s ease;
    background: rgba(30,41,59,0.5); color: #94a3b8;
  }}
  .trend-toggle button:hover {{ background: rgba(51,65,85,0.5); }}
  .trend-toggle button.active {{
    background: rgba(99,102,241,0.18); color: #818cf8;
  }}

  /* Data Table */
  .data-table {{
    width: 100%; border-collapse: collapse; font-size: 0.85rem;
  }}
  .data-table th {{
    text-align: left; padding: 0.7rem 0.8rem; font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px; color: #64748b;
    border-bottom: 1px solid rgba(148,163,184,0.15);
  }}
  .data-table td {{
    padding: 0.6rem 0.8rem; border-bottom: 1px solid rgba(148,163,184,0.06); color: #cbd5e1;
  }}
  .data-table tr:hover td {{ background: rgba(148,163,184,0.04); }}

  /* Footer */
  .foot {{
    text-align: center; color: #475569; font-size: 0.75rem; padding: 1.5rem 0 0.5rem 0; line-height: 1.7;
  }}
  .foot a {{ color: #818cf8; text-decoration: none; }}

  @media (max-width: 768px) {{
    .container {{ padding: 1.5rem 1rem; }}
    .hero-title {{ font-size: 1.6rem; }}
    .metric-row {{ flex-direction: column; }}
    .row-2col {{ flex-direction: column; }}
    .row-2col > div {{ min-width: 100%; }}
    .m-value {{ font-size: 2rem; }}
  }}
</style>
</head>
<body>
<div class="container">

<!-- Hero -->
<div class="hero">
    <p class="hero-title">FOMC Participant<br>Stance Tracker</p>
    <p class="hero-sub">Hawkish / dovish classification of Federal Reserve officials
    based on recent news, speeches, and public statements.</p>
    <span class="hero-date">Report generated {date_str}</span>
</div>

<!-- Legend -->
<div class="legend" style="margin-bottom:0.5rem">
    <div class="legend-item"><div class="legend-dot" style="background:{HAWK}"></div>Hawkish (&gt; +1.5)</div>
    <div class="legend-item"><div class="legend-dot" style="background:{NEUTRAL_C}"></div>Neutral (-1.5 to +1.5)</div>
    <div class="legend-item"><div class="legend-dot" style="background:{DOVE}"></div>Dovish (&lt; -1.5)</div>
</div>

<!-- Metrics -->
<div class="metric-row">
    <div class="m-card m-hawk"><p class="m-label">Hawkish</p><p class="m-value">{len(hawks)}</p><p class="m-sub">{hawk_pct} of committee</p></div>
    <div class="m-card m-neut"><p class="m-label">Neutral</p><p class="m-value">{len(neutrals)}</p><p class="m-sub">{len(neutrals)} centrist</p></div>
    <div class="m-card m-dove"><p class="m-label">Dovish</p><p class="m-value">{len(doves)}</p><p class="m-sub">{dove_pct} of committee</p></div>
    <div class="m-card m-bal"><p class="m-label">Hawk-Dove Balance</p><p class="m-value">{bal_str}</p><p class="m-sub">{bal_text}</p></div>
    <div class="m-card m-avg"><p class="m-label">Committee Avg</p><p class="m-value">{avg_score:+.2f}</p><p class="m-sub">{score_label(avg_score).lower()} lean</p></div>
</div>

<!-- Chart 1: Spectrum -->
<hr class="divider">
<p class="section-hdr">Hawk-Dove Spectrum</p>
<p class="section-sub">All participants ranked from most dovish to most hawkish &bull;
<span style="color:#fbbf24">&#9733;</span> = 2026 voting member &bull; Click any bar for details</p>
{chart_spectrum}
<div id="spectrum-detail"></div>

<!-- Chart 2: 2D Scatter -->
<hr class="divider">
<p class="section-hdr">2D Stance Map &mdash; Policy vs Balance Sheet</p>
<p class="section-sub">Each participant plotted by interest rate stance (x) and balance sheet stance (y) &bull; Dot size indicates voter status &bull; Click any point for details</p>
{chart_scatter}
<div id="scatter-detail"></div>

<!-- Composition + Voters (side by side) -->
<hr class="divider">
<div class="row-2col">
    <div>
        <p class="section-hdr">Committee Composition</p>
        <p class="section-sub">Stance breakdown across all participants</p>
        {chart_composition}
    </div>
    <div>
        <p class="section-hdr">Voters vs Alternates</p>
        <p class="section-sub">Comparing stance distributions &bull;
        <span style="color:#fbbf24">&#9670;</span> = group average &bull; Click any point for details</p>
        {chart_voters}
        <div id="voters-detail"></div>
    </div>
</div>

<!-- Trends -->
<hr class="divider">
<p class="section-hdr">Stance Trends</p>
<p class="section-sub">How each participant&rsquo;s stance has evolved over recent months &bull; Click any data point for details</p>
<div class="trend-toggle" id="trend-toggle">
  <button class="active" data-mode="aggregate" onclick="switchTrendMode('aggregate')">Aggregate</button>
  <button data-mode="dimensions" onclick="switchTrendMode('dimensions')">Policy &amp; Balance Sheet</button>
</div>
<div id="trends-wrap-agg">{chart_trends}</div>
<div id="trends-wrap-dim" style="display:none">{chart_trends_dim}</div>
<p class="td-hint">Click a data point on the chart above to see evidence and sources</p>
<div id="trend-detail"></div>

<script>
(function() {{
  var historyData = {history_json};
  var traceNamesAgg = {trace_names_json};
  var traceNamesDim = {trace_names_dim_json};
  var sourceLabels = {source_labels_json};
  var dimLabels = {dim_labels_json};
  var spectrumNames = {spectrum_names_json};
  var scatterNames = {scatter_names_json};
  var vaTraceNames = {va_trace_names_json};
  var heatmapNameMap = {heatmap_name_map_json};

  var currentMode = 'aggregate';

  function scoreColor(s) {{
    if (s > 1.5) return '#f87171';
    if (s < -1.5) return '#60a5fa';
    return '#64748b';
  }}
  function scoreLabel(s) {{
    if (s > 1.5) return 'Hawkish';
    if (s < -1.5) return 'Dovish';
    return 'Neutral';
  }}
  function esc(str) {{
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }}

  function buildDetailHtml(name, clickedDate, clickedScore) {{
    var entries = historyData[name] || [];
    var entry = null;
    if (clickedDate) {{
      for (var i = 0; i < entries.length; i++) {{
        if (entries[i].date === clickedDate) {{ entry = entries[i]; break; }}
      }}
    }}
    if (!entry && entries.length > 0) {{
      entry = entries[entries.length - 1];
    }}

    var sc = (clickedScore !== null && clickedScore !== undefined) ? clickedScore : (entry ? entry.score || 0 : 0);
    var lbl = scoreLabel(sc);
    var clr = scoreColor(sc);
    var policyScore = entry ? (entry.policy_score || 0) : 0;
    var bsScore = entry ? (entry.balance_sheet_score || 0) : 0;
    var source = entry ? (entry.source || 'n/a') : 'n/a';
    var dateStr = clickedDate || (entry ? entry.date || '' : '');

    var html = '<div class="td-header" style="border:1px solid ' + clr + '40">'
      + '<div class="td-header-row">'
      + '<span class="td-name">' + esc(name) + '</span>'
      + '<span class="td-badge" style="background:' + clr + '18;color:' + clr + ';border:1px solid ' + clr + '30">'
      + lbl + ' &nbsp; ' + (sc >= 0 ? '+' : '') + sc.toFixed(3) + '</span>'
      + '</div>'
      + '<p class="td-meta">' + esc(dateStr)
      + ' &nbsp;&bull;&nbsp; Source: ' + esc(source)
      + ' &nbsp;&bull;&nbsp; Policy: ' + (policyScore >= 0 ? '+' : '') + policyScore.toFixed(2)
      + ' &nbsp;|&nbsp; Balance Sheet: ' + (bsScore >= 0 ? '+' : '') + bsScore.toFixed(2)
      + '</p></div>';

    var evList = entry ? (entry.evidence || []) : [];
    if (evList.length > 0) {{
      for (var j = 0; j < evList.length; j++) {{
        var ev = evList[j];
        var evTitle = ev.title || 'Untitled';
        var evUrl = ev.url || '';
        var evQuote = ev.quote || '';
        var evKws = ev.keywords || [];
        var evDirs = ev.directions || [];
        var evDims = ev.dimensions || [];
        var evSrcType = sourceLabels[ev.source_type] || ev.source_type || '';
        var evScore = ev.score || 0;

        var titleHtml = evUrl
          ? '<a href="' + esc(evUrl) + '" target="_blank">' + esc(evTitle) + '</a>'
          : esc(evTitle);
        var quoteHtml = evQuote
          ? '<p class="ev-quote">&ldquo;' + esc(evQuote) + '&rdquo;</p>'
          : '';

        var tagsHtml = '';
        for (var k = 0; k < evKws.length; k++) {{
          var tagCls = (evDirs[k] === 'hawkish') ? 'ev-tag-hawk' : 'ev-tag-dove';
          var dimLbl = dimLabels[evDims[k]] || evDims[k] || '';
          tagsHtml += '<span class="ev-tag ' + tagCls + '">' + esc(evKws[k]) + '</span>';
          if (dimLbl) tagsHtml += '<span class="ev-tag ev-tag-dim">' + esc(dimLbl) + '</span>';
        }}
        if (evSrcType) {{
          tagsHtml += '<span class="ev-tag ev-tag-src">' + esc(evSrcType) + '</span>';
        }}
        var evClr = scoreColor(evScore);
        tagsHtml += '<span class="ev-tag" style="background:' + evClr + '18;color:' + evClr
          + ';border:1px solid ' + evClr + '30">' + (evScore >= 0 ? '+' : '') + evScore.toFixed(1) + '</span>';

        html += '<div class="ev-card">'
          + '<p class="ev-title">' + titleHtml + '</p>'
          + quoteHtml
          + '<div class="ev-tags">' + tagsHtml + '</div>'
          + '</div>';
      }}
    }} else if (source === 'seed') {{
      html += '<p style="color:#64748b;font-size:0.82rem;font-style:italic;margin:0.5rem 0">'
        + 'This is a seed/baseline data point — no news evidence available.</p>';
    }} else {{
      html += '<p style="color:#64748b;font-size:0.82rem;font-style:italic;margin:0.5rem 0">'
        + 'No evidence articles stored for this data point.</p>';
    }}
    return html;
  }}

  function showDetail(targetId, name, date, score) {{
    var el = document.getElementById(targetId);
    if (!el) return;
    el.innerHTML = buildDetailHtml(name, date, score);
    el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
  }}

  /* Trend charts click handler */
  function handleTrendClick(traceNames, data) {{
    if (!data || !data.points || !data.points.length) return;
    var pt = data.points[0];
    if (pt.curveNumber >= traceNames.length) return;
    var name = traceNames[pt.curveNumber];
    showDetail('trend-detail', name, pt.x, pt.y);
  }}

  /* Spectrum bar chart */
  var spectrumEl = document.getElementById('spectrum-chart');
  if (spectrumEl) {{
    spectrumEl.on('plotly_click', function(data) {{
      if (!data || !data.points || !data.points.length) return;
      var pt = data.points[0];
      var idx = pt.pointNumber;
      if (idx < spectrumNames.length) {{
        showDetail('spectrum-detail', spectrumNames[idx], null, null);
      }}
    }});
  }}

  /* 2D Scatter chart */
  var scatterEl = document.getElementById('scatter-chart');
  if (scatterEl) {{
    scatterEl.on('plotly_click', function(data) {{
      if (!data || !data.points || !data.points.length) return;
      var pt = data.points[0];
      var idx = pt.pointNumber;
      if (idx < scatterNames.length) {{
        showDetail('scatter-detail', scatterNames[idx], null, null);
      }}
    }});
  }}

  /* Voters vs Alternates chart */
  var votersEl = document.getElementById('voters-chart');
  if (votersEl) {{
    votersEl.on('plotly_click', function(data) {{
      if (!data || !data.points || !data.points.length) return;
      var pt = data.points[0];
      var curve = pt.curveNumber;
      var idx = pt.pointNumber;
      if (curve < vaTraceNames.length && idx < vaTraceNames[curve].length) {{
        showDetail('voters-detail', vaTraceNames[curve][idx], null, null);
      }}
    }});
  }}

  /* Trend charts */
  var trendEl = document.getElementById('trends-chart');
  var trendDimEl = document.getElementById('trends-chart-dim');

  if (trendEl) {{
    trendEl.on('plotly_click', function(data) {{ handleTrendClick(traceNamesAgg, data); }});
  }}
  if (trendDimEl) {{
    trendDimEl.on('plotly_click', function(data) {{ handleTrendClick(traceNamesDim, data); }});
  }}

  /* Heatmap chart */
  var heatmapEl = document.getElementById('heatmap-chart');
  if (heatmapEl) {{
    heatmapEl.on('plotly_click', function(data) {{
      if (!data || !data.points || !data.points.length) return;
      var pt = data.points[0];
      var shortName = pt.y;
      var clickedDate = pt.x;
      var fullName = heatmapNameMap[shortName] || '';
      if (fullName) {{
        showDetail('heatmap-detail', fullName, clickedDate, pt.z);
      }}
    }});
  }}

  /* Toggle logic */
  window.switchTrendMode = function(mode) {{
    currentMode = mode;
    var aggWrap = document.getElementById('trends-wrap-agg');
    var dimWrap = document.getElementById('trends-wrap-dim');
    var btns = document.querySelectorAll('#trend-toggle button');
    btns.forEach(function(b) {{ b.classList.remove('active'); }});
    document.querySelector('#trend-toggle button[data-mode="' + mode + '"]').classList.add('active');
    if (mode === 'aggregate') {{
      aggWrap.style.display = '';
      dimWrap.style.display = 'none';
    }} else {{
      aggWrap.style.display = 'none';
      dimWrap.style.display = '';
    }}
    document.getElementById('trend-detail').innerHTML = '';
  }};
}})();
</script>

<!-- Heatmap -->
<hr class="divider">
<p class="section-hdr">Stance Heatmap</p>
<p class="section-sub">Monthly stance scores across all participants &bull; Click any cell for details</p>
{chart_heatmap}
<div id="heatmap-detail"></div>

<!-- Table -->
<hr class="divider">
<p class="section-hdr">Participant Details</p>
<p class="section-sub">Full roster with current stance scores across all dimensions</p>
{table_html}

<!-- Evidence -->
<hr class="divider">
<p class="section-hdr">Evidence &amp; Sources</p>
<p class="section-sub">News articles, speeches, and quotes supporting each participant&rsquo;s stance classification</p>
{evidence_html}

<!-- Footer -->
<hr class="divider">
<div class="foot">
    FOMC Stance Tracker &middot;
    Data from DuckDuckGo News, Federal Reserve RSS &amp;
    <a href="https://www.bis.org/cbspeeches/index.htm">BIS Central Banker Speeches</a>
    &middot; Keyword-based NLP classification<br>
    Dual-dimension analysis: Policy (rates) + Balance Sheet (QT/QE)<br>
    This tool is for informational purposes only and does not constitute financial advice.
</div>

</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written to: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate standalone FOMC Stance Tracker HTML report")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file path")
    args = parser.parse_args()
    out = args.output or f"fomc_report_{datetime.now():%Y-%m-%d}.html"
    generate_html(out)
