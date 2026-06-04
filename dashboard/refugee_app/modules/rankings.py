"""Graph 5 and Graph 6 ranking outputs."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs, render, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, MUTED, ORANGE
from refugee_app.modules.hero import empty_fig, fmt_num
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, aggregate_dimension
from refugee_app.services.serializers import safe_fig


def ranking_bar(df: pd.DataFrame, country_col: str, color: str, title: str) -> go.Figure:
    if df.empty:
        return empty_fig("No ranking data for this selection", 500)
    d = df.sort_values("value_observed", ascending=True).copy()
    labels = [f"{fmt_num(v)} | {s*100:.1f}%" if pd.notna(s) else fmt_num(v) for v, s in zip(d["value_observed"], d["share"])]
    xmax = float(d["value_observed"].max()) * 1.15 if len(d) else 1
    fig = go.Figure()
    fig.add_bar(x=[xmax] * len(d), y=d[country_col], orientation="h", marker_color="rgba(17,24,39,.07)", hoverinfo="skip", showlegend=False)
    fig.add_bar(x=d["value_observed"], y=d[country_col], orientation="h", marker_color=color, text=labels, textposition="outside", cliponaxis=False,
                hovertemplate="%{y}<br><b>%{x:,.0f}</b> people<extra></extra>", showlegend=False)
    fig.update_layout(barmode="overlay", height=520, margin={"l": 145, "r": 84, "t": 18, "b": 42}, title=None)
    fig.update_xaxes(title="Observed people", tickformat="~s", showgrid=True, gridcolor="rgba(17,24,39,.10)", range=[0, xmax * 1.08])
    fig.update_yaxes(title="", showgrid=False)
    return safe_fig(fig)


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def graph5_plot():
        d = aggregate_dimension(state.selected_stock(), "origin", state.top_n())
        return ranking_bar(d, "origin_country_std", ORANGE, "Graph 5")

    @output
    @render_widget
    def graph6_plot():
        d = aggregate_dimension(state.selected_stock(), "host", state.top_n())
        return ranking_bar(d, "host_country_std", GREEN, "Graph 6")

    @output
    @render.ui
    def ranking_note():
        return ui.div(
            ui.h3("Method note"),
            ui.p("Graph 5 and Graph 6 use the cleaned population-stock table. The default scope excludes IDPs from host-country ranking because IDPs are internal displacement, not cross-border hosting."),
            ui.p("Asylum application files remain flow datasets and support monthly trends, decisions and corridors."),
        )
