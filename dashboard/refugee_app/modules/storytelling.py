"""Crisis storytelling outputs."""
from __future__ import annotations

import plotly.express as px
from shiny import Inputs, Outputs, render, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, CRISIS_EVENTS, CRISIS_ORIGIN, GREEN, ORANGE
from refugee_app.modules.hero import empty_fig
from refugee_app.modules.map_flows import make_route_map_figure
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, aggregate_dimension
from refugee_app.services.serializers import safe_fig


def crisis_origin(crisis: str) -> str:
    return CRISIS_ORIGIN.get(crisis) or "Syrian Arab Republic"


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render.ui
    def crisis_timeline():
        crisis = state.crisis() if state.crisis() != "All Crises" else "Syrian Civil War"

        rows = [
            ui.h3(crisis),
            ui.p(f"Origin focus: {crisis_origin(crisis)}"),
        ]

        for year, event in CRISIS_EVENTS.get(crisis, []):
            rows.append(
                ui.div(
                    ui.span(str(year), class_="timeline-year"),
                    ui.span(event),
                    class_="timeline-row",
                )
            )

        return ui.div(*rows)

    @output
    @render_widget
    def crisis_trend():
        origin = crisis_origin(state.crisis())
        d = data.time_series.copy()
        d = d[d["origin_country_std"].eq(origin) & d["population_type_std"].isin(state.types())]

        if d.empty:
            return empty_fig("No crisis trend data", 430)

        out = (
            d.groupby(["year", "population_type_std"], as_index=False)
            .agg(value_observed=("value_observed", "sum"))
        )

        fig = px.line(
            out,
            x="year",
            y="value_observed",
            color="population_type_std",
            markers=True,
            color_discrete_sequence=[BLUE, ORANGE, GREEN],
        )

        fig.update_layout(
            height=430,
            margin={"l": 50, "r": 20, "t": 18, "b": 44},
            legend_title_text="",
        )
        fig.update_yaxes(tickformat="~s", title="People")
        fig.update_xaxes(title="")

        return safe_fig(fig)

    @output
    @render_widget
    def crisis_hosts():
        origin = crisis_origin(state.crisis())
        d = state.selected_stock()
        d = d[d["origin_country_std"].eq(origin)]

        out = aggregate_dimension(d, "host", state.top_n())

        if out.empty:
            return empty_fig("No crisis host ranking", 430)

        out = out.sort_values("value_observed", ascending=True)

        fig = px.bar(
            out,
            x="value_observed",
            y="host_country_std",
            orientation="h",
            color_discrete_sequence=[GREEN],
        )
        fig.update_layout(height=430, margin={"l": 150, "r": 24, "t": 14, "b": 44})
        fig.update_xaxes(title="People", tickformat="~s")
        fig.update_yaxes(title="")

        return safe_fig(fig)

    @output
    @render_widget
    def crisis_routes():
        origin = crisis_origin(state.crisis())
        d = state.selected_stock()
        d = d[d["origin_country_std"].eq(origin)]

        if d.empty:
            return empty_fig("No crisis route data", 430)

        routes = (
            d.groupby(["origin_country_std", "host_country_std"], as_index=False)
            .agg(value_observed=("value_observed", "sum"))
            .sort_values("value_observed", ascending=False)
            .head(state.top_n())
        )

        return make_route_map_figure(
            routes,
            height=430,
            max_routes=state.top_n(),
            route_color=BLUE,
            moving=True,
        )
