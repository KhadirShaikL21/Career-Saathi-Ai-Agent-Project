from __future__ import annotations

# Reusable Plotly visual helpers for Career Saathi.

from typing import Dict, List

import plotly.graph_objects as go


_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    template="plotly_dark",
    font=dict(family="'Inter', sans-serif"),
)


def plot_growth_line(years: List[int], values: List[float]) -> go.Figure:
    """Interactive line illustrating hiring momentum."""

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines+markers",
            line=dict(color="#7f5af0", width=4),
            marker=dict(size=10, color="#00c6ff", symbol="circle"),
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        title="Job Growth Trend (2020-2030)",
        margin=dict(t=60, l=10, r=10, b=10),
        hovermode="x unified",
    )
    return fig


def plot_salary_bars(levels: List[str], values: List[float]) -> go.Figure:
    """Bar chart comparing entry, mid, and senior salaries."""

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=levels,
            y=values,
            text=[f"{value} LPA" for value in values],
            textposition="outside",
            marker=dict(
                color=["#00c6ff", "#7f5af0", "#ff6ad5"],
                line=dict(color="rgba(255,255,255,0.4)", width=1),
            ),
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        title="Compensation Ladder (in LPA equivalent)",
        margin=dict(t=60, l=20, r=20, b=40),
        yaxis=dict(title="Salary"),
    )
    return fig


def plot_radar_chart(user_scores: Dict[str, int], required_scores: Dict[str, int]) -> go.Figure:
    """Return a radar chart comparing user skills against industry benchmarks."""

    categories = list(user_scores.keys())
    user_values = [user_scores[key] for key in categories]
    required_values = [required_scores.get(key, 0) for key in categories]
    categories_cycle = categories + [categories[0]] if categories else []
    user_cycle = user_values + [user_values[0]] if user_values else []
    required_cycle = required_values + [required_values[0]] if required_values else []

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=user_cycle,
            theta=categories_cycle,
            fill="toself",
            name="You",
            line=dict(color="#00c6ff"),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=required_cycle,
            theta=categories_cycle,
            fill="toself",
            name="Industry Benchmark",
            line=dict(color="#7f5af0"),
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showline=False)),
        margin=dict(t=60, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
    )
    return fig


def plot_industry_pie(labels: List[str], values: List[float]) -> go.Figure:
    """Pie chart for industry distribution."""

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            textinfo="label+percent",
            pull=[0.08] + [0] * (len(labels) - 1),
            marker=dict(colors=["#7f5af0", "#00c6ff", "#ff6ad5", "#f9ed69", "#6a7efc"]),
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        title="Top Industries Hiring",
        margin=dict(t=60, l=10, r=10, b=10),
        showlegend=False,
    )
    return fig
