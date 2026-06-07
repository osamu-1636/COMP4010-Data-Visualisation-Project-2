"""ML Visualized module for corridor-flow prediction.

This module is designed for the final dashboard story:

Observed corridor distance pattern
→ engineered features
→ RandomForestRegressor
→ predicted corridor flow
→ predicted near/regional/far mix
→ top predicted host destinations
→ similarity explorer and feature importance

Interpretation:
This is a supervised predictive baseline, not causal war forecasting.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
from shiny import Inputs, Outputs, reactive, render, ui
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE, CENTROIDS
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState
from refugee_app.services.serializers import safe_fig

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

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


def _fmt(x: float | None, digits: int = 3) -> str:
    if x is None:
        return "n/a"
    try:
        x = float(x)
    except Exception:
        return "n/a"
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{digits}f}"


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


def _distance_band(distance_km: float) -> str:
    if distance_km < 1000:
        return "Near (<1,000 km)"
    if distance_km < 3000:
        return "Regional (1,000–3,000 km)"
    return "Far (>3,000 km)"


def _human_feature(name: str) -> str:
    return {
        "year": "year",
        "distance_km": "distance",
        "prev_flow_log": "previous corridor flow",
        "origin_prev_total_log": "origin previous pressure",
        "host_prev_total_log": "host previous pressure",
        "band__Near (<1,000 km)": "near band",
        "band__Regional (1,000–3,000 km)": "regional band",
        "band__Far (>3,000 km)": "far band",
    }.get(name, name)


def _corridor_year_table(d: pd.DataFrame) -> pd.DataFrame:
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
                "distance_band": _distance_band(distance_km),
                "value_observed": float(r["value_observed"]),
            }
        )

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)

    # Previous-year flow for the same origin-host pair.
    prev_pair = out[["year", "origin", "host", "value_observed"]].copy()
    prev_pair["year"] = prev_pair["year"] + 1
    prev_pair = prev_pair.rename(columns={"value_observed": "previous_year_flow"})
    out = out.merge(prev_pair, on=["year", "origin", "host"], how="left")

    # Previous-year origin pressure.
    origin_prev = (
        out.groupby(["year", "origin"], as_index=False)
        .agg(origin_total_previous_year=("value_observed", "sum"))
    )
    origin_prev["year"] = origin_prev["year"] + 1
    out = out.merge(origin_prev, on=["year", "origin"], how="left")

    # Previous-year host pressure.
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


def _train_model(d: pd.DataFrame) -> ModelBundle:
    if not SKLEARN_AVAILABLE:
        return ModelBundle(False, "scikit-learn is not installed.", None)

    table = _corridor_year_table(d)

    if table.empty or len(table) < 80:
        return ModelBundle(False, "Not enough corridor-year rows for a stable model.", None)

    years = sorted(table["year"].dropna().astype(int).unique().tolist())

    if len(years) < 5:
        return ModelBundle(False, "Not enough years for train/test validation.", None)

    test_years = years[-3:] if len(years) >= 8 else years[-2:]

    train = table[~table["year"].isin(test_years)].copy()
    test = table[table["year"].isin(test_years)].copy()

    if len(train) < 50 or len(test) < 10:
        return ModelBundle(False, "Train/test split is too small.", None)

    x_train = _feature_matrix(train)
    y_train = train["target_log_flow"].to_numpy()

    x_test = _feature_matrix(test)
    y_test = test["target_log_flow"].to_numpy()

    model = RandomForestRegressor(
        n_estimators=140,
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


def _observed_distance_mix(d: pd.DataFrame) -> pd.DataFrame:
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


def _selected_year_predictions(bundle: ModelBundle, selected: pd.DataFrame, year: int) -> pd.DataFrame:
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
    pred_base["prediction_year"] = target_year

    return pred_base


def _actual_vs_predicted_distance_mix(bundle: ModelBundle, selected: pd.DataFrame, year: int) -> pd.DataFrame:
    pred_base = _selected_year_predictions(bundle, selected, year)

    if pred_base.empty:
        return pd.DataFrame()

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
        agg["year"] = int(pred_base["prediction_year"].iloc[0])
        rows.append(agg)

    out = pd.concat(rows, ignore_index=True)
    out["distance_band"] = pd.Categorical(
        out["distance_band"],
        categories=DISTANCE_ORDER,
        ordered=True,
    )

    return out.sort_values(["distance_band", "series"])


def _distance_uncertainty(bundle: ModelBundle, selected: pd.DataFrame, year: int) -> pd.DataFrame:
    """Approximate uncertainty using tree-level RandomForest predictions."""
    if not bundle.ok or bundle.model is None or not hasattr(bundle.model, "estimators_"):
        return pd.DataFrame()

    pred_base = _selected_year_predictions(bundle, selected, year)

    if pred_base.empty:
        return pd.DataFrame()

    x = _feature_matrix(pred_base)

    rows = []

    for estimator in bundle.model.estimators_[:80]:
        pred_log = estimator.predict(x)
        pred_value = np.expm1(pred_log).clip(min=0)
        temp = pred_base[["distance_band"]].copy()
        temp["pred_value"] = pred_value

        agg = (
            temp.groupby("distance_band", as_index=False, observed=False)
            .agg(value=("pred_value", "sum"))
        )

        total = float(agg["value"].sum())
        agg["share"] = np.where(total > 0, agg["value"] / total, 0)
        rows.append(agg)

    if not rows:
        return pd.DataFrame()

    sim = pd.concat(rows, keys=range(len(rows)), names=["tree_id"]).reset_index(level=0)

    out = (
        sim.groupby("distance_band", observed=False)["share"]
        .quantile([0.10, 0.50, 0.90])
        .unstack()
        .reset_index()
        .rename(columns={0.10: "p10", 0.50: "p50", 0.90: "p90"})
    )

    out["distance_band"] = pd.Categorical(out["distance_band"], categories=DISTANCE_ORDER, ordered=True)
    return out.sort_values("distance_band")


def _feature_bars(bundle: ModelBundle) -> list:
    if not bundle.ok or bundle.feature_importance is None or bundle.feature_importance.empty:
        return [ui.div("Feature importance is unavailable.", class_="mlv-muted")]

    imp = bundle.feature_importance.copy().head(6)
    max_imp = max(float(imp["importance"].max()), 1e-9)

    rows = []

    for _, r in imp.iterrows():
        pct = 100 * float(r["importance"]) / max_imp
        rows.append(
            ui.div(
                ui.div(_human_feature(str(r["feature"])), class_="mlv-feature-name"),
                ui.div(
                    ui.div(style=f"width:{pct:.1f}%"),
                    class_="mlv-feature-track",
                ),
                ui.div(f"{float(r['importance']):.3f}", class_="mlv-feature-score"),
                class_="mlv-feature-row",
            )
        )

    return rows


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @reactive.calc
    def model_bundle():
        d = data.time_series.copy()

        if "population_type_std" in d.columns:
            d = d[d["population_type_std"].isin(state.types())]

        return _train_model(d)

    @output
    @render_widget
    def ml_observed_distance_stack_plot():
        d = state.stock_all_years_same_filters()
        out = _observed_distance_mix(d)

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
            hover_data={"share": ":.1%", "value_observed": ":,.0f", "total": ":,.0f"},
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
    def ml_prediction_mix_plot():
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
            hover_data={"share": ":.1%", "value": ":,.0f", "year": True},
        )

        fig.update_traces(texttemplate="%{text:.0%}", textposition="outside")
        fig.update_layout(
            height=520,
            margin={"l": 52, "r": 24, "t": 14, "b": 70},
            legend_title_text="",
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        fig.update_yaxes(title="Share of selected-year corridor stock", tickformat=".0%", range=[0, 1])
        fig.update_xaxes(title="Distance band")

        return safe_fig(fig)

    @output
    @render_widget
    def ml_top_destination_plot():
        bundle = model_bundle()

        if not bundle.ok:
            return empty_fig(f"ML model unavailable: {bundle.reason}", 520)

        selected = state.stock_all_years_same_filters()
        pred = _selected_year_predictions(bundle, selected, state.year())

        if pred.empty:
            return empty_fig("No selected-year rows for destination prediction", 520)

        agg = (
            pred.groupby("host", as_index=False)
            .agg(actual_value=("actual_value", "sum"), predicted_value=("predicted_value", "sum"))
        )
        agg["score"] = agg[["actual_value", "predicted_value"]].max(axis=1)
        agg = agg.sort_values("score", ascending=False).head(10).sort_values("score", ascending=True)

        long = agg.melt(
            id_vars=["host"],
            value_vars=["actual_value", "predicted_value"],
            var_name="series",
            value_name="people",
        )
        long["series"] = long["series"].map(
            {"actual_value": "Actual observed", "predicted_value": "ML predicted"}
        )

        fig = px.bar(
            long,
            x="people",
            y="host",
            color="series",
            orientation="h",
            barmode="group",
            color_discrete_map={
                "Actual observed": "#64748b",
                "ML predicted": ORANGE,
            },
            hover_data={"people": ":,.0f"},
        )

        fig.update_layout(
            height=520,
            margin={"l": 130, "r": 24, "t": 14, "b": 54},
            legend_title_text="",
        )
        fig.update_xaxes(title="People", tickformat="~s")
        fig.update_yaxes(title="Host destination")

        return safe_fig(fig)

    @output
    @render_widget
    def ml_similarity_plot():
        if not SKLEARN_AVAILABLE:
            return empty_fig("scikit-learn is required for the similarity explorer", 520)

        selected = state.stock_all_years_same_filters()
        table = _corridor_year_table(selected)

        if table.empty or len(table) < 10:
            # fallback to full scope if selected filters are too narrow
            full = data.time_series.copy()
            if "population_type_std" in full.columns:
                full = full[full["population_type_std"].isin(state.types())]
            table = _corridor_year_table(full)

        if table.empty or len(table) < 10:
            return empty_fig("Not enough corridor rows for similarity explorer", 520)

        # Keep plot readable and fast.
        table = table.sort_values("value_observed", ascending=False).head(700).copy()

        x = _feature_matrix(table)

        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x)

        coords = PCA(n_components=2, random_state=42).fit_transform(x_scaled)

        table["component_1"] = coords[:, 0]
        table["component_2"] = coords[:, 1]
        table["flow_size"] = np.log1p(table["value_observed"])
        table["route"] = table["origin"] + " → " + table["host"]

        fig = px.scatter(
            table,
            x="component_1",
            y="component_2",
            color="distance_band",
            size="flow_size",
            hover_name="route",
            hover_data={
                "year": True,
                "distance_km": ":.0f",
                "value_observed": ":,.0f",
                "component_1": False,
                "component_2": False,
                "flow_size": False,
            },
            category_orders={"distance_band": DISTANCE_ORDER},
            color_discrete_map={
                "Near (<1,000 km)": ORANGE,
                "Regional (1,000–3,000 km)": BLUE,
                "Far (>3,000 km)": PURPLE,
            },
        )

        fig.update_traces(marker={"opacity": 0.72, "line": {"width": 0.5, "color": "white"}})
        fig.update_layout(
            height=520,
            margin={"l": 46, "r": 24, "t": 14, "b": 54},
            legend_title_text="Distance band",
        )
        fig.update_xaxes(title="Similarity component 1")
        fig.update_yaxes(title="Similarity component 2")

        return safe_fig(fig)

    @output
    @render.ui
    def ml_pipeline_card():
        bundle = model_bundle()

        if not bundle.ok:
            return ui.div(
                ui.div("ML visualized", class_="explain-kicker"),
                ui.h3("Model not available"),
                ui.p(bundle.reason),
                class_="mlv-card",
            )

        selected = state.stock_all_years_same_filters()
        uncertainty = _distance_uncertainty(bundle, selected, state.year())

        uncertainty_cards = []
        if not uncertainty.empty:
            for _, r in uncertainty.iterrows():
                uncertainty_cards.append(
                    ui.div(
                        ui.div(str(r["distance_band"]), class_="mlv-interval-label"),
                        ui.strong(f"{float(r['p50']):.0%}"),
                        ui.span(f"{float(r['p10']):.0%}–{float(r['p90']):.0%} tree interval"),
                        class_="mlv-interval-card",
                    )
                )

        return ui.div(
            ui.div("ML visualized", class_="explain-kicker"),
            ui.h3("How the model learns corridor pressure"),
            ui.div(
                ui.div(
                    ui.div("01", class_="mlv-step-num"),
                    ui.strong("Features"),
                    ui.span("distance + lagged flow + origin/host pressure"),
                    class_="mlv-step",
                ),
                ui.div("→", class_="mlv-arrow"),
                ui.div(
                    ui.div("02", class_="mlv-step-num"),
                    ui.strong("Model"),
                    ui.span("RandomForestRegressor"),
                    class_="mlv-step",
                ),
                ui.div("→", class_="mlv-arrow"),
                ui.div(
                    ui.div("03", class_="mlv-step-num"),
                    ui.strong("Target"),
                    ui.span("log(1 + corridor flow)"),
                    class_="mlv-step",
                ),
                ui.div("→", class_="mlv-arrow"),
                ui.div(
                    ui.div("04", class_="mlv-step-num"),
                    ui.strong("Output"),
                    ui.span("predicted destination and distance mix"),
                    class_="mlv-step",
                ),
                class_="mlv-pipeline",
            ),
            ui.div(
                ui.div(
                    ui.div("Train rows", class_="mlv-metric-label"),
                    ui.strong(f"{bundle.train_rows:,}"),
                    class_="mlv-metric",
                ),
                ui.div(
                    ui.div("Test rows", class_="mlv-metric-label"),
                    ui.strong(f"{bundle.test_rows:,}"),
                    class_="mlv-metric",
                ),
                ui.div(
                    ui.div("MAE log target", class_="mlv-metric-label"),
                    ui.strong(_fmt(bundle.mae_log, 3)),
                    class_="mlv-metric",
                ),
                ui.div(
                    ui.div("R²", class_="mlv-metric-label"),
                    ui.strong(_fmt(bundle.r2, 3)),
                    class_="mlv-metric",
                ),
                class_="mlv-metrics",
            ),
            ui.div(
                ui.div("Uncertainty from the tree ensemble", class_="mlv-subtitle"),
                ui.div(*uncertainty_cards, class_="mlv-interval-grid") if uncertainty_cards else ui.div("Interval unavailable for this filter.", class_="mlv-muted"),
                class_="mlv-interval-wrap",
            ),
            ui.div(
                ui.div("What mattered most?", class_="mlv-subtitle"),
                *_feature_bars(bundle),
                class_="mlv-features",
            ),
            ui.p(
                "This is a predictive baseline, not causal war forecasting.",
                class_="mlv-caution",
            ),
            class_="mlv-card",
        )
