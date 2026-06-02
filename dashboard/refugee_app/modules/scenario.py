"""Scenario-based displacement estimator.

This module is intentionally framed as visual analytics, not causal forecasting.
It estimates future displacement magnitude using historical crisis analogues from
cleaned UNHCR population-stock data and then distributes the projected total
across likely host countries and demographic groups.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs, render, ui
from shinywidgets import render_widget

from refugee_app.constants import ACTIVE_FORCED_TYPES, BLUE, CRISIS_EVENTS, CRISIS_ORIGIN, GREEN, ORANGE, PURPLE, RED
from refugee_app.modules.hero import empty_fig, fmt_num
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, selected_types
from refugee_app.services.serializers import safe_fig

SCENARIO_SCOPE_TYPES = {
    "Cross-border displacement": ["Refugees", "Asylum-seekers", "Others of concern"],
    "Refugees only": ["Refugees"],
    "Active forced displacement incl. IDPs": ACTIVE_FORCED_TYPES,
}

SEVERITY_QUANTILE = {
    "Contained shock": 0.25,
    "Major conflict": 0.50,
    "Regional war": 0.75,
    "Extreme crisis": 0.90,
}

REGION_LOOKUP = {
    # Middle East / North Africa
    "Syrian Arab Republic": "Middle East", "Turkey": "Middle East", "Lebanon": "Middle East",
    "Jordan": "Middle East", "Iraq": "Middle East", "Iran": "Middle East", "Yemen": "Middle East",
    "Egypt": "North Africa", "Algeria": "North Africa", "Sudan": "East/North Africa",
    # Africa
    "South Sudan": "East Africa", "Uganda": "East Africa", "Kenya": "East Africa",
    "Ethiopia": "East Africa", "Somalia": "East Africa", "Eritrea": "East Africa",
    "Rwanda": "East Africa", "Burundi": "East Africa", "United Republic of Tanzania": "East Africa",
    "Democratic Republic of the Congo": "Central Africa", "Central African Republic": "Central Africa",
    "Chad": "Central Africa", "Cameroon": "Central Africa", "South Africa": "Southern Africa",
    "Zambia": "Southern Africa", "Zimbabwe": "Southern Africa",
    # Asia
    "Afghanistan": "South/Central Asia", "Pakistan": "South/Central Asia", "India": "South Asia",
    "Bangladesh": "South Asia", "Myanmar": "Southeast Asia", "Thailand": "Southeast Asia",
    "Malaysia": "Southeast Asia", "China": "East Asia", "Sri Lanka": "South Asia",
    # Europe / Americas
    "Germany": "Europe", "France": "Europe", "Italy": "Europe", "Greece": "Europe", "Sweden": "Europe",
    "United Kingdom": "Europe", "Spain": "Europe", "Austria": "Europe", "Belgium": "Europe",
    "Switzerland": "Europe", "Netherlands": "Europe", "Ukraine": "Europe", "Russia": "Europe/Asia",
    "United States": "North America", "Canada": "North America", "Colombia": "Latin America",
    "Venezuela": "Latin America", "Brazil": "Latin America", "Australia": "Oceania",
}


def _scenario_types(label: str) -> list[str]:
    return SCENARIO_SCOPE_TYPES.get(label, SCENARIO_SCOPE_TYPES["Cross-border displacement"])


def _resolve_origin(input: Inputs, data: DataStore, state: DashboardState) -> str:
    selected = input.scenario_origin()
    if selected and selected != "Current dashboard focus":
        return str(selected)

    if input.origin() != "All":
        return str(input.origin())

    crisis_origin = CRISIS_ORIGIN.get(input.crisis())
    if crisis_origin:
        return crisis_origin

    d = state.selected_stock()
    if not d.empty:
        top = (
            d.groupby("origin_country_std", as_index=False)
            .agg(value_observed=("value_observed", "sum"))
            .sort_values("value_observed", ascending=False)
        )
        if len(top):
            return str(top.iloc[0]["origin_country_std"])

    return "Syrian Arab Republic"


def _origin_series(ts: pd.DataFrame, origin: str, types: Iterable[str]) -> pd.DataFrame:
    d = ts[ts["population_type_std"].isin(list(types))].copy()
    d = d[d["origin_country_std"].eq(origin)]
    out = (
        d.groupby("year", as_index=False)
        .agg(value_observed=("value_observed", "sum"))
        .sort_values("year")
    )
    out = out[out["value_observed"].fillna(0) > 0]
    return out


def _base_value(series: pd.DataFrame, year: int) -> tuple[int, float]:
    if series.empty:
        return year, 0.0
    before = series[series["year"].le(year)]
    if before.empty:
        row = series.iloc[0]
    else:
        row = before.iloc[-1]
    return int(row["year"]), float(row["value_observed"])


def _crisis_start_year(crisis: str) -> int | None:
    events = CRISIS_EVENTS.get(crisis, [])
    if not events:
        return None
    return int(events[0][0])


def _historical_multiplier_table(ts: pd.DataFrame, types: list[str], horizon: int) -> pd.DataFrame:
    rows: list[dict] = []
    for crisis, origin in CRISIS_ORIGIN.items():
        if not origin:
            continue
        start_year = _crisis_start_year(crisis)
        if start_year is None:
            continue
        series = _origin_series(ts, origin, types)
        if series.empty:
            continue
        base_year, base = _base_value(series, start_year)
        if base <= 0:
            continue
        for h in range(1, horizon + 1):
            future = series[series["year"].eq(base_year + h)]
            if future.empty:
                continue
            value = float(future.iloc[0]["value_observed"])
            if value > 0:
                rows.append({"crisis": crisis, "origin": origin, "horizon": h, "multiplier": max(value / base, 0.05)})
    return pd.DataFrame(rows)


def _projection(ts: pd.DataFrame, origin: str, types: list[str], base_year: int, horizon: int, severity: str) -> pd.DataFrame:
    series = _origin_series(ts, origin, types)
    actual_year, base = _base_value(series, base_year)
    if base <= 0:
        base = 1.0

    analogues = _historical_multiplier_table(ts, types, horizon)
    q = SEVERITY_QUANTILE.get(severity, 0.50)

    rows: list[dict] = []
    rows.append({"year": actual_year, "value_observed": base, "series": "Current baseline", "lower": base, "upper": base})

    for h in range(1, horizon + 1):
        if not analogues.empty and h in set(analogues["horizon"]):
            subset = analogues[analogues["horizon"].eq(h)]["multiplier"].dropna()
            main = float(subset.quantile(q)) if len(subset) else (1.08 ** h)
            low = float(subset.quantile(0.25)) if len(subset) else (1.02 ** h)
            high = float(subset.quantile(0.90)) if len(subset) else (1.18 ** h)
        else:
            # Fallback to recent own trend when analogue horizon is unavailable.
            recent = series.tail(4).copy()
            if len(recent) >= 2:
                first = max(float(recent.iloc[0]["value_observed"]), 1.0)
                last = max(float(recent.iloc[-1]["value_observed"]), 1.0)
                years = max(int(recent.iloc[-1]["year"] - recent.iloc[0]["year"]), 1)
                cagr = max(min((last / first) ** (1 / years) - 1, 0.85), -0.35)
            else:
                cagr = 0.08
            severity_boost = {"Contained shock": 0.6, "Major conflict": 1.0, "Regional war": 1.5, "Extreme crisis": 2.1}.get(severity, 1.0)
            main = max((1 + cagr * severity_boost) ** h, 0.2)
            low = max((1 + cagr * 0.5) ** h, 0.1)
            high = max((1 + cagr * 2.3) ** h, 0.2)
        rows.append(
            {
                "year": actual_year + h,
                "value_observed": base * main,
                "series": f"{severity} scenario",
                "lower": base * min(low, high),
                "upper": base * max(low, high),
            }
        )
    return pd.DataFrame(rows)


def _host_allocation(ts: pd.DataFrame, origin: str, types: list[str], year: int, total_projected: float, top_n: int) -> pd.DataFrame:
    d = ts[ts["population_type_std"].isin(types)]
    d = d[d["origin_country_std"].eq(origin)]
    before = d[d["year"].le(year)]
    if before.empty:
        before = d
    if before.empty:
        return pd.DataFrame()
    latest_year = int(before["year"].max())
    latest = before[before["year"].eq(latest_year)]
    out = (
        latest.groupby("host_country_std", as_index=False)
        .agg(value_observed=("value_observed", "sum"))
        .sort_values("value_observed", ascending=False)
        .head(top_n)
    )
    total = out["value_observed"].sum()
    if total <= 0:
        return pd.DataFrame()
    out["projected_people"] = out["value_observed"] / total * total_projected
    out["region"] = out["host_country_std"].map(REGION_LOOKUP).fillna("Other / mixed")
    return out.sort_values("projected_people", ascending=True)


def _demo_split(demo: pd.DataFrame, total_projected: float) -> pd.DataFrame:
    if demo.empty or total_projected <= 0:
        return pd.DataFrame()
    d = demo.copy()
    d = d.groupby(["age_group"], as_index=False).agg(value_observed=("value_observed", "sum"))
    d = d[d["value_observed"].fillna(0) > 0]
    if d.empty:
        return pd.DataFrame()
    d["share"] = d["value_observed"] / d["value_observed"].sum()
    d["projected_people"] = d["share"] * total_projected
    return d


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def scenario_projection_plot():
        origin = _resolve_origin(input, data, state)
        types = _scenario_types(input.scenario_scope())
        horizon = int(input.scenario_horizon())
        base_year = int(input.year())
        severity = input.scenario_severity()
        proj = _projection(data.time_series, origin, types, base_year, horizon, severity)
        if proj.empty:
            return empty_fig("No scenario data", 500)
        fig = go.Figure()
        hist = _origin_series(data.time_series, origin, types)
        if not hist.empty:
            hist = hist[hist["year"].between(max(hist["year"].min(), base_year - 12), base_year)]
            fig.add_trace(go.Scatter(x=hist["year"], y=hist["value_observed"], mode="lines+markers", name="Observed history", line={"color": BLUE, "width": 3}))
        fig.add_trace(go.Scatter(x=proj["year"], y=proj["upper"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=proj["year"], y=proj["lower"], mode="lines", line={"width": 0}, fill="tonexty", fillcolor="rgba(223,122,38,.18)", name="Scenario range", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=proj["year"], y=proj["value_observed"], mode="lines+markers", name=severity, line={"color": ORANGE, "width": 4, "dash": "dash"}))
        fig.update_layout(height=500, margin={"l": 56, "r": 24, "t": 22, "b": 50}, legend_title_text="")
        fig.update_yaxes(title="People", tickformat="~s")
        fig.update_xaxes(title="Year")
        return safe_fig(fig)

    @output
    @render_widget
    def scenario_host_plot():
        origin = _resolve_origin(input, data, state)
        types = _scenario_types(input.scenario_scope())
        proj = _projection(data.time_series, origin, types, int(input.year()), int(input.scenario_horizon()), input.scenario_severity())
        final_total = float(proj.iloc[-1]["value_observed"]) if len(proj) else 0.0
        out = _host_allocation(data.time_series, origin, types, int(input.year()), final_total, min(int(input.top_n()), 12))
        if out.empty:
            return empty_fig("No historical host split for this origin", 430)
        fig = px.bar(out, x="projected_people", y="host_country_std", color="region", orientation="h", color_discrete_sequence=[GREEN, BLUE, ORANGE, PURPLE, RED])
        fig.update_layout(height=430, margin={"l": 150, "r": 26, "t": 18, "b": 48}, legend_title_text="Region")
        fig.update_xaxes(title="Projected people", tickformat="~s")
        fig.update_yaxes(title="")
        return safe_fig(fig)

    @output
    @render_widget
    def scenario_demographic_plot():
        origin = _resolve_origin(input, data, state)
        types = _scenario_types(input.scenario_scope())
        proj = _projection(data.time_series, origin, types, int(input.year()), int(input.scenario_horizon()), input.scenario_severity())
        total = float(proj.iloc[-1]["value_observed"]) if len(proj) else 0.0
        out = _demo_split(data.demographics_age, total)
        if out.empty:
            return empty_fig("Demographic split unavailable", 430)
        fig = px.pie(out, names="age_group", values="projected_people", hole=0.48, color_discrete_sequence=[BLUE, PURPLE, ORANGE, GREEN, RED])
        fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br><b>%{value:,.0f}</b> people<extra></extra>")
        fig.update_layout(height=430, margin={"l": 20, "r": 20, "t": 18, "b": 20}, showlegend=False)
        return safe_fig(fig)

    @output
    @render.ui
    def scenario_summary():
        origin = _resolve_origin(input, data, state)
        types = _scenario_types(input.scenario_scope())
        horizon = int(input.scenario_horizon())
        proj = _projection(data.time_series, origin, types, int(input.year()), horizon, input.scenario_severity())
        if proj.empty:
            return ui.div(ui.h3("Scenario reading"), ui.p("No projection could be calculated under the current settings."))
        baseline = float(proj.iloc[0]["value_observed"])
        final = float(proj.iloc[-1]["value_observed"])
        low = float(proj.iloc[-1]["lower"])
        high = float(proj.iloc[-1]["upper"])
        change = final - baseline
        return ui.div(
            ui.div("Scenario reading", class_="explain-kicker"),
            ui.h3(f"{origin}: {fmt_num(final)} people after {horizon} years"),
            ui.p(f"Under the selected {input.scenario_severity().lower()} setting, the model estimates a range of {fmt_num(low)} to {fmt_num(high)} people by the end of the scenario horizon."),
            ui.p(f"Change from the baseline: {fmt_num(change)}. This is an analogue-based estimator, not a causal forecast."),
        )

    @output
    @render.ui
    def scenario_method_note():
        return ui.div(
            ui.div("Model note", class_="explain-kicker"),
            ui.h3("Historical analogue, not deterministic prediction"),
            ui.p("The estimator compares crisis-origin trajectories in the cleaned UNHCR stock data and applies severity-specific historical multipliers to the selected origin."),
            ui.tags.ul(
                ui.tags.li("Country output: projected displaced population for the selected origin."),
                ui.tags.li("Regional output: host-country distribution grouped by approximate region."),
                ui.tags.li("Demographic output: projected age-group composition using the latest demographic shares."),
            ),
        )
