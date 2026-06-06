"""Analytical appendix outputs."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from shiny import Inputs, Outputs, render
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState
from refugee_app.services.serializers import safe_fig


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def monthly_plot():
        d = data.monthly_apps.copy()
        if d.empty:
            return empty_fig("Monthly data unavailable", 380)
        out = d.groupby(["month_num", "month"], as_index=False).agg(applications_observed=("applications_observed", "mean")).sort_values("month_num")
        fig = px.bar(out, x="month", y="applications_observed", color_discrete_sequence=[BLUE])
        fig.update_layout(height=380, margin={"l": 48, "r": 20, "t": 16, "b": 50})
        fig.update_yaxes(title="Mean applications", tickformat="~s")
        fig.update_xaxes(title="")
        return safe_fig(fig)

    @output
    @render_widget
    def demo_plot():
        d = data.demographics_age.copy()
        if d.empty:
            return empty_fig("Demographic data unavailable", 380)
        fig = px.bar(d, x="age_group", y="value_observed", color="sex", barmode="group", color_discrete_sequence=[PURPLE, BLUE])
        fig.update_layout(height=380, margin={"l": 48, "r": 20, "t": 16, "b": 48}, legend_title_text="")
        fig.update_yaxes(title="People", tickformat="~s")
        fig.update_xaxes(title="Age group")
        return safe_fig(fig)

    @output
    @render_widget
    def resettlement_plot():
        d = data.resettlement_year.copy()
        if d.empty:
            return empty_fig("Resettlement data unavailable", 380)
        fig = px.area(d, x="year", y="resettlement_observed", color_discrete_sequence=[GREEN])
        fig.update_layout(height=380, margin={"l": 48, "r": 20, "t": 16, "b": 48})
        fig.update_yaxes(title="Resettled people", tickformat="~s")
        fig.update_xaxes(title="")
        return safe_fig(fig)

    @output
    @render_widget
    def forecast_plot():
        d = data.forecast.copy()
        if d.empty:
            return empty_fig("Forecast data unavailable", 380)
        fig = px.line(d, x="year", y="value_observed", color="series", markers=True, color_discrete_sequence=[BLUE, ORANGE])
        fig.update_layout(height=380, margin={"l": 48, "r": 20, "t": 16, "b": 48}, legend_title_text="")
        fig.update_yaxes(title="People", tickformat="~s")
        fig.update_xaxes(title="")
        return safe_fig(fig)
