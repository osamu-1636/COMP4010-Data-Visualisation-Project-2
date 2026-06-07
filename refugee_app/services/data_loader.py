"""Data loading layer.

The app never reads raw UNHCR CSVs. It reads only cleaned and chart-ready outputs
from the preprocessing + EDA pipeline. Parquet is preferred when present; CSV is
used as fallback so the repository remains easy to run on student machines.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .cache import read_table_cached


@dataclass(frozen=True)
class DataStore:
    root: Path
    outputs: Path
    clean: Path
    chart: Path
    audit: Path
    metadata: dict
    time_series: pd.DataFrame
    annual_population: pd.DataFrame
    monthly_apps: pd.DataFrame
    demographics_age: pd.DataFrame
    resettlement_year: pd.DataFrame
    forecast: pd.DataFrame
    role_scatter: pd.DataFrame
    host_pressure: pd.DataFrame
    quality_gate: pd.DataFrame

    @property
    def year_min(self) -> int:
        return int(self.time_series["year"].min())

    @property
    def year_max(self) -> int:
        return int(self.time_series["year"].max())

    @property
    def origin_choices(self) -> list[str]:
        s = self.time_series.loc[self.time_series["origin_mapping_status"].ne("special_entity"), "origin_country_std"]
        return ["All"] + sorted(s.dropna().astype(str).unique().tolist())

    @property
    def host_choices(self) -> list[str]:
        s = self.time_series.loc[self.time_series["host_mapping_status"].ne("special_entity"), "host_country_std"]
        return ["All"] + sorted(s.dropna().astype(str).unique().tolist())


def _read_first(chart_dir: Path, names: list[str], required: bool = False) -> pd.DataFrame:
    for name in names:
        p = chart_dir / name
        if p.exists():
            return read_table_cached(str(p.resolve()))
    if required:
        raise FileNotFoundError(f"None of these chart data files exist: {names}")
    return pd.DataFrame()


def load_data(app_dir: Path | None = None) -> DataStore:
    root = (app_dir or Path(__file__).resolve().parents[2]).resolve()
    outputs = root / "outputs"
    clean = outputs / "01_clean"
    chart = outputs / "03_chart_data"
    audit = outputs / "00_audit"
    meta_path = chart / "metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    ts_candidates = [chart / "stock.parquet", chart / "stock_timeseries.parquet", clean / "time_series_clean.csv.gz"]
    ts_path = next((p for p in ts_candidates if p.exists()), None)
    if ts_path is None:
        raise FileNotFoundError("Missing stock table. Expected outputs/03_chart_data/stock.parquet or outputs/01_clean/time_series_clean.csv.gz")

    return DataStore(
        root=root,
        outputs=outputs,
        clean=clean,
        chart=chart,
        audit=audit,
        metadata=metadata,
        time_series=read_table_cached(str(ts_path.resolve())),
        annual_population=_read_first(chart, ["trends.parquet", "trends.csv", "annual_population_by_type.csv"]),
        monthly_apps=_read_first(chart, ["monthly_applications_by_year_month.parquet", "monthly_applications_by_year_month.csv"]),
        demographics_age=_read_first(chart, ["demographics_age_sex_latest.parquet", "demographics_age_sex_latest.csv"]),
        resettlement_year=_read_first(chart, ["resettlement_by_year.parquet", "resettlement_by_year.csv"]),
        forecast=_read_first(chart, ["forecast_global_active_forced_displacement.parquet", "forecast_global_active_forced_displacement.csv"]),
        role_scatter=_read_first(chart, ["role_scatter.parquet", "role_scatter.csv", "country_origin_host_role_scatter.csv"]),
        host_pressure=_read_first(chart, ["host_pressure.parquet", "host_pressure.csv", "host_pressure_per_100k.csv"]),
        quality_gate=read_table_cached(str((audit / "quality_gate_summary.csv").resolve())) if (audit / "quality_gate_summary.csv").exists() else pd.DataFrame(),
    )
