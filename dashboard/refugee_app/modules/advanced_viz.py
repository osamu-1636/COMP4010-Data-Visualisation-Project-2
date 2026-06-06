"""Advanced visual analytics + ML baseline.

This module adds:
1. Host concentration treemap.
2. Observed distance-band analytics.
3. A supervised ML baseline using RandomForestRegressor.

ML task:
Predict log(1 + corridor refugee count) for origin-host-year corridors.

Features:
- year
- distance_km
- previous_year_flow
- origin_total_previous_year
- host_total_previous_year
- distance_band one-hot indicators

Important interpretation:
This is a predictive baseline, not a causal war forecasting model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
from shiny import Inputs, Outputs, render, reactive, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, ORANGE, PURPLE, CENTROIDS
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, aggregate_dimension
from refugee_app.services.serializers import safe_fig

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score

    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


DISTANCE_ORDER = [
    "Near (<1,000 km)",
    "Regional (1,000–3,000 km)",
    "Far (>3,000 km)",
]

NUMERIC_FEATURES = [
    "year",
    "distance_km",
    "prev_flow_log",
    "origin_prev_total_log",
    "host_prev_total_log",
]

BAND_FEATURES = [f"band__{x}" for x in DISTANCE_ORDER]
FEATURE_COLUMNS = NUMERIC_FEATURES + BAND_FEATURES


@dataclass
class ModelBundle:
    ok: bool
    reason: str
    model: object | None
    train_rows: int = 0
    test_rows: int = 0
    mae_log: float | None = None
    r2: float | None = None
    feature_importance: pd.DataFrame | None = None


def _compact(x: float) -> str:
    try:
        x = float(x)
    except Exception:
        return "0"

    if abs(x) >= 1_000_000:
        return f"{x / 1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"{x / 1_000:.0f}K"
    return f"{x:.0f}"


def _fmt_metric(x: float | None, digits: int = 3) -> str:
    if x is None:
        return "n/a"
    try:
        x = float(x)
    except Exception:
        return "n/a"
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{digits}f}"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def _band(distance_km: float) -> str:
    if distance_km < 1000:
        return "Near (<1,000 km)"
    if distance_km < 3000:
        return "Regional (1,000–3,000 km)"
    return "Far (>3,000 km)"


def _corridor_year_table(d: pd.DataFrame) -> pd.DataFrame:
    """Create one row per year-origin-host corridor with engineered features."""
    needed = {
        "year",
        "origin_country_std",
        "host_country_std",
        "value_observed",
    }

    if d.empty or not needed.issubset(d.columns):
        return pd.DataFrame()

    base = (
        d.dropna(subset=["year", "origin_country_std", "host_country_std"])
        .groupby(["year", "origin_country_std", "host_country_std"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
    )

    base = base[base["value_observed"].fillna(0) > 0].copy()

    rows: list[dict] = []

    for _, r in base.iterrows():
        origin = str(r["origin_country_std"])
        host = str(r["host_country_std"])

        if origin not in CENTROIDS or host not in CENTROIDS:
            continue

        origin_lat, origin_lon = CENTROIDS[origin]
        host_lat, host_lon = CENTROIDS[host]

        distance_km = _haversine_km(origin_lat, origin_lon, host_lat, host_lon)

        rows.append(
            {
                "year": int(r["year"]),
                "origin": origin,
                "host": host,
                "distance_km": float(distance_km),
                "distance_band": _band(distance_km),
                "value_observed": float(r["value_observed"]),
            }
        )

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)

    # Pair-level lag: previous year flow for the same origin-host corridor.
    prev_pair = out[["year", "origin", "host", "value_observed"]].copy()
    prev_pair["year"] = prev_pair["year"] + 1
    prev_pair = prev_pair.rename(columns={"value_observed": "previous_year_flow"})
    out = out.merge(prev_pair, on=["year", "origin", "host"], how="left")

    # Origin previous-year total.
    origin_prev = (
        out.groupby(["year", "origin"], as_index=False)
        .agg(origin_total_previous_year=("value_observed", "sum"))
    )
    origin_prev["year"] = origin_prev["year"] + 1
    out = out.merge(origin_prev, on=["year", "origin"], how="left")

    # Host previous-year total.
    host_prev = (
        out.groupby(["year", "host"], as_index=False)
        .agg(host_total_previous_year=("value_observed", "sum"))
    )
    host_prev["year"] = host_prev["year"] + 1
    out = out.merge(host_prev, on=["year", "host"], how="left")

    for col in ["previous_year_flow", "origin_total_previous_year", "host_total_previous_year"]:
        out[col] = out[col].fillna(0)

    out["prev_flow_log"] = np.log1p(out["previous_year_flow"])
    out["origin_prev_total_log"] = np.log1p(out["origin_total_previous_year"])
    out["host_prev_total_log"] = np.log1p(out["host_total_previous_year"])
    out["target_log_flow"] = np.log1p(out["value_observed"])

    out["distance_band"] = pd.Categorical(
        out["distance_band"],
        categories=DISTANCE_ORDER,
        ordered=True,
    )

    return out.sort_values(["year", "origin", "host"])


def _feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    x = df[NUMERIC_FEATURES].copy()

    for band in DISTANCE_ORDER:
        x[f"band__{band}"] = (df["distance_band"].astype(str) == band).astype(float)

    return x[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _distance_table(d: pd.DataFrame) -> pd.DataFrame:
    """Actual near/regional/far shares by year."""
    table = _corridor_year_table(d)

    if table.empty:
        return pd.DataFrame()

    out = (
        table.groupby(["year", "distance_band"], as_index=False, observed=False)
        .agg(value_observed=("value_observed", "sum"))
    )

    totals = out.groupby("year", as_index=False).agg(total=("value_observed", "sum"))
    out = out.merge(totals, on="year", how="left")
    out["share"] = np.where(out["total"] > 0, out["value_observed"] / out["total"], np.nan)
    out["distance_band"] = pd.Categorical(
        out["distance_band"],
        categories=DISTANCE_ORDER,
        ordered=True,
    )

    return out.sort_values(["year", "distance_band"])


def _train_model(d: pd.DataFrame) -> ModelBundle:
    if not SKLEARN_AVAILABLE:
        return ModelBundle(False, "scikit-learn is not installed.", None)

    table = _corridor_year_table(d)

    if table.empty or len(table) < 80:
        return ModelBundle(False, "Not enough corridor-year rows for a stable model.", None)

    years = sorted(table["year"].dropna().astype(int).unique().tolist())

    if len(years) < 5:
        return ModelBundle(False, "Not enough years for a time-based train/test split.", None)

    test_years = years[-3:] if len(years) >= 8 else years[-2:]

    train = table[~table["year"].isin(test_years)].copy()
    test = table[table["year"].isin(test_years)].copy()

    if len(train) < 50 or len(test) < 10:
        return ModelBundle(False, "Train/test split is too small for reliable validation.", None)

    x_train = _feature_matrix(train)
    y_train = train["target_log_flow"].to_numpy()

    x_test = _feature_matrix(test)
    y_test = test["target_log_flow"].to_numpy()

    model = RandomForestRegressor(
        n_estimators=120,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)

    pred = model.predict(x_test)

    mae = float(mean_absolute_error(y_test, pred))

    try:
        r2 = float(r2_score(y_test, pred))
    except Exception:
        r2 = float("nan")

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": getattr(model, "feature_importances_", np.zeros(len(FEATURE_COLUMNS))),
        }
    ).sort_values("importance", ascending=False)

    return ModelBundle(
        ok=True,
        reason="OK",
        model=model,
        train_rows=len(train),
        test_rows=len(test),
        mae_log=mae,
        r2=r2,
        feature_importance=importance,
    )


def _actual_vs_predicted_distance_mix(
    bundle: ModelBundle,
    selected: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    if not bundle.ok or bundle.model is None:
        return pd.DataFrame()

    table = _corridor_year_table(selected)

    if table.empty:
        return pd.DataFrame()

    target_year = int(year)
    pred_base = table[table["year"].eq(target_year)].copy()

    if pred_base.empty:
        target_year = int(table["year"].max())
        pred_base = table[table["year"].eq(target_year)].copy()

    if pred_base.empty:
        return pd.DataFrame()

    x = _feature_matrix(pred_base)
    pred_log = bundle.model.predict(x)

    pred_base["predicted_value"] = np.expm1(pred_log).clip(min=0)
    pred_base["actual_value"] = pred_base["value_observed"].clip(lower=0)

    rows = []

    for series, value_col in [
        ("Actual observed", "actual_value"),
        ("ML predicted", "predicted_value"),
    ]:
        agg = (
            pred_base.groupby("distance_band", as_index=False, observed=False)
            .agg(value=(value_col, "sum"))
        )
        total = float(agg["value"].sum())
        agg["share"] = np.where(total > 0, agg["value"] / total, 0)
        agg["series"] = series
        agg["year"] = target_year
        rows.append(agg)

    out = pd.concat(rows, ignore_index=True)
    out["distance_band"] = pd.Categorical(
        out["distance_band"],
        categories=DISTANCE_ORDER,
        ordered=True,
    )

    return out.sort_values(["distance_band", "series"])


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @reactive.calc
    def model_bundle():
        # Train on all years for the selected population scope.
        d = data.time_series.copy()

        if "population_type_std" in d.columns:
            d = d[d["population_type_std"].isin(state.types())]

        return _train_model(d)

    @output
    @render_widget
    def host_treemap():
        d = state.selected_stock()
        out = aggregate_dimension(d, "host", min(state.top_n(), 20))

        if out.empty:
            return empty_fig("No host concentration data for this selection", 520)

        out = out.copy()
        out["Total"] = "Selected host stock"

        fig = px.treemap(
            out,
            path=["Total", "host_country_std"],
            values="value_observed",
            color="value_observed",
            color_continuous_scale="YlGnBu",
            hover_data={"value_observed": ":,.0f", "share": ":.1%"},
        )

        fig.update_traces(
            textinfo="label+value",
            texttemplate="<b>%{label}</b><br>%{value:,.0f}",
            marker_line_color="#fffdf8",
            marker_line_width=2,
        )

        fig.update_layout(
            height=520,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            coloraxis_showscale=False,
        )

        return safe_fig(fig)

    @output
    @render_widget
    def distance_stack_plot():
        d = state.stock_all_years_same_filters()
        out = _distance_table(d)

        if out.empty:
            return empty_fig("No distance-band data for this selection", 520)

        years = sorted(out["year"].dropna().astype(int).unique().tolist())

        if len(years) > 12:
            out = out[out["year"].isin(set(years[-12:]))]

        fig = px.area(
            out,
            x="year",
            y="share",
            color="distance_band",
            category_orders={"distance_band": DISTANCE_ORDER},
            color_discrete_map={
                "Near (<1,000 km)": ORANGE,
                "Regional (1,000–3,000 km)": BLUE,
                "Far (>3,000 km)": PURPLE,
            },
            hover_data={
                "share": ":.1%",
                "value_observed": ":,.0f",
                "total": ":,.0f",
            },
        )

        fig.update_layout(
            height=520,
            margin={"l": 52, "r": 24, "t": 14, "b": 54},
            legend_title_text="Distance band",
        )
        fig.update_yaxes(title="Share of selected corridor stock", tickformat=".0%")
        fig.update_xaxes(title="Year", dtick=1)

        return safe_fig(fig)

    @output
    @render_widget
    def ml_distance_prediction_plot():
        bundle = model_bundle()

        if not bundle.ok:
            return empty_fig(f"ML model unavailable: {bundle.reason}", 520)

        selected = state.stock_all_years_same_filters()
        out = _actual_vs_predicted_distance_mix(bundle, selected, state.year())

        if out.empty:
            return empty_fig("No selected-year rows available for ML prediction", 520)

        fig = px.bar(
            out,
            x="distance_band",
            y="share",
            color="series",
            barmode="group",
            text="share",
            category_orders={"distance_band": DISTANCE_ORDER},
            color_discrete_map={
                "Actual observed": "#64748b",
                "ML predicted": ORANGE,
            },
            hover_data={
                "share": ":.1%",
                "value": ":,.0f",
                "year": True,
            },
        )

        fig.update_traces(texttemplate="%{text:.0%}", textposition="outside")
        fig.update_layout(
            height=520,
            margin={"l": 52, "r": 24, "t": 14, "b": 70},
            legend_title_text="",
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        fig.update_yaxes(
            title="Share of selected-year corridor stock",
            tickformat=".0%",
            range=[0, 1],
        )
        fig.update_xaxes(title="Distance band")

        return safe_fig(fig)

    @output
    @render.ui
    def ml_model_cards():
        bundle = model_bundle()

        if not bundle.ok:
            return ui.div(
                ui.div("ML baseline", class_="explain-kicker"),
                ui.h3("Model not available"),
                ui.p(bundle.reason),
                class_="ml-card-wrap",
            )

        importance = (
            bundle.feature_importance.copy()
            if bundle.feature_importance is not None
            else pd.DataFrame()
        )

        top_features = importance.head(5)["feature"].tolist() if not importance.empty else []

        return ui.div(
            ui.div("ML baseline", class_="explain-kicker"),
            ui.h3("How the model learns corridor pressure"),
            ui.p(
                "A RandomForestRegressor predicts log(1 + refugee count) for each "
                "origin-host-year corridor. Predicted corridor counts are aggregated "
                "into near, regional and far distance bands."
            ),
            ui.div(
                ui.div(
                    ui.div("Train rows", class_="ml-metric-label"),
                    ui.strong(f"{bundle.train_rows:,}"),
                    class_="ml-metric",
                ),
                ui.div(
                    ui.div("Test rows", class_="ml-metric-label"),
                    ui.strong(f"{bundle.test_rows:,}"),
                    class_="ml-metric",
                ),
                ui.div(
                    ui.div("MAE on log target", class_="ml-metric-label"),
                    ui.strong(_fmt_metric(bundle.mae_log, 3)),
                    class_="ml-metric",
                ),
                ui.div(
                    ui.div("R²", class_="ml-metric-label"),
                    ui.strong(_fmt_metric(bundle.r2, 3)),
                    class_="ml-metric",
                ),
                class_="ml-metric-grid",
            ),
            ui.div(
                ui.strong("Top features: "),
                ", ".join(top_features) if top_features else "n/a",
                class_="ml-feature-note",
            ),
            ui.p(
                "Interpretation: predictive baseline, not causal war forecasting.",
                class_="ml-caution",
            ),
            class_="ml-card-wrap",
        )
