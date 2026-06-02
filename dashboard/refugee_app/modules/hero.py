"""Executive overview outputs: KPI cards, trend, map and insight text."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs, render, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, CENTROIDS, GREEN, MUTED, ORANGE, PURPLE
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
            return empty_fig("No host geography for this selection", 470)

        d = d[(d["host_map_eligible_flag"] == True) & d["host_iso3"].notna()].copy()
        m = (
            d.groupby(["host_country_std", "host_iso3"], as_index=False)
            .agg(value_observed=("value_observed", "sum"))
        )
        m = m[m["value_observed"].fillna(0) > 0]

        if m.empty:
            return empty_fig("No map-eligible host countries", 470)

        points = []
        for country in m["host_country_std"].dropna().astype(str):
            if country in CENTROIDS:
                points.append(CENTROIDS[country])

        def focus_ranges(points):
            if len(points) < 2:
                return None, None

            lats = [float(p[0]) for p in points]
            lons = [float(p[1]) for p in points]

            lat_min, lat_max = min(lats), max(lats)
            lon_min, lon_max = min(lons), max(lons)

            lat_span = max(lat_max - lat_min, 10.0)
            lon_span = max(lon_max - lon_min, 16.0)

            if lon_span > 155 or lat_span > 115:
                return None, None

            lat_pad = max(5.0, lat_span * 0.32)
            lon_pad = max(7.0, lon_span * 0.32)

            lat_range = [max(-58, lat_min - lat_pad), min(78, lat_max + lat_pad)]
            lon_range = [max(-170, lon_min - lon_pad), min(170, lon_max + lon_pad)]
            return lat_range, lon_range

        fig = px.choropleth(
            m,
            locations="host_iso3",
            color="value_observed",
            hover_name="host_country_std",
            color_continuous_scale="Blues",
            range_color=(0, float(m["value_observed"].max())),
        )

        fig.update_traces(
            marker_line_width=0.55,
            marker_line_color="rgba(17,24,39,.36)",
        )

        lat_range, lon_range = focus_ranges(points)

        fig.update_geos(
            projection_type="natural earth",
            showframe=False,
            showcoastlines=False,
            showland=True,
            landcolor="rgb(247,243,236)",
            showcountries=True,
            countrycolor="rgba(17,24,39,.28)",
            showocean=True,
            oceancolor="rgb(252,249,243)",
            bgcolor="rgba(0,0,0,0)",
            domain={"x": [0.00, 0.88], "y": [0.00, 1.00]},
        )

        if lat_range is not None and lon_range is not None:
            fig.update_geos(lataxis_range=lat_range, lonaxis_range=lon_range)
        else:
            fig.update_geos(scope="world")

        fig.update_layout(
            height=470,
            autosize=True,
            margin={"l": 0, "r": 4, "t": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar={
                "title": {"text": "People", "side": "top"},
                "tickformat": "~s",
                "thickness": 9,
                "len": 0.46,
                "x": 0.91,
                "xanchor": "left",
                "y": 0.50,
                "yanchor": "middle",
                "outlinewidth": 0,
            },
            uirevision="host-map-executive",
        )

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
