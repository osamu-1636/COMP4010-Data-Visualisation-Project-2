"""Executive overview outputs: KPI cards, trend, map and insight text."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs, render, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, MUTED, ORANGE, PURPLE
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState
from refugee_app.services.serializers import safe_fig
from refugee_app.ui.theme import ACCENTS


def fmt_num(x):
    if x is None or pd.isna(x):
        return "-"
    x = float(x)
    ax = abs(x)
    if ax >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f}B"
    if ax >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if ax >= 1_000:
        return f"{x/1_000:.0f}K"
    return f"{x:,.0f}"


def empty_fig(msg: str, height: int = 360) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.55, xref="paper", yref="paper", showarrow=False, font={"size": 15, "color": MUTED})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=height, margin={"l": 0, "r": 0, "t": 0, "b": 0})
    return safe_fig(fig)


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render.text
    def kpi_cross_border():
        return fmt_num(state.kpis()["total"])

    @output
    @render.text
    def kpi_refugees():
        return fmt_num(state.kpis()["refugees"])

    @output
    @render.text
    def kpi_idps():
        return fmt_num(state.kpis()["idps"])

    @output
    @render.text
    def kpi_asylum():
        return fmt_num(state.kpis()["asylum"])

    @output
    @render.text
    def kpi_countries():
        return fmt_num(state.kpis()["countries"])

    @output
    @render_widget
    def trend_plot():
        d = state.stock_all_years_same_filters()
        if d.empty:
            return empty_fig("No trend data for this selection", 430)
        annual = d.groupby(["year", "population_type_std"], as_index=False).agg(value_observed=("value_observed", "sum"))
        fig = px.line(annual, x="year", y="value_observed", color="population_type_std", markers=True,
                      color_discrete_map={"Refugees": GREEN, "Asylum-seekers": PURPLE, "Others of concern": ORANGE, "IDPs": ORANGE})
        fig.update_layout(height=430, margin={"l": 48, "r": 20, "t": 30, "b": 42}, legend_title_text="Population type")
        fig.update_yaxes(title="People", tickformat="~s")
        fig.update_xaxes(title="")
        return safe_fig(fig)

    @output
    @render_widget
    def host_map():
        d = state.selected_stock()
        if d.empty:
            return empty_fig("No host geography for this selection", 430)
        d = d[(d["host_map_eligible_flag"] == True) & d["host_iso3"].notna()]
        m = d.groupby(["host_country_std", "host_iso3"], as_index=False).agg(value_observed=("value_observed", "sum"))
        m = m[m["value_observed"].fillna(0) > 0]
        if m.empty:
            return empty_fig("No map-eligible host countries", 430)
        fig = px.choropleth(m, locations="host_iso3", color="value_observed", hover_name="host_country_std", color_continuous_scale="Blues")
        fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth", bgcolor="rgba(0,0,0,0)")
        fig.update_layout(height=430, margin={"l": 0, "r": 0, "t": 0, "b": 0}, coloraxis_colorbar={"title": "People", "tickformat": "~s"})
        return safe_fig(fig)

    @output
    @render.ui
    def executive_insight():
        d = state.selected_stock()
        if d.empty:
            return ui.div(ui.h3("Key reading"), ui.p("No data under the current filters."))
        origin = d.groupby("origin_country_std", as_index=False).agg(value=("value_observed", "sum")).sort_values("value", ascending=False).head(1)
        host = d.groupby("host_country_std", as_index=False).agg(value=("value_observed", "sum")).sort_values("value", ascending=False).head(1)
        origin_name = origin.iloc[0]["origin_country_std"] if len(origin) else "-"
        host_name = host.iloc[0]["host_country_std"] if len(host) else "-"
        return ui.div(
            ui.div("Key reading", class_="insight-kicker"),
            ui.h3(f"{origin_name} is the leading origin and {host_name} is the leading host."),
            ui.p("The opening view combines scale, geography and ranking to frame the rest of the dashboard story."),
        )
