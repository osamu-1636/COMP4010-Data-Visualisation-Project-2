"""Graph 4 Sankey: origin -> host/asylum country -> population status.

Purpose: restore a meaningful third chart type for the final dashboard while
keeping the view stable and readable in Shiny.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, build_corridors
from refugee_app.services.serializers import safe_fig


def _short(label: object, limit: int = 23) -> str:
    text = str(label)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _status_color(status: str) -> str:
    s = str(status).lower()
    if "refugee" in s:
        return GREEN
    if "asylum" in s:
        return PURPLE
    if "idp" in s or "internally" in s:
        return "#d99a2b"
    return "#94a3b8"


def _build_sankey(corridors: pd.DataFrame, height: int = 610) -> go.Figure:
    required = {"origin_country_std", "host_country_std", "population_type_std", "value_observed"}
    if corridors.empty or not required.issubset(corridors.columns):
        return empty_fig("No Sankey links for this selection", height)

    d = corridors.copy()
    d = d[d["value_observed"].fillna(0) > 0]
    if d.empty:
        return empty_fig("No positive Sankey links for this selection", height)

    # Keep the story readable; Sankey gets messy quickly.
    d = d.sort_values("value_observed", ascending=False).head(14)

    origin_host = (
        d.groupby(["origin_country_std", "host_country_std"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
        .sort_values("value_observed", ascending=False)
    )
    host_status = (
        d.groupby(["host_country_std", "population_type_std"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
        .sort_values("value_observed", ascending=False)
    )

    origins = origin_host["origin_country_std"].drop_duplicates().tolist()
    hosts = origin_host["host_country_std"].drop_duplicates().tolist()
    statuses = host_status["population_type_std"].drop_duplicates().tolist()
    labels = origins + hosts + statuses
    idx = {label: i for i, label in enumerate(labels)}

    source: list[int] = []
    target: list[int] = []
    value: list[float] = []
    link_color: list[str] = []

    for _, r in origin_host.iterrows():
        source.append(idx[r["origin_country_std"]])
        target.append(idx[r["host_country_std"]])
        value.append(float(r["value_observed"]))
        link_color.append("rgba(223,122,38,.28)")

    for _, r in host_status.iterrows():
        source.append(idx[r["host_country_std"]])
        target.append(idx[r["population_type_std"]])
        value.append(float(r["value_observed"]))
        link_color.append("rgba(47,102,197,.22)")

    node_color = [ORANGE] * len(origins) + [BLUE] * len(hosts) + [_status_color(s) for s in statuses]

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "label": [_short(x) for x in labels],
                "pad": 18,
                "thickness": 14,
                "color": node_color,
                "line": {"color": "rgba(17,24,39,.35)", "width": 0.6},
            },
            link={"source": source, "target": target, "value": value, "color": link_color},
        )
    )
    fig.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 12, "b": 10},
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        font={"size": 12, "color": "#111827"},
    )
    return safe_fig(fig)


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def sankey_plot():
        corridors = build_corridors(state.selected_stock(), min(state.top_n(), 18))
        return _build_sankey(corridors, height=610)
