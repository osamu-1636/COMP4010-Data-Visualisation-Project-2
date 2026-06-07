"""Reactive filter state and data-filtering helpers.

Hybrid final version.

Design choice:
- The dashboard has an Apply button, so expensive Plotly charts rerender only after
  the presenter commits the filter state.
- Modules read from DashboardState instead of directly reading input.*.
- This keeps the GitHub base architecture clean while supporting the final story UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from shiny import Inputs, Session, reactive, ui

from refugee_app.constants import ACTIVE_FORCED_TYPES, CROSS_BORDER_TYPES, CRISIS_ORIGIN
from refugee_app.services.data_loader import DataStore


def selected_types(refugee_type: str) -> list[str]:
    return {
        "All cross-border": CROSS_BORDER_TYPES,
        "Refugees": ["Refugees"],
        "Asylum-seekers": ["Asylum-seekers"],
        "Others of concern": ["Others of concern"],
        "Active forced incl. IDPs": ACTIVE_FORCED_TYPES,
    }.get(refugee_type, CROSS_BORDER_TYPES)


def apply_filters(
    df: pd.DataFrame,
    *,
    year: int | None,
    types: Sequence[str] | None,
    crisis: str,
    origin: str,
    host: str,
) -> pd.DataFrame:
    d = df.copy()

    if year is not None and "year" in d.columns:
        d = d[d["year"].eq(int(year))]

    if types is not None and "population_type_std" in d.columns:
        d = d[d["population_type_std"].isin(types)]

    crisis_origin = CRISIS_ORIGIN.get(crisis)

    if origin != "All" and "origin_country_std" in d.columns:
        d = d[d["origin_country_std"].eq(origin)]
    elif crisis_origin is not None and "origin_country_std" in d.columns:
        d = d[d["origin_country_std"].eq(crisis_origin)]

    if host != "All" and "host_country_std" in d.columns:
        d = d[d["host_country_std"].eq(host)]

    return d


def clean_country(d: pd.DataFrame, prefix: str, map_only: bool = False) -> pd.DataFrame:
    if d.empty:
        return d.copy()

    d = d.copy()
    d = d[d[f"{prefix}_iso3"].notna()]
    d = d[d[f"{prefix}_iso3"].ne("UNMAPPED")]
    d = d[~d[f"{prefix}_mapping_status"].isin(["special_entity", "missing", "unmapped"])]

    if map_only and f"{prefix}_map_eligible_flag" in d.columns:
        d = d[d[f"{prefix}_map_eligible_flag"] == True]

    return d


def aggregate_dimension(d: pd.DataFrame, prefix: str, top_n: int) -> pd.DataFrame:
    d = clean_country(d, prefix, map_only=False)

    if d.empty:
        return pd.DataFrame()

    out = (
        d.groupby([f"{prefix}_country_std", f"{prefix}_iso3"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
    )
    out = (
        out[out["value_observed"].fillna(0) > 0]
        .sort_values("value_observed", ascending=False)
        .head(int(top_n))
        .copy()
    )
    out["rank"] = np.arange(1, len(out) + 1)

    total = d["value_observed"].sum(skipna=True)
    out["share"] = np.where(total > 0, out["value_observed"] / total, np.nan)

    return out


def build_corridors(d: pd.DataFrame, top_n: int) -> pd.DataFrame:
    d = clean_country(clean_country(d, "origin", False), "host", False)

    if d.empty:
        return pd.DataFrame()

    out = (
        d.groupby(["origin_country_std", "host_country_std", "population_type_std"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
    )
    out = (
        out[out["value_observed"].fillna(0) > 0]
        .sort_values("value_observed", ascending=False)
        .head(int(top_n))
        .copy()
    )

    return out


@dataclass
class DashboardState:
    types: Callable[[], list[str]]
    year: Callable[[], int]
    top_n: Callable[[], int]
    crisis: Callable[[], str]
    selected_stock: Callable[[], pd.DataFrame]
    stock_all_years_same_filters: Callable[[], pd.DataFrame]
    kpis: Callable[[], dict]


def make_state(input: Inputs, session: Session, data: DataStore) -> DashboardState:
    """Build a stable app state from top-bar inputs.

    The initial state uses the latest available year and the default cross-border
    scope. When the Apply button is present, charts update only after Apply. If a
    legacy layout does not contain Apply, the state still initializes correctly.
    """
    applied = reactive.value(
        {
            "year": data.year_max,
            "crisis": "All Crises",
            "origin": "All",
            "host": "All",
            "refugee_type": "All cross-border",
            "top_n": 12,
        }
    )

    def current_inputs() -> dict:
        return {
            "year": int(input.year()),
            "crisis": input.crisis(),
            "origin": input.origin(),
            "host": input.host(),
            "refugee_type": input.refugee_type(),
            "top_n": int(input.top_n()),
        }

    @reactive.effect
    @reactive.event(input.apply_filters, ignore_none=True)
    def _apply_filters():
        applied.set(current_inputs())

    @reactive.effect
    @reactive.event(input.reset)
    def _reset():
        ui.update_slider("year", value=data.year_max)
        ui.update_select("crisis", selected="All Crises")
        ui.update_selectize("origin", selected="All")
        ui.update_selectize("host", selected="All")
        ui.update_select("refugee_type", selected="All cross-border")
        ui.update_slider("top_n", value=12)
        applied.set(
            {
                "year": data.year_max,
                "crisis": "All Crises",
                "origin": "All",
                "host": "All",
                "refugee_type": "All cross-border",
                "top_n": 12,
            }
        )

    @reactive.calc
    def year():
        return int(applied()["year"])

    @reactive.calc
    def top_n():
        return int(applied()["top_n"])

    @reactive.calc
    def crisis():
        return str(applied()["crisis"])

    @reactive.calc
    def types():
        return selected_types(applied()["refugee_type"])

    @reactive.calc
    def selected_stock():
        filters = applied()
        return apply_filters(
            data.time_series,
            year=year(),
            types=types(),
            crisis=crisis(),
            origin=filters["origin"],
            host=filters["host"],
        )

    @reactive.calc
    def stock_all_years_same_filters():
        filters = applied()
        return apply_filters(
            data.time_series,
            year=None,
            types=types(),
            crisis=crisis(),
            origin=filters["origin"],
            host=filters["host"],
        )

    @reactive.calc
    def kpis():
        d = selected_stock()
        filters = applied()
        active = apply_filters(
            data.time_series,
            year=year(),
            types=ACTIVE_FORCED_TYPES,
            crisis=crisis(),
            origin=filters["origin"],
            host=filters["host"],
        )
        total = float(d["value_observed"].sum(skipna=True)) if len(d) else 0.0
        ref = float(d[d["population_type_std"].eq("Refugees")]["value_observed"].sum(skipna=True)) if len(d) else 0.0
        asylum = float(d[d["population_type_std"].eq("Asylum-seekers")]["value_observed"].sum(skipna=True)) if len(d) else 0.0
        idp = float(active[active["population_type_std"].eq("IDPs")]["value_observed"].sum(skipna=True)) if len(active) else 0.0
        countries = int(pd.concat([d["origin_country_std"], d["host_country_std"]]).dropna().nunique()) if len(d) else 0
        return {"total": total, "refugees": ref, "asylum": asylum, "idps": idp, "countries": countries}

    return DashboardState(
        types=types,
        year=year,
        top_n=top_n,
        crisis=crisis,
        selected_stock=selected_stock,
        stock_all_years_same_filters=stock_all_years_same_filters,
        kpis=kpis,
    )
