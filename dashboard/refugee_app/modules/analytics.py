"""Analytical appendix outputs."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from shiny import Inputs, Outputs
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState
from refugee_app.services.serializers import safe_fig


def _read_chart_file(data: DataStore, names: list[str]) -> pd.DataFrame:
    for name in names:
        path = data.chart / name
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path)
            return pd.read_csv(path)
    return pd.DataFrame()


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def monthly_plot():
        d = data.monthly_apps.copy()
        if d.empty:
            return empty_fig("Monthly data unavailable", 430)

        needed = {"year", "month_num", "month", "applications_observed"}
        if not needed.issubset(d.columns):
            return empty_fig("Monthly data missing required columns", 430)

        out = (
            d.groupby(["year", "month_num", "month"], as_index=False)
            .agg(applications_observed=("applications_observed", "sum"))
            .sort_values(["year", "month_num"])
        )

        # Keep the heatmap readable on a slide while preserving the full monthly story.
        years = sorted(out["year"].dropna().astype(int).unique().tolist())
        if len(years) > 18:
            keep = set(years[-18:])
            out = out[out["year"].astype(int).isin(keep)]

        month_order = (
            out[["month_num", "month"]]
            .drop_duplicates()
            .sort_values("month_num")["month"]
            .tolist()
        )

        fig = px.density_heatmap(
            out,
            x="month",
            y="year",
            z="applications_observed",
            histfunc="sum",
            category_orders={"month": month_order},
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=430, margin={"l": 54, "r": 20, "t": 18, "b": 50}, coloraxis_colorbar={"title": "Applications", "tickformat": "~s"})
        fig.update_xaxes(title="Month")
        fig.update_yaxes(title="Year", autorange="reversed", dtick=1)
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

    @output
    @render_widget
    def animated_host_map_plot():
        """Animated host-country map inspired by the reference prototype.

        Prefer per-100k host-pressure data when denominators are available; fall
        back to absolute host stock otherwise. The chart is still rendered from
        precomputed EDA outputs, not from raw CSV or runtime API calls.
        """
        hp = data.host_pressure.copy()
        use_pressure = False
        if not hp.empty and "host_stock_per_100k_population" in hp.columns and hp["host_stock_per_100k_population"].notna().any():
            d = hp.copy()
            metric = "host_stock_per_100k_population"
            location_col = "iso3"
            hover_col = "country"
            title = "Host pressure per 100k population"
            use_pressure = True
        else:
            d = _read_chart_file(data, ["animated_host_map.parquet", "animated_host_map.csv", "animated_host_map_by_year.csv"])
            if d.empty:
                return empty_fig("Animated host map unavailable", 430)
            metric = "value_observed"
            location_col = "host_iso3"
            hover_col = "host_country_std"
            title = "Host stock over time"

        needed = {"year", location_col, metric}
        if not needed.issubset(d.columns):
            return empty_fig("Animated map data missing required columns", 430)

        d = d.dropna(subset=["year", location_col, metric]).copy()
        d = d[d[metric].fillna(0) > 0]
        if d.empty:
            return empty_fig("No positive values for animated map", 430)

        years = sorted(d["year"].dropna().astype(int).unique().tolist())
        if len(years) > 22:
            # Keep the animation responsive for live demo while preserving trend coverage.
            keep = set(years[:: max(1, len(years) // 18)] + [years[-1]])
            d = d[d["year"].astype(int).isin(keep)]

        fig = px.choropleth(
            d,
            locations=location_col,
            color=metric,
            hover_name=hover_col if hover_col in d.columns else None,
            animation_frame="year",
            animation_group=location_col,
            color_continuous_scale="Blues" if not use_pressure else "YlOrRd",
        )
        fig.update_traces(marker_line_width=0.35, marker_line_color="rgba(17,24,39,.28)")
        fig.update_geos(
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(247,243,236)",
            showcountries=True,
            countrycolor="rgba(17,24,39,.22)",
            bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(
            height=430,
            margin={"l": 0, "r": 0, "t": 20, "b": 0},
            title={"text": title, "x": 0.02, "font": {"size": 15}},
            coloraxis_colorbar={"title": "per 100k" if use_pressure else "People", "tickformat": "~s", "thickness": 9, "len": 0.50},
        )
        return safe_fig(fig)
