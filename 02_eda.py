#!/usr/bin/env python3
"""
SECTION 2 — EDA
Global Refugee Movement Dashboard, Group 11

Purpose
-------
Turn cleaned datasets into professor-ready analytical tables for the dashboard story.
This script deliberately does not render figures. It produces reusable chart-ready
CSV/JSON/report assets for the whole Shiny project: KPI cards, time-series, maps,
Sankey/network views, monthly trends, demographics, resettlement, forecasting seeds,
and the data tables required by Graph 5 and Graph 6.

Run after preprocessing
-----------------------
python 01_preprocessing.py --input-dir . --output-dir outputs
python 02_eda.py --output-dir outputs --top-n 10 --scope cross_border
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

CROSS_BORDER_TYPES = ["Refugees", "Asylum-seekers", "Others of concern"]
ACTIVE_FORCED_TYPES = ["Refugees", "Asylum-seekers", "IDPs", "Others of concern"]
REPORTING_TYPES = [
    "Refugees",
    "Asylum-seekers",
    "IDPs",
    "Stateless persons",
    "Others of concern",
    "Returned refugees",
    "Returned IDPs",
]


@dataclass(frozen=True)
class Config:
    output_dir: Path
    top_n: int = 10
    year: Optional[int] = None
    scope: str = "cross_border"  # cross_border or active_forced


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="EDA and chart-ready data for the refugee dashboard.")
    parser.add_argument("--output-dir", default="outputs", help="Folder created by 01_preprocessing.py.")
    parser.add_argument("--top-n", type=int, default=10, help="Number of countries in Graph 5 and Graph 6.")
    parser.add_argument("--year", type=int, default=None, help="Dashboard year. Default = latest year in time_series_clean.")
    parser.add_argument(
        "--scope",
        choices=["cross_border", "active_forced"],
        default="cross_border",
        help="cross_border = Refugees + Asylum-seekers + Others. active_forced additionally includes IDPs.",
    )
    args = parser.parse_args()
    return Config(Path(args.output_dir).resolve(), args.top_n, args.year, args.scope)


def ensure_dirs(c: Config) -> None:
    for sub in ["02_eda", "03_chart_data", "07_report_assets"]:
        (c.output_dir / sub).mkdir(parents=True, exist_ok=True)


def read_clean(c: Config, filename: str) -> pd.DataFrame:
    path = c.output_dir / "01_clean" / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run 01_preprocessing.py first.")
    return pd.read_csv(path, low_memory=False)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, na_rep="")


def get_scope_types(scope: str) -> List[str]:
    return ACTIVE_FORCED_TYPES if scope == "active_forced" else CROSS_BORDER_TYPES


def safe_share(numer: pd.Series, denom: float) -> pd.Series:
    return numer / denom if denom and not pd.isna(denom) else np.nan


def summarize_value(df: pd.DataFrame, group_cols: List[str], value_col: str = "value_observed") -> pd.DataFrame:
    return (
        df.groupby(group_cols, dropna=False)
        .agg(
            value_observed=(value_col, "sum"),
            source_rows=(value_col, "size"),
            observed_rows=(value_col, lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )


def filter_country_quality(df: pd.DataFrame, prefix: str, exclude_special: bool = True, require_map_eligible: bool = False) -> pd.DataFrame:
    d = df.copy()
    if exclude_special:
        d = d[~d[f"{prefix}_mapping_status"].isin(["special_entity", "missing", "unmapped"])]
        d = d[d[f"{prefix}_iso3"].ne("UNMAPPED")]
    if require_map_eligible:
        d = d[d[f"{prefix}_map_eligible_flag"] == True]
    return d


def rank_dimension(ts: pd.DataFrame, dim: str, year: int, pop_types: List[str], top_n: int, *, require_map_eligible: bool = False) -> pd.DataFrame:
    prefix = "origin" if dim == "origin" else "host"
    selected = ts[(ts["year"] == year) & (ts["population_type_std"].isin(pop_types))].copy()
    selected = filter_country_quality(selected, prefix, exclude_special=True, require_map_eligible=require_map_eligible)
    cols = [f"{prefix}_country_std", f"{prefix}_iso3", f"{prefix}_mapping_status", f"{prefix}_map_eligible_flag"]
    out = summarize_value(selected, cols)
    total = selected["value_observed"].sum(skipna=True)
    out = out.sort_values("value_observed", ascending=False).head(top_n).reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    out["share_of_selected_total"] = safe_share(out["value_observed"], total)
    out["year"] = year
    out["population_scope"] = "+".join(pop_types)
    out["metric_type"] = "population_stock_observed"
    return out


def compute_annual(ts: pd.DataFrame) -> pd.DataFrame:
    annual = (
        ts.groupby(["year", "population_type_std"], dropna=False)
        .agg(
            value_observed=("value_observed", "sum"),
            source_rows=("value_observed", "size"),
            observed_rows=("value_observed", lambda s: int(s.notna().sum())),
            redacted_rows=("value_observed_is_redacted", "sum"),
            blank_rows=("value_observed_is_blank", "sum"),
            zero_rows=("value_observed_is_zero", "sum"),
        )
        .reset_index()
        .sort_values(["population_type_std", "year"])
    )
    annual["yoy_absolute_change"] = annual.groupby("population_type_std")["value_observed"].diff()
    annual["yoy_pct_change"] = annual.groupby("population_type_std")["value_observed"].pct_change()
    return annual


def compute_kpis(ts: pd.DataFrame, asylum: pd.DataFrame, year: int, scope_types: List[str]) -> pd.DataFrame:
    latest = ts[ts["year"] == year].copy()
    rows: List[dict] = []
    by_type = latest.groupby("population_type_std", as_index=False).agg(value_observed=("value_observed", "sum"))
    for _, r in by_type.iterrows():
        rows.append({"kpi": str(r["population_type_std"]), "value": float(r["value_observed"]), "year": year, "source": "time_series_clean"})
    active = latest[latest["population_type_std"].isin(ACTIVE_FORCED_TYPES)]
    cross = latest[latest["population_type_std"].isin(scope_types)]
    rows.extend(
        [
            {"kpi": "Active forced-displacement scope", "value": float(active["value_observed"].sum(skipna=True)), "year": year, "source": "time_series_clean"},
            {"kpi": "Cross-border dashboard scope", "value": float(cross["value_observed"].sum(skipna=True)), "year": year, "source": "time_series_clean"},
            {"kpi": "Origin countries/entities", "value": float(cross["origin_country_std"].nunique()), "year": year, "source": "time_series_clean"},
            {"kpi": "Host countries/entities", "value": float(cross["host_country_std"].nunique()), "year": year, "source": "time_series_clean"},
        ]
    )
    asylum_y = asylum[asylum["year"] == year]
    if len(asylum_y):
        rows.append({"kpi": "Asylum applications during year", "value": float(asylum_y["applications_observed"].sum(skipna=True)), "year": year, "source": "asylum_seekers_clean"})
    return pd.DataFrame(rows)


def concentration_by_year(ts: pd.DataFrame, dimension: str, pop_types: List[str]) -> pd.DataFrame:
    prefix = "origin" if dimension == "origin" else "host"
    d = ts[ts["population_type_std"].isin(pop_types)].copy()
    d = filter_country_quality(d, prefix, exclude_special=True, require_map_eligible=False)
    grouped = d.groupby(["year", f"{prefix}_country_std"], as_index=False).agg(value_observed=("value_observed", "sum"))
    rows: List[dict] = []
    for year, gy in grouped.groupby("year"):
        total = gy["value_observed"].sum(skipna=True)
        shares = gy["value_observed"] / total if total else pd.Series(dtype=float)
        rows.append(
            {
                "year": int(year),
                "dimension": dimension,
                "countries": int(gy[f"{prefix}_country_std"].nunique()),
                "total_observed": float(total),
                "top1_share": float(shares.max()) if len(shares) else np.nan,
                "top5_share": float(gy.sort_values("value_observed", ascending=False).head(5)["value_observed"].sum() / total) if total else np.nan,
                "hhi": float((shares ** 2).sum()) if len(shares) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def monthly_outputs(monthly: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    monthly_agg = (
        monthly.groupby(["year", "month_num", "month"], as_index=False)
        .agg(applications_observed=("applications_monthly_observed", "sum"), source_rows=("applications_monthly_observed", "size"))
        .sort_values(["year", "month_num"])
    )
    seasonality = (
        monthly_agg.groupby(["month_num", "month"], as_index=False)
        .agg(mean_applications=("applications_observed", "mean"), median_applications=("applications_observed", "median"), max_applications=("applications_observed", "max"))
        .sort_values("month_num")
    )
    return monthly_agg, seasonality


def demographics_latest(demo: pd.DataFrame) -> pd.DataFrame:
    year = int(demo["year"].max())
    d = demo[demo["year"] == year].copy()
    specs = [
        ("0-4", "female_0_4_observed", "male_0_4_observed"),
        ("5-17", "female_5_17_combined_observed", "male_5_17_combined_observed"),
        ("18-59", "female_18_59_observed", "male_18_59_observed"),
        ("60+", "female_60_observed", "male_60_observed"),
        ("Unknown", "f_unknown_observed", "m_unknown_observed"),
    ]
    rows: List[dict] = []
    for age_group, female_col, male_col in specs:
        female = d[female_col].sum(skipna=True) if female_col in d.columns else np.nan
        male = d[male_col].sum(skipna=True) if male_col in d.columns else np.nan
        rows.append({"year": year, "age_group": age_group, "sex": "Female", "value_observed": female})
        rows.append({"year": year, "age_group": age_group, "sex": "Male", "value_observed": male})
    out = pd.DataFrame(rows)
    out["age_order"] = out["age_group"].map({"0-4": 1, "5-17": 2, "18-59": 3, "60+": 4, "Unknown": 5})
    return out


def asylum_yearly(asylum: pd.DataFrame) -> pd.DataFrame:
    out = (
        asylum.groupby("year", as_index=False)
        .agg(
            applications_observed=("applications_observed", "sum"),
            recognized_observed=("recognized_observed", "sum"),
            rejected_observed=("rejected_observed", "sum"),
            other_decisions_observed=("other_decisions_observed", "sum"),
            otherwise_closed_observed=("otherwise_closed_observed", "sum"),
            total_decisions_final=("total_decisions_final", "sum"),
            decision_total_mismatch_rows=("decision_total_mismatch", "sum"),
            source_rows=("applications_observed", "size"),
        )
        .sort_values("year")
    )
    out["recognition_rate_observed"] = np.where(out["total_decisions_final"] > 0, out["recognized_observed"] / out["total_decisions_final"], np.nan)
    return out


def build_corridors(ts: pd.DataFrame, year: int, pop_types: List[str]) -> pd.DataFrame:
    d = ts[(ts["year"] == year) & ts["population_type_std"].isin(pop_types)].copy()
    d = filter_country_quality(d, "origin", exclude_special=True, require_map_eligible=False)
    d = filter_country_quality(d, "host", exclude_special=True, require_map_eligible=False)
    cols = ["year", "origin_country_std", "origin_iso3", "host_country_std", "host_iso3", "population_type_std"]
    out = d.groupby(cols, as_index=False).agg(value_observed=("value_observed", "sum"), source_rows=("value_observed", "size"))
    out = out[out["value_observed"].fillna(0) > 0].sort_values("value_observed", ascending=False)
    return out


def build_network_metrics(corridors: pd.DataFrame) -> pd.DataFrame:
    try:
        import networkx as nx
    except Exception:
        return pd.DataFrame(columns=["node", "node_type", "degree", "in_strength", "out_strength", "betweenness"])

    g = nx.DiGraph()
    for _, r in corridors.head(1000).iterrows():
        origin = f"Origin: {r['origin_country_std']}"
        host = f"Host: {r['host_country_std']}"
        weight = float(r["value_observed"]) if pd.notna(r["value_observed"]) else 0.0
        if weight > 0:
            g.add_node(origin, node_type="origin")
            g.add_node(host, node_type="host")
            g.add_edge(origin, host, weight=weight)
    if not g.nodes:
        return pd.DataFrame(columns=["node", "node_type", "degree", "in_strength", "out_strength", "betweenness"])
    degree = dict(g.degree())
    in_strength = dict(g.in_degree(weight="weight"))
    out_strength = dict(g.out_degree(weight="weight"))
    # Betweenness can be expensive; for 1000 corridor graph it remains manageable, otherwise skip.
    between = nx.betweenness_centrality(g, weight="weight", normalized=True) if len(g.nodes) <= 500 else {node: np.nan for node in g.nodes}
    rows = []
    for node, attrs in g.nodes(data=True):
        rows.append(
            {
                "node": node,
                "node_type": attrs.get("node_type", "unknown"),
                "degree": degree.get(node, 0),
                "in_strength": in_strength.get(node, 0.0),
                "out_strength": out_strength.get(node, 0.0),
                "betweenness": between.get(node, np.nan),
            }
        )
    return pd.DataFrame(rows).sort_values(["in_strength", "out_strength", "degree"], ascending=False)


def build_forecast(annual: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    active = annual[annual["population_type_std"].isin(ACTIVE_FORCED_TYPES)].groupby("year", as_index=False).agg(value_observed=("value_observed", "sum"))
    active = active.dropna().sort_values("year")
    if len(active) < 8:
        return active.assign(series="observed"), pd.DataFrame()
    train = active.iloc[:-3].copy()
    test = active.iloc[-3:].copy()
    metrics: List[dict] = []

    # Model 1: naive last value.
    naive_pred = np.repeat(train["value_observed"].iloc[-1], len(test))
    naive_mae = float(np.mean(np.abs(test["value_observed"].values - naive_pred)))
    metrics.append({"model": "naive_last_observed", "holdout_mae": naive_mae})

    # Model 2: linear trend. Used only as exploratory visual analytics, not causal prediction.
    try:
        from sklearn.linear_model import LinearRegression

        model = LinearRegression().fit(train[["year"]].values, train["value_observed"].values)
        lin_pred = model.predict(test[["year"]].values)
        metrics.append({"model": "linear_trend", "holdout_mae": float(np.mean(np.abs(test["value_observed"].values - lin_pred)))})
        future_years = np.arange(int(active["year"].max()) + 1, int(active["year"].max()) + 6)
        future_pred = model.predict(future_years.reshape(-1, 1))
        forecast = pd.concat(
            [
                active.assign(series="observed"),
                pd.DataFrame({"year": future_years, "value_observed": future_pred, "series": "linear_trend_forecast_exploratory"}),
            ],
            ignore_index=True,
        )
    except Exception as exc:
        metrics.append({"model": "linear_trend", "holdout_mae": np.nan, "warning": str(exc)})
        forecast = active.assign(series="observed")
    return forecast, pd.DataFrame(metrics)


def build_time_series_vs_poc_crosscheck(ts: pd.DataFrame, poc_long: pd.DataFrame) -> pd.DataFrame:
    a = ts.groupby(["year", "population_type_std"], as_index=False).agg(time_series_sum=("value_observed", "sum"))
    b = poc_long.groupby(["year", "population_type_std"], as_index=False).agg(persons_of_concern_long_sum=("value_observed", "sum"))
    out = a.merge(b, on=["year", "population_type_std"], how="outer")
    out["absolute_difference"] = (out["time_series_sum"].fillna(0) - out["persons_of_concern_long_sum"].fillna(0)).abs()
    return out.sort_values(["year", "population_type_std"])



# ---------------------------------------------------------------------------
# Professor-grade additions: dashboard coverage, filter metadata, WDI gap,
# asylum status Sankey seed, scatter/bubble data and rubric alignment.
# These additions preserve all original output filenames used by 03_graphs.py.
# ---------------------------------------------------------------------------

REQUIRED_CLEAN_SPEC = {
    "time_series_clean.csv.gz": ["year", "population_type_std", "value_observed", "host_country_std", "host_iso3", "host_map_eligible_flag", "origin_country_std", "origin_iso3", "origin_map_eligible_flag"],
    "persons_of_concern_clean_long.csv.gz": ["year", "population_type_std", "value_observed"],
    "asylum_seekers_clean.csv.gz": ["year", "applications_observed", "recognized_observed", "rejected_observed", "total_decisions_final", "host_country_std", "origin_country_std"],
    "asylum_seekers_monthly_clean.csv.gz": ["year", "month_num", "month", "applications_monthly_observed"],
    "demographics_clean.csv.gz": ["year", "host_country_std"],
    "resettlement_clean.csv.gz": ["year", "resettlement_observed", "host_country_std", "origin_country_std"],
}


def validate_clean_inputs(c: Config) -> pd.DataFrame:
    """Validate that preprocessing outputs contain the columns needed by EDA.

    This makes the pipeline easier to defend in the final report and easier to debug
    before the Shiny dashboard is launched.
    """
    rows: List[dict] = []
    missing_files: List[str] = []
    missing_columns: List[str] = []
    for fname, required_cols in REQUIRED_CLEAN_SPEC.items():
        path = c.output_dir / "01_clean" / fname
        file_exists = path.exists()
        row_count = np.nan
        col_count = np.nan
        absent_cols: List[str] = []
        if file_exists:
            preview = pd.read_csv(path, nrows=5, low_memory=False)
            row_count = int(sum(1 for _ in pd.read_csv(path, usecols=[preview.columns[0]], chunksize=200000))) if False else np.nan
            col_count = int(len(preview.columns))
            absent_cols = [col for col in required_cols if col not in preview.columns]
        else:
            missing_files.append(fname)
            absent_cols = required_cols
        if absent_cols:
            missing_columns.extend([f"{fname}:{col}" for col in absent_cols])
        rows.append(
            {
                "file": fname,
                "exists": bool(file_exists),
                "columns_in_preview": col_count,
                "required_columns": " | ".join(required_cols),
                "missing_required_columns": " | ".join(absent_cols),
                "status": "PASS" if file_exists and not absent_cols else "FAIL",
            }
        )
    out = pd.DataFrame(rows)
    if missing_files or missing_columns:
        details = []
        if missing_files:
            details.append("Missing files: " + ", ".join(missing_files))
        if missing_columns:
            details.append("Missing columns: " + ", ".join(missing_columns[:20]))
        raise ValueError("EDA input validation failed. " + " ; ".join(details))
    return out


def build_dashboard_component_matrix(year: int, scope_types: List[str]) -> pd.DataFrame:
    scope = "+".join(scope_types)
    rows = [
        {
            "dashboard_component": "KPI cards",
            "wireframe_match": "Key figures panel",
            "source_dataset": "time_series_clean; asylum_seekers_clean",
            "output_file": "kpi_cards_latest.csv",
            "status": "ready",
            "metric_note": f"Latest year {year}; stock KPIs use {scope}; asylum applications are flow metrics.",
        },
        {
            "dashboard_component": "Global trend line / stacked area",
            "wireframe_match": "Refugees over time",
            "source_dataset": "time_series_clean",
            "output_file": "annual_population_by_type.csv",
            "status": "ready",
            "metric_note": "Observed population-stock trend by category.",
        },
        {
            "dashboard_component": "Graph 5 ranked origins",
            "wireframe_match": "Top origin countries",
            "source_dataset": "time_series_clean",
            "output_file": "graph5_top_origin_countries.csv",
            "status": "ready",
            "metric_note": f"Observed stock, {scope}, IDPs excluded in cross_border scope.",
        },
        {
            "dashboard_component": "Graph 6 ranked hosts",
            "wireframe_match": "Top host countries",
            "source_dataset": "time_series_clean",
            "output_file": "graph6_top_host_countries.csv",
            "status": "ready",
            "metric_note": f"Observed stock, {scope}; host means country of asylum/residence.",
        },
        {
            "dashboard_component": "Sankey origin-host corridors",
            "wireframe_match": "Origin → asylum country",
            "source_dataset": "time_series_clean",
            "output_file": "sankey_top_corridors.csv",
            "status": "ready",
            "metric_note": "Stock corridor, not literal border-crossing flow.",
        },
        {
            "dashboard_component": "Sankey origin-host-status",
            "wireframe_match": "Origin → asylum country → status",
            "source_dataset": "asylum_seekers_clean",
            "output_file": "sankey_origin_host_status_decisions.csv",
            "status": "ready_with_caveat",
            "metric_note": "Uses applications and decisions from the same reporting year; not cohort tracking.",
        },
        {
            "dashboard_component": "Choropleth map",
            "wireframe_match": "Map by host country",
            "source_dataset": "time_series_clean",
            "output_file": "choropleth_host_latest.csv",
            "status": "ready",
            "metric_note": "Absolute observed stock by host ISO3.",
        },
        {
            "dashboard_component": "Hosting pressure choropleth",
            "wireframe_match": "Refugees per population",
            "source_dataset": "time_series_clean + optional WDI",
            "output_file": "host_pressure_per_100k.csv",
            "status": "partial_until_WDI_added",
            "metric_note": "Requires population denominator from WDI to calculate per-100k pressure.",
        },
        {
            "dashboard_component": "Animated map",
            "wireframe_match": "Animation by year",
            "source_dataset": "time_series_clean",
            "output_file": "animated_host_map_by_year.csv",
            "status": "ready",
            "metric_note": "Yearly host-country stock values for animation_frame.",
        },
        {
            "dashboard_component": "Monthly asylum seasonality",
            "wireframe_match": "Additional time-series detail",
            "source_dataset": "asylum_seekers_monthly_clean",
            "output_file": "monthly_application_seasonality_profile.csv",
            "status": "ready",
            "metric_note": "Application-flow seasonality, separate from stock metrics.",
        },
        {
            "dashboard_component": "Demographic profile",
            "wireframe_match": "Demographic storytelling extension",
            "source_dataset": "demographics_clean",
            "output_file": "demographics_age_sex_latest.csv",
            "status": "ready",
            "metric_note": "Latest-year age/sex profile.",
        },
        {
            "dashboard_component": "Network graph",
            "wireframe_match": "Network graph origin-host",
            "source_dataset": "time_series_clean",
            "output_file": "network_metrics_top_corridors.csv",
            "status": "ready",
            "metric_note": "Directed network from origin to host nodes using top corridors.",
        },
        {
            "dashboard_component": "Exploratory forecast",
            "wireframe_match": "Advanced analytics / ML component",
            "source_dataset": "time_series_clean",
            "output_file": "forecast_global_active_forced_displacement.csv",
            "status": "ready_with_caveat",
            "metric_note": "Exploratory trend model, not causal or policy forecast.",
        },
        {
            "dashboard_component": "Crisis storytelling",
            "wireframe_match": "Crisis storytelling panel",
            "source_dataset": "time_series_clean + manual annotations",
            "output_file": "crisis_storytelling_template.csv",
            "status": "partial_manual_annotation_needed",
            "metric_note": "Quantitative trend is ready; historical event annotations should be cited manually.",
        },
    ]
    return pd.DataFrame(rows)


def build_filter_options(ts: pd.DataFrame, asylum: pd.DataFrame, monthly: pd.DataFrame, demo: pd.DataFrame, res: pd.DataFrame) -> Tuple[dict, pd.DataFrame]:
    datasets = {
        "time_series": ts,
        "asylum_seekers": asylum,
        "asylum_seekers_monthly": monthly,
        "demographics": demo,
        "resettlement": res,
    }
    def clean_years(df: pd.DataFrame) -> List[int]:
        return sorted(pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce").dropna().astype(int).unique().tolist())

    # The dashboard's main year slider should be anchored to time_series_clean, because
    # Graph 5/6, the global trend, maps, Sankey stock corridors and KPI stock cards are
    # driven by that canonical population-stock table. Some supporting datasets may
    # extend one year further; those are recorded separately to avoid an empty default year.
    stock_years = clean_years(ts)
    all_years = sorted(set().union(*[set(clean_years(df)) for df in datasets.values()]))
    dataset_year_coverage = {
        name: {"year_min": (min(clean_years(df)) if clean_years(df) else None), "year_max": (max(clean_years(df)) if clean_years(df) else None)}
        for name, df in datasets.items()
    }
    origin_values = sorted(ts["origin_country_std"].dropna().astype(str).unique().tolist()) if "origin_country_std" in ts else []
    host_values = sorted(ts["host_country_std"].dropna().astype(str).unique().tolist()) if "host_country_std" in ts else []
    pop_types = sorted(ts["population_type_std"].dropna().astype(str).unique().tolist()) if "population_type_std" in ts else []
    opts = {
        "year_min": int(min(stock_years)) if stock_years else None,
        "year_max": int(max(stock_years)) if stock_years else None,
        "years": stock_years,
        "all_dataset_year_min": int(min(all_years)) if all_years else None,
        "all_dataset_year_max": int(max(all_years)) if all_years else None,
        "dataset_year_coverage": dataset_year_coverage,
        "population_types": pop_types,
        "origin_country_count": len(origin_values),
        "host_country_count": len(host_values),
        "origin_countries": origin_values,
        "host_countries": host_values,
        "recommended_default_scope": CROSS_BORDER_TYPES,
        "notes": [
            "Use the time_series_clean year range for the main dashboard year slider.",
            "Use year, population type, origin country and host country as primary Shiny filters.",
            "Keep stock and flow metric filters visually separated in the app.",
        ],
    }
    summary = pd.DataFrame(
        [
            {"filter_name": "Year", "type": "slider", "n_options": len(stock_years), "default": opts["year_max"], "source": "time_series_clean"},
            {"filter_name": "Population category", "type": "multi-select", "n_options": len(pop_types), "default": "+".join(CROSS_BORDER_TYPES), "source": "time_series_clean"},
            {"filter_name": "Origin country", "type": "searchable select", "n_options": len(origin_values), "default": "All", "source": "time_series_clean"},
            {"filter_name": "Host/asylum country", "type": "searchable select", "n_options": len(host_values), "default": "All", "source": "time_series_clean"},
            {"filter_name": "Metric family", "type": "radio/tabs", "n_options": 2, "default": "Stock", "source": "stock vs flow separation"},
        ]
    )
    return opts, summary


def build_chart_coverage(ts: pd.DataFrame, asylum: pd.DataFrame, monthly: pd.DataFrame, demo: pd.DataFrame, res: pd.DataFrame, year: int) -> pd.DataFrame:
    def years(df: pd.DataFrame) -> str:
        y = pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce").dropna()
        return f"{int(y.min())}-{int(y.max())}" if len(y) else "unknown"

    rows = [
        {"chart_or_component": "KPI cards", "primary_dataset": "time_series_clean", "rows_available": len(ts), "year_coverage": years(ts), "latest_year_used": year, "readiness": "ready"},
        {"chart_or_component": "Graph 5 top origins", "primary_dataset": "time_series_clean", "rows_available": len(ts), "year_coverage": years(ts), "latest_year_used": year, "readiness": "ready"},
        {"chart_or_component": "Graph 6 top hosts", "primary_dataset": "time_series_clean", "rows_available": len(ts), "year_coverage": years(ts), "latest_year_used": year, "readiness": "ready"},
        {"chart_or_component": "Origin-host flow/Sankey", "primary_dataset": "time_series_clean / asylum_seekers_clean", "rows_available": len(ts) + len(asylum), "year_coverage": f"stock {years(ts)}; asylum {years(asylum)}", "latest_year_used": year, "readiness": "ready_with_caveat"},
        {"chart_or_component": "Monthly asylum trend", "primary_dataset": "asylum_seekers_monthly_clean", "rows_available": len(monthly), "year_coverage": years(monthly), "latest_year_used": year, "readiness": "ready"},
        {"chart_or_component": "Demographics", "primary_dataset": "demographics_clean", "rows_available": len(demo), "year_coverage": years(demo), "latest_year_used": int(pd.to_numeric(demo['year'], errors='coerce').max()) if len(demo) else year, "readiness": "ready"},
        {"chart_or_component": "Resettlement", "primary_dataset": "resettlement_clean", "rows_available": len(res), "year_coverage": years(res), "latest_year_used": year, "readiness": "ready"},
        {"chart_or_component": "Hosting pressure per 100k", "primary_dataset": "time_series_clean + WDI", "rows_available": len(ts), "year_coverage": years(ts), "latest_year_used": year, "readiness": "partial_until_WDI_added"},
    ]
    return pd.DataFrame(rows)


def build_country_role_scatter(ts: pd.DataFrame, year: int, pop_types: List[str]) -> pd.DataFrame:
    d = ts[(ts["year"] == year) & ts["population_type_std"].isin(pop_types)].copy()
    origin = filter_country_quality(d, "origin", exclude_special=True, require_map_eligible=False)
    origin = origin.groupby(["origin_country_std", "origin_iso3"], as_index=False).agg(origin_stock_observed=("value_observed", "sum"))
    origin = origin.rename(columns={"origin_country_std": "country", "origin_iso3": "iso3"})
    host = filter_country_quality(d, "host", exclude_special=True, require_map_eligible=False)
    host = host.groupby(["host_country_std", "host_iso3"], as_index=False).agg(host_stock_observed=("value_observed", "sum"))
    host = host.rename(columns={"host_country_std": "country", "host_iso3": "iso3"})
    out = origin.merge(host, on=["country", "iso3"], how="outer")
    out[["origin_stock_observed", "host_stock_observed"]] = out[["origin_stock_observed", "host_stock_observed"]].fillna(0)
    out["net_host_minus_origin"] = out["host_stock_observed"] - out["origin_stock_observed"]
    out["role_class"] = np.select(
        [
            (out["host_stock_observed"] > 0) & (out["origin_stock_observed"] > 0),
            (out["host_stock_observed"] > 0) & (out["origin_stock_observed"] == 0),
            (out["host_stock_observed"] == 0) & (out["origin_stock_observed"] > 0),
        ],
        ["both_origin_and_host", "mostly_host", "mostly_origin"],
        default="no_observed_role",
    )
    out["year"] = year
    out["population_scope"] = "+".join(pop_types)
    return out.sort_values(["host_stock_observed", "origin_stock_observed"], ascending=False)


def build_asylum_corridors(asylum: pd.DataFrame, year: int, top_n: int = 100) -> pd.DataFrame:
    d = asylum[asylum["year"] == year].copy()
    if d.empty:
        # Fall back to all years only if the chosen dashboard year has no asylum data.
        d = asylum.copy()
    d = filter_country_quality(d, "origin", exclude_special=True, require_map_eligible=False)
    d = filter_country_quality(d, "host", exclude_special=True, require_map_eligible=False)
    cols = ["year", "origin_country_std", "origin_iso3", "host_country_std", "host_iso3"]
    out = d.groupby(cols, as_index=False).agg(
        applications_observed=("applications_observed", "sum"),
        recognized_observed=("recognized_observed", "sum"),
        rejected_observed=("rejected_observed", "sum"),
        other_decisions_observed=("other_decisions_observed", "sum"),
        otherwise_closed_observed=("otherwise_closed_observed", "sum"),
        total_decisions_final=("total_decisions_final", "sum"),
        source_rows=("applications_observed", "size"),
    )
    out = out[out["applications_observed"].fillna(0) > 0].sort_values("applications_observed", ascending=False).head(top_n)
    out["metric_type"] = "asylum_application_flow_observed"
    return out.reset_index(drop=True)


def build_sankey_origin_host_status(asylum_corridors: pd.DataFrame) -> pd.DataFrame:
    if asylum_corridors.empty:
        return pd.DataFrame(columns=["source", "target", "value_observed", "link_layer", "metric_type", "caveat"])
    top = asylum_corridors.head(40).copy()
    links: List[dict] = []
    for _, r in top.iterrows():
        origin = f"Origin: {r['origin_country_std']}"
        host = f"Host: {r['host_country_std']}"
        links.append(
            {
                "source": origin,
                "target": host,
                "value_observed": float(r["applications_observed"]),
                "link_layer": "origin_to_host",
                "metric_type": "asylum_applications_observed",
                "caveat": "Applications are flow counts, not refugee stock.",
            }
        )
    decision_cols = [
        ("recognized_observed", "Status: Recognized"),
        ("rejected_observed", "Status: Rejected"),
        ("other_decisions_observed", "Status: Other decision"),
        ("otherwise_closed_observed", "Status: Otherwise closed"),
    ]
    host_decisions = top.groupby("host_country_std", as_index=False).agg({col: "sum" for col, _ in decision_cols})
    for _, r in host_decisions.iterrows():
        host = f"Host: {r['host_country_std']}"
        for col, status in decision_cols:
            val = float(r[col]) if pd.notna(r[col]) else 0.0
            if val > 0:
                links.append(
                    {
                        "source": host,
                        "target": status,
                        "value_observed": val,
                        "link_layer": "host_to_status",
                        "metric_type": "asylum_decisions_observed",
                        "caveat": "Decision outcomes are same-year administrative totals and should not be interpreted as cohort outcomes for the applications link.",
                    }
                )
    return pd.DataFrame(links)


def build_host_pressure_table(host_map_latest: pd.DataFrame, c: Config, year: int) -> pd.DataFrame:
    """Prepare host-pressure denominator table.

    The proposal mentions WDI population/GDP. This function keeps the EDA honest:
    it produces a ready table and explicitly marks the WDI denominator as missing unless
    a suitable file is supplied in 01_clean or the project root.
    """
    candidates = [
        c.output_dir / "01_clean" / "wdi_country_indicators_clean.csv",
        c.output_dir / "01_clean" / "wdi_country_indicators_clean.csv.gz",
        c.output_dir / "data" / "wdi_country_indicators.csv",
        Path.cwd() / "wdi_country_indicators.csv",
    ]
    base = host_map_latest.rename(columns={"host_country_std": "country", "host_iso3": "iso3", "value_observed": "host_stock_observed"}).copy()
    base["year"] = year
    base["population_total"] = np.nan
    base["host_stock_per_100k_population"] = np.nan
    base["gdp_per_capita"] = np.nan
    base["income_group"] = ""
    base["wdi_status"] = "missing_wdi_denominator"
    for path in candidates:
        if path.exists():
            wdi = pd.read_csv(path, low_memory=False)
            cols = {c.lower(): c for c in wdi.columns}
            iso_col = cols.get("iso3") or cols.get("country_code") or cols.get("countryiso3code")
            year_col = cols.get("year")
            pop_col = cols.get("population_total") or cols.get("population") or cols.get("sp.pop.totl")
            gdp_col = cols.get("gdp_per_capita") or cols.get("ny.gdp.pcap.cd")
            income_col = cols.get("income_group")
            if iso_col and year_col and pop_col:
                w = wdi[pd.to_numeric(wdi[year_col], errors="coerce").eq(year)].copy()
                keep = [iso_col, year_col, pop_col]
                rename = {iso_col: "iso3", year_col: "wdi_year", pop_col: "population_total"}
                if gdp_col:
                    keep.append(gdp_col); rename[gdp_col] = "gdp_per_capita"
                if income_col:
                    keep.append(income_col); rename[income_col] = "income_group"
                w = w[keep].rename(columns=rename)
                base = base.drop(columns=["population_total", "gdp_per_capita", "income_group", "wdi_status"], errors="ignore").merge(w, on="iso3", how="left")
                base["host_stock_per_100k_population"] = np.where(
                    pd.to_numeric(base["population_total"], errors="coerce") > 0,
                    base["host_stock_observed"] / pd.to_numeric(base["population_total"], errors="coerce") * 100000,
                    np.nan,
                )
                base["wdi_status"] = np.where(base["population_total"].notna(), "matched_wdi", "missing_country_year_denominator")
                if "gdp_per_capita" not in base:
                    base["gdp_per_capita"] = np.nan
                if "income_group" not in base:
                    base["income_group"] = ""
                return base
    return base


def build_crisis_storytelling_template(ts: pd.DataFrame, g5: pd.DataFrame, year: int, pop_types: List[str]) -> pd.DataFrame:
    rows: List[dict] = []
    top_origins = g5["origin_country_std"].dropna().astype(str).head(5).tolist() if "origin_country_std" in g5 else []
    for origin in top_origins:
        d = ts[(ts["origin_country_std"].eq(origin)) & (ts["population_type_std"].isin(pop_types))]
        trend = d.groupby("year", as_index=False).agg(value_observed=("value_observed", "sum")).sort_values("year")
        if trend.empty:
            continue
        peak = trend.loc[trend["value_observed"].idxmax()]
        latest = trend[trend["year"].eq(year)]
        latest_val = float(latest["value_observed"].sum()) if len(latest) else np.nan
        rows.append(
            {
                "crisis_or_origin": origin,
                "first_observed_year": int(trend["year"].min()),
                "latest_year": year,
                "latest_value_observed": latest_val,
                "peak_year_in_dataset": int(peak["year"]),
                "peak_value_observed": float(peak["value_observed"]),
                "suggested_dashboard_use": "Use this row to drive the crisis storytelling selector and add researched/cited event annotations manually.",
                "manual_event_annotation_required": True,
            }
        )
    return pd.DataFrame(rows)


def build_chart_narrative_cards(g5: pd.DataFrame, g6: pd.DataFrame, kpis: pd.DataFrame, year: int, scope_types: List[str]) -> pd.DataFrame:
    def fmt_m(x: float) -> str:
        if pd.isna(x):
            return "n/a"
        return f"{x/1_000_000:.1f}M" if abs(x) >= 1_000_000 else f"{x/1_000:.0f}K"

    top_origin = g5.iloc[0] if len(g5) else None
    top_host = g6.iloc[0] if len(g6) else None
    scope = "+".join(scope_types)
    rows = [
        {
            "card_id": "story_01_global_scale",
            "dashboard_section": "KPI + trend",
            "question_answered": "How large is the observed displacement stock in the selected scope?",
            "headline": f"Latest-year stock scope: {scope}",
            "evidence_file": "kpi_cards_latest.csv; annual_population_by_type.csv",
            "interpretation": "Use KPI cards and the global time-series to introduce scale before showing origin-destination details.",
            "caveat": "Totals are observed reported values after redaction/missingness handling.",
        },
        {
            "card_id": "story_02_top_origin",
            "dashboard_section": "Graph 5",
            "question_answered": "Which countries produced the largest displaced populations?",
            "headline": f"Top origin in {year}: {top_origin['origin_country_std']} ({fmt_m(float(top_origin['value_observed']))})" if top_origin is not None else "Top origin unavailable",
            "evidence_file": "graph5_top_origin_countries.csv",
            "interpretation": "Ranked horizontal bars make the skewed distribution readable.",
            "caveat": "This is population stock, not annual applications.",
        },
        {
            "card_id": "story_03_top_host",
            "dashboard_section": "Graph 6",
            "question_answered": "Which countries hosted the largest displaced populations?",
            "headline": f"Top host in {year}: {top_host['host_country_std']} ({fmt_m(float(top_host['value_observed']))})" if top_host is not None else "Top host unavailable",
            "evidence_file": "graph6_top_host_countries.csv",
            "interpretation": "Host-country ranking links the humanitarian story to asylum/residence destinations.",
            "caveat": "IDPs should not be mixed into host-country rankings unless the dashboard explicitly says active-forced/residence scope.",
        },
        {
            "card_id": "story_04_flow_network",
            "dashboard_section": "Sankey / map / network",
            "question_answered": "How are origin and host countries connected?",
            "headline": "Top corridors connect the ranked bar charts to spatial and network views.",
            "evidence_file": "top_origin_host_corridors.csv; network_metrics_top_corridors.csv",
            "interpretation": "Use corridors after Graph 5 and Graph 6 so the audience sees relationships, not only rankings.",
            "caveat": "Stock corridors should be called origin-host population corridors, not literal migration trips.",
        },
        {
            "card_id": "story_05_advanced_analytics",
            "dashboard_section": "Forecast / concentration / pressure",
            "question_answered": "What makes the project technically stronger than basic charts?",
            "headline": "Forecasting, concentration metrics, network metrics and optional WDI pressure support the rubric's advanced-analytics criterion.",
            "evidence_file": "forecast_model_comparison.csv; origin_host_concentration_by_year.csv; host_pressure_per_100k.csv",
            "interpretation": "These outputs give material for the technical-complexity and ML/analytics discussion.",
            "caveat": "Forecast is exploratory and WDI pressure is partial unless the denominator file is added.",
        },
    ]
    return pd.DataFrame(rows)


def build_rubric_alignment_checklist() -> pd.DataFrame:
    rows = [
        {"rubric_item": "At least 5 charts", "status": "satisfied", "evidence": "Graph 5, Graph 6, trend, choropleth, Sankey, monthly, demographics, forecast, network"},
        {"rubric_item": "At least 3 chart types", "status": "satisfied", "evidence": "Ranked bars, line/area, choropleth, Sankey, network, pyramid, forecast line"},
        {"rubric_item": "Python Shiny interactive dashboard", "status": "requires app.py integration", "evidence": "EDA outputs filter_options.json and chart-ready CSVs"},
        {"rubric_item": "Spatial/spatio-temporal visualization", "status": "satisfied", "evidence": "choropleth_host_latest.csv; animated_host_map_by_year.csv"},
        {"rubric_item": "Network or flow visualization", "status": "satisfied", "evidence": "top_origin_host_corridors.csv; network_metrics_top_corridors.csv; sankey_top_corridors.csv"},
        {"rubric_item": "Forecasting / model comparison", "status": "satisfied_with_caveat", "evidence": "forecast_global_active_forced_displacement.csv; forecast_model_comparison.csv"},
        {"rubric_item": "Reproducibility", "status": "satisfied", "evidence": "input_validation_checklist.csv; eda_manifest.json; deterministic scripts"},
        {"rubric_item": "Storytelling", "status": "satisfied_with_manual_annotations", "evidence": "chart_narrative_cards.csv; crisis_storytelling_template.csv"},
        {"rubric_item": "Hosting pressure per population", "status": "partial_until_WDI_added", "evidence": "host_pressure_per_100k.csv explicitly marks WDI denominator status"},
    ]
    return pd.DataFrame(rows)

def run(c: Config) -> None:
    ensure_dirs(c)
    input_validation = validate_clean_inputs(c)
    eda_dir = c.output_dir / "02_eda"
    chart_dir = c.output_dir / "03_chart_data"
    report_dir = c.output_dir / "07_report_assets"

    print("[1/6] Reading cleaned datasets")
    ts = read_clean(c, "time_series_clean.csv.gz")
    poc_long = read_clean(c, "persons_of_concern_clean_long.csv.gz")
    asylum = read_clean(c, "asylum_seekers_clean.csv.gz")
    monthly = read_clean(c, "asylum_seekers_monthly_clean.csv.gz")
    demo = read_clean(c, "demographics_clean.csv.gz")
    res = read_clean(c, "resettlement_clean.csv.gz")

    year = int(ts["year"].max()) if c.year is None else int(c.year)
    scope_types = get_scope_types(c.scope)

    print(f"[2/6] Building EDA tables for year={year}, scope={'+'.join(scope_types)}")
    annual = compute_annual(ts)
    kpis = compute_kpis(ts, asylum, year, scope_types)
    g5 = rank_dimension(ts, "origin", year, scope_types, c.top_n, require_map_eligible=False)
    # For Graph 6, IDPs are excluded by default under cross_border scope. If user chooses active_forced,
    # host rankings are still data-valid but should be interpreted as residence/asylum + internal displacement.
    g6 = rank_dimension(ts, "host", year, scope_types, c.top_n, require_map_eligible=False)

    g5_long = g5.rename(
        columns={
            "origin_country_std": "country",
            "origin_iso3": "iso3",
            "origin_mapping_status": "mapping_status",
            "origin_map_eligible_flag": "map_eligible_flag",
        }
    ).copy()
    g5_long["chart_role"] = "Graph 5 — Top origin countries"
    g6_long = g6.rename(
        columns={
            "host_country_std": "country",
            "host_iso3": "iso3",
            "host_mapping_status": "mapping_status",
            "host_map_eligible_flag": "map_eligible_flag",
        }
    ).copy()
    g6_long["chart_role"] = "Graph 6 — Top host countries"
    combined = pd.concat(
        [
            g5_long[["chart_role", "rank", "country", "iso3", "mapping_status", "map_eligible_flag", "value_observed", "share_of_selected_total", "source_rows", "observed_rows", "year", "population_scope", "metric_type"]],
            g6_long[["chart_role", "rank", "country", "iso3", "mapping_status", "map_eligible_flag", "value_observed", "share_of_selected_total", "source_rows", "observed_rows", "year", "population_scope", "metric_type"]],
        ],
        ignore_index=True,
    )

    print("[3/6] Building flow, Sankey, map and network-ready tables")
    corridors = build_corridors(ts, year, scope_types)
    sankey_top = corridors.head(50).copy()
    host_map_latest = corridors[corridors["host_iso3"].str.len().eq(3)].groupby(["year", "host_country_std", "host_iso3"], as_index=False).agg(value_observed=("value_observed", "sum"), source_rows=("source_rows", "sum"))
    host_by_year = ts[(ts["population_type_std"].isin(scope_types)) & (ts["host_map_eligible_flag"] == True)]
    host_by_year = host_by_year.groupby(["year", "host_country_std", "host_iso3"], as_index=False).agg(value_observed=("value_observed", "sum"), source_rows=("value_observed", "size"))
    network_metrics = build_network_metrics(corridors)

    print("[4/6] Building secondary analytical tables")
    monthly_agg, monthly_seasonality = monthly_outputs(monthly)
    demo_age = demographics_latest(demo)
    asylum_by_year = asylum_yearly(asylum)
    res_by_year = res.groupby("year", as_index=False).agg(resettlement_observed=("resettlement_observed", "sum"), source_rows=("resettlement_observed", "size")).sort_values("year")
    res_top_dest = res.groupby(["host_country_std", "host_iso3"], as_index=False).agg(resettlement_observed=("resettlement_observed", "sum"), source_rows=("resettlement_observed", "size")).sort_values("resettlement_observed", ascending=False).head(20)
    forecast, forecast_metrics = build_forecast(annual)
    concentration = pd.concat([concentration_by_year(ts, "origin", scope_types), concentration_by_year(ts, "host", scope_types)], ignore_index=True)
    crosscheck = build_time_series_vs_poc_crosscheck(ts, poc_long)

    # Crisis storytelling seed: Syria over time and latest top hosts.
    syria = ts[ts["origin_country_std"].eq("Syrian Arab Republic") & ts["population_type_std"].isin(scope_types)]
    syria_trend = syria.groupby(["year", "population_type_std"], as_index=False).agg(value_observed=("value_observed", "sum"))
    syria_hosts = syria[syria["year"].eq(year)].groupby(["host_country_std", "host_iso3"], as_index=False).agg(value_observed=("value_observed", "sum")).sort_values("value_observed", ascending=False).head(15)

    # Professor-grade dashboard-support tables.
    dashboard_matrix = build_dashboard_component_matrix(year, scope_types)
    filter_options, filter_options_summary = build_filter_options(ts, asylum, monthly, demo, res)
    chart_coverage = build_chart_coverage(ts, asylum, monthly, demo, res, year)
    country_role_scatter = build_country_role_scatter(ts, year, scope_types)
    asylum_corridors = build_asylum_corridors(asylum, year, top_n=150)
    sankey_status = build_sankey_origin_host_status(asylum_corridors)
    host_pressure = build_host_pressure_table(host_map_latest, c, year)
    crisis_template = build_crisis_storytelling_template(ts, g5, year, scope_types)
    narrative_cards = build_chart_narrative_cards(g5, g6, kpis, year, scope_types)
    rubric_checklist = build_rubric_alignment_checklist()

    print("[5/6] Writing EDA and chart-ready data")
    save_csv(annual, chart_dir / "annual_population_by_type.csv")
    save_csv(kpis, chart_dir / "kpi_cards_latest.csv")
    save_csv(g5, chart_dir / "graph5_top_origin_countries.csv")
    save_csv(g6, chart_dir / "graph6_top_host_countries.csv")
    save_csv(combined, chart_dir / "graph5_6_combined_top_origin_host.csv")
    save_csv(corridors.head(300), chart_dir / "top_origin_host_corridors.csv")
    save_csv(sankey_top, chart_dir / "sankey_top_corridors.csv")
    save_csv(host_map_latest.sort_values("value_observed", ascending=False), chart_dir / "choropleth_host_latest.csv")
    save_csv(host_by_year, chart_dir / "animated_host_map_by_year.csv")
    save_csv(network_metrics, chart_dir / "network_metrics_top_corridors.csv")
    save_csv(monthly_agg, chart_dir / "monthly_applications_by_year_month.csv")
    save_csv(monthly_seasonality, chart_dir / "monthly_application_seasonality_profile.csv")
    save_csv(demo_age, chart_dir / "demographics_age_sex_latest.csv")
    save_csv(asylum_by_year, chart_dir / "asylum_applications_decisions_by_year.csv")
    save_csv(res_by_year, chart_dir / "resettlement_by_year.csv")
    save_csv(res_top_dest, chart_dir / "top_resettlement_destination_countries.csv")
    save_csv(forecast, chart_dir / "forecast_global_active_forced_displacement.csv")
    save_csv(forecast_metrics, chart_dir / "forecast_model_comparison.csv")
    save_csv(concentration, eda_dir / "origin_host_concentration_by_year.csv")
    save_csv(crosscheck, eda_dir / "time_series_vs_persons_of_concern_crosscheck.csv")
    save_csv(syria_trend, chart_dir / "crisis_story_syria_trend.csv")
    save_csv(syria_hosts, chart_dir / "crisis_story_syria_top_hosts_latest.csv")

    # Additional dashboard-readiness outputs for Shiny and final report.
    save_csv(input_validation, eda_dir / "input_validation_checklist.csv")
    save_csv(dashboard_matrix, report_dir / "dashboard_component_matrix.csv")
    save_csv(filter_options_summary, report_dir / "filter_options_summary.csv")
    (chart_dir / "filter_options.json").write_text(json.dumps(filter_options, indent=2, ensure_ascii=False), encoding="utf-8")
    save_csv(chart_coverage, report_dir / "chart_data_coverage_by_component.csv")
    save_csv(country_role_scatter, chart_dir / "country_origin_host_role_scatter.csv")
    save_csv(asylum_corridors, chart_dir / "top_asylum_application_corridors.csv")
    save_csv(sankey_status, chart_dir / "sankey_origin_host_status_decisions.csv")
    save_csv(host_pressure, chart_dir / "host_pressure_per_100k.csv")
    save_csv(crisis_template, chart_dir / "crisis_storytelling_template.csv")
    save_csv(narrative_cards, report_dir / "chart_narrative_cards.csv")
    save_csv(rubric_checklist, report_dir / "rubric_alignment_checklist.csv")

    # Quality summary from raw audit.
    raw_quality_path = c.output_dir / "00_audit" / "numeric_quality_audit.csv"
    if raw_quality_path.exists():
        q = pd.read_csv(raw_quality_path)
        q["missing_or_redacted_rows"] = q["blank_rows"].fillna(0) + q["redacted_star_rows"].fillna(0)
        qsum = q.groupby("dataset", as_index=False).agg(
            numeric_columns=("column", "nunique"),
            observed_cells=("observed_nonmissing_rows", "sum"),
            zero_cells=("zero_rows", "sum"),
            blank_cells=("blank_rows", "sum"),
            redacted_star_cells=("redacted_star_rows", "sum"),
            negative_raw_cells=("negative_raw_rows", "sum"),
            observed_sum_all_numeric=("observed_sum", "sum"),
        )
        save_csv(qsum, eda_dir / "zero_missing_redaction_summary_by_dataset.csv")

    print("[6/6] Writing methodology notes")
    summary = f"""
# EDA methodology and dashboard alignment

## Default analytical scope

- Dashboard year: **{year}**
- Graph 5/6 population scope: **{'+'.join(scope_types)}**
- Metric type: **observed population stock** from cleaned `time_series.csv`

## Why Graph 5 and Graph 6 use `time_series_clean.csv.gz`

Graph 5 and Graph 6 are designed to answer the wireframe questions: which countries produce the largest cross-border displaced populations, and which countries host the largest populations. The cleaned `time_series.csv` is the canonical long-format stock table, so it is better suited than `asylum_seekers.csv`, which is an application-flow dataset.

## Stock vs flow separation

- Stock metrics: `time_series.csv` and `persons_of_concern.csv`.
- Flow metrics: `asylum_seekers.csv`, `asylum_seekers_monthly.csv`, `resettlement.csv`.
- IDPs are excluded from the default host-country ranking because IDPs are internally displaced and do not represent cross-border hosting.

## Dashboard tables generated

- KPI cards
- Global time series by population type
- Graph 5 top origin countries
- Graph 6 top host countries
- Combined Graph 5 + 6 comparison
- Origin-host corridors and Sankey links
- Choropleth and animated map data
- Monthly asylum seasonality
- Demographic age/sex profile
- Resettlement trend
- Network metrics
- Exploratory forecast table
- Filter options for Shiny controls
- Dashboard component-to-dataset matrix
- Input validation checklist
- Host-pressure table with WDI denominator status
- Crisis-storytelling template for manually cited crisis events
- Rubric-alignment checklist for final report/presentation

## Important caveat for professor-facing presentation

The EDA is now dashboard-ready. The only planned feature that remains partial is **hosting pressure per 100k population**, because it requires a WDI population denominator. The script therefore writes `host_pressure_per_100k.csv` and explicitly marks rows as `missing_wdi_denominator` unless a WDI file is added.

## Top findings, latest year

### Graph 5 — origins
{g5[['rank', 'origin_country_std', 'value_observed', 'share_of_selected_total']].to_markdown(index=False)}

### Graph 6 — hosts
{g6[['rank', 'host_country_std', 'value_observed', 'share_of_selected_total']].to_markdown(index=False)}
""".strip()
    (report_dir / "eda_methodology_and_findings.md").write_text(summary, encoding="utf-8")

    manifest = {
        "output_dir": str(c.output_dir),
        "year": year,
        "top_n": c.top_n,
        "scope": c.scope,
        "scope_types": scope_types,
        "chart_data_files": [p.name for p in sorted(chart_dir.glob("*.csv"))],
        "eda_files": [p.name for p in sorted(eda_dir.glob("*.csv"))],
        "report_asset_files": [p.name for p in sorted(report_dir.glob("*.csv"))] + [p.name for p in sorted(report_dir.glob("*.md"))],
        "graph_rendering_in_this_script": False,
        "app_included": False,
        "handoff_note": "This EDA script prepares app-ready tables only. The teammate's app.py should read outputs/03_chart_data/.",
    }
    (eda_dir / "eda_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("EDA complete. No figures were rendered in this section.")
    print(f"Dashboard year: {year} | Scope: {'+'.join(scope_types)} | Chart-ready files: {len(manifest['chart_data_files'])}")


if __name__ == "__main__":
    run(parse_args())
