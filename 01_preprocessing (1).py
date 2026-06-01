#!/usr/bin/env python3
"""
SECTION 1 — PREPROCESSING
Global Refugee Movement Dashboard, Group 11

Purpose
-------
Build a reproducible, audit-friendly cleaned data layer from six UNHCR-style CSV files.
The script is intentionally conservative: it never treats reported zero as missing, and it
keeps redacted/blank values as missing with explicit flags.

Expected input files
--------------------
- resettlement.csv
- asylum_seekers_monthly.csv
- demographics.csv
- asylum_seekers.csv
- persons_of_concern.csv
- time_series.csv

Main outputs
------------
outputs/00_audit/
outputs/01_clean/
outputs/07_report_assets/preprocessing_methodology.md

Run
---
python 01_preprocessing.py --input-dir . --output-dir outputs
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

try:
    import pycountry
except Exception:  # pragma: no cover
    pycountry = None

RAW_FILES: Dict[str, str] = {
    "resettlement": "resettlement.csv",
    "asylum_seekers_monthly": "asylum_seekers_monthly.csv",
    "demographics": "demographics.csv",
    "asylum_seekers": "asylum_seekers.csv",
    "persons_of_concern": "persons_of_concern.csv",
    "time_series": "time_series.csv",
}

HOST_COL = "Country / territory of asylum/residence"
ORIGIN_COL = "Origin"
YEAR_COL = "Year"

POC_WIDE_TYPE_MAP = {
    "Refugees (incl. refugee-like situations)": "Refugees",
    "Asylum-seekers (pending cases)": "Asylum-seekers",
    "Returned refugees": "Returned refugees",
    "Internally displaced persons (IDPs)": "IDPs",
    "Returned IDPs": "Returned IDPs",
    "Stateless persons": "Stateless persons",
    "Others of concern": "Others of concern",
}

TIME_TYPE_MAP = {
    "Refugees (incl. refugee-like situations)": "Refugees",
    "Refugees": "Refugees",
    "Asylum-seekers": "Asylum-seekers",
    "Asylum-seekers (pending cases)": "Asylum-seekers",
    "Internally displaced persons": "IDPs",
    "Internally displaced persons (IDPs)": "IDPs",
    "IDPs": "IDPs",
    "Returnees": "Returned refugees",
    "Returned refugees": "Returned refugees",
    "Returned IDPs": "Returned IDPs",
    "Stateless": "Stateless persons",
    "Stateless persons": "Stateless persons",
    "Others of concern": "Others of concern",
}

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

# Manual UNHCR/historical harmonisation. ISO values beginning with X_ or composite labels
# are deliberately not map-ready. This avoids falsely plotting non-current entities.
COUNTRY_ALIASES: Dict[str, Tuple[str, str, str, bool]] = {
    "": ("Missing", "X_MISSING", "missing", False),
    "Various/Unknown": ("Various/Unknown", "X_UNK", "special_entity", False),
    "Various/unknown": ("Various/Unknown", "X_UNK", "special_entity", False),
    "Various": ("Various/Unknown", "X_UNK", "special_entity", False),
    "Unknown": ("Various/Unknown", "X_UNK", "special_entity", False),
    "Stateless": ("Stateless", "X_STAT", "special_entity", False),
    "Tibetan": ("Tibetan", "X_TIB", "special_entity", False),
    "Serbia and Kosovo": ("Serbia and Kosovo (historical UN label)", "SRB_XKX", "historical_or_composite", False),
    "Serbia and Kosovo: S/RES/1244 (1999)": ("Serbia and Kosovo (historical UN label)", "SRB_XKX", "historical_or_composite", False),
    "Serbia and Kosovo (S/RES/1244 (1999))": ("Serbia and Kosovo (historical UN label)", "SRB_XKX", "historical_or_composite", False),
    "Kosovo (S/RES/1244 (1999))": ("Kosovo", "XKX", "manual_iso", False),
    "Kosovo": ("Kosovo", "XKX", "manual_iso", False),
    "Central African Rep.": ("Central African Republic", "CAF", "manual_iso", True),
    "Rep. of Moldova": ("Moldova", "MDA", "manual_iso", True),
    "Moldova, Republic of": ("Moldova", "MDA", "manual_iso", True),
    "Republic of Moldova": ("Moldova", "MDA", "manual_iso", True),
    "The former Yugoslav Rep. of Macedonia": ("North Macedonia", "MKD", "manual_iso", True),
    "The former Yugoslav Republic of Macedonia": ("North Macedonia", "MKD", "manual_iso", True),
    "North Macedonia": ("North Macedonia", "MKD", "manual_iso", True),
    "Dominican Rep.": ("Dominican Republic", "DOM", "manual_iso", True),
    "USA (INS/DHS)": ("United States", "USA", "manual_iso", True),
    "USA (EOIR)": ("United States", "USA", "manual_iso", True),
    "United States of America": ("United States", "USA", "manual_iso", True),
    "United States": ("United States", "USA", "manual_iso", True),
    "United Kingdom of Great Britain and Northern Ireland": ("United Kingdom", "GBR", "manual_iso", True),
    "United Kingdom": ("United Kingdom", "GBR", "manual_iso", True),
    "Holy See (the)": ("Holy See", "VAT", "manual_iso", True),
    "Holy See": ("Holy See", "VAT", "manual_iso", True),
    "Wallis and Futuna Islands": ("Wallis and Futuna", "WLF", "manual_iso", True),
    "China, Hong Kong SAR": ("Hong Kong", "HKG", "manual_iso", True),
    "Hong Kong SAR, China": ("Hong Kong", "HKG", "manual_iso", True),
    "Hong Kong (Special Administrative Region of China)": ("Hong Kong", "HKG", "manual_iso", True),
    "China, Macao SAR": ("Macao", "MAC", "manual_iso", True),
    "Macau (Special Administrative Region of China)": ("Macao", "MAC", "manual_iso", True),
    "Macao": ("Macao", "MAC", "manual_iso", True),
    "Czech Rep.": ("Czechia", "CZE", "manual_iso", True),
    "Czech Republic": ("Czechia", "CZE", "manual_iso", True),
    "Iran (Islamic Rep. of)": ("Iran", "IRN", "manual_iso", True),
    "Islamic Republic of Iran": ("Iran", "IRN", "manual_iso", True),
    "Syrian Arab Rep.": ("Syrian Arab Republic", "SYR", "manual_iso", True),
    "Syrian Arab Republic": ("Syrian Arab Republic", "SYR", "manual_iso", True),
    "Venezuela (Bolivarian Republic of)": ("Venezuela", "VEN", "manual_iso", True),
    "Bolivia (Plurinational State of)": ("Bolivia", "BOL", "manual_iso", True),
    "United Rep. of Tanzania": ("Tanzania", "TZA", "manual_iso", True),
    "United Republic of Tanzania": ("Tanzania", "TZA", "manual_iso", True),
    "Rep. of Korea": ("South Korea", "KOR", "manual_iso", True),
    "Republic of Korea": ("South Korea", "KOR", "manual_iso", True),
    "Dem. People's Rep. of Korea": ("North Korea", "PRK", "manual_iso", True),
    "Democratic People's Republic of Korea": ("North Korea", "PRK", "manual_iso", True),
    "Dem. Rep. of the Congo": ("Democratic Republic of the Congo", "COD", "manual_iso", True),
    "Democratic Republic of the Congo": ("Democratic Republic of the Congo", "COD", "manual_iso", True),
    "Congo": ("Republic of the Congo", "COG", "manual_iso", True),
    "Republic of the Congo": ("Republic of the Congo", "COG", "manual_iso", True),
    "Russian Federation": ("Russia", "RUS", "manual_iso", True),
    "Lao People's Dem. Rep.": ("Laos", "LAO", "manual_iso", True),
    "Lao People's Democratic Republic": ("Laos", "LAO", "manual_iso", True),
    "Viet Nam": ("Vietnam", "VNM", "manual_iso", True),
    "Côte d'Ivoire": ("Côte d'Ivoire", "CIV", "manual_iso", True),
    "Cote d'Ivoire": ("Côte d'Ivoire", "CIV", "manual_iso", True),
    "Palestinian": ("State of Palestine", "PSE", "manual_iso", True),
    "State of Palestine": ("State of Palestine", "PSE", "manual_iso", True),
    "Türkiye": ("Turkey", "TUR", "manual_iso", True),
    "Republic of Türkiye": ("Turkey", "TUR", "manual_iso", True),
    "Turkey": ("Turkey", "TUR", "manual_iso", True),
    "Swaziland": ("Eswatini", "SWZ", "manual_iso", True),
    "Cabo Verde": ("Cabo Verde", "CPV", "manual_iso", True),
    "Micronesia (Federated States of)": ("Micronesia", "FSM", "manual_iso", True),
    "Federated States of Micronesia": ("Micronesia", "FSM", "manual_iso", True),
    "Brunei Darussalam": ("Brunei", "BRN", "manual_iso", True),
    "Netherlands (Kingdom of the)": ("Netherlands", "NLD", "manual_iso", True),
    "Netherlands Antilles": ("Netherlands Antilles", "ANT", "historical_or_composite", False),
    "Curaçao": ("Curaçao", "CUW", "manual_iso", True),
    "Curacao": ("Curaçao", "CUW", "manual_iso", True),
    "Sint Maarten (Dutch part)": ("Sint Maarten", "SXM", "manual_iso", True),
    "Saint Martin (French part)": ("Saint Martin", "MAF", "manual_iso", True),
    "Bonaire, Sint Eustatius and Saba": ("Bonaire, Sint Eustatius and Saba", "BES", "manual_iso", True),
    "British Virgin Islands": ("British Virgin Islands", "VGB", "manual_iso", True),
    "Cayman Islands": ("Cayman Islands", "CYM", "manual_iso", True),
    "French Guiana": ("French Guiana", "GUF", "manual_iso", True),
    "Guadeloupe": ("Guadeloupe", "GLP", "manual_iso", True),
    "Martinique": ("Martinique", "MTQ", "manual_iso", True),
    "Réunion": ("Réunion", "REU", "manual_iso", True),
    "Reunion": ("Réunion", "REU", "manual_iso", True),
    "Western Sahara Territory": ("Western Sahara", "ESH", "manual_iso", True),
}


@dataclass(frozen=True)
class Config:
    input_dir: Path
    output_dir: Path
    write_full_clean: bool = True


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Preprocess six UNHCR datasets for the refugee dashboard.")
    parser.add_argument("--input-dir", default=".", help="Folder containing the six raw CSV files.")
    parser.add_argument("--output-dir", default="outputs", help="Folder where cleaned outputs will be written.")
    parser.add_argument("--no-full-clean", action="store_true", help="Skip wide clean file exports if needed for speed.")
    args = parser.parse_args()
    return Config(Path(args.input_dir).resolve(), Path(args.output_dir).resolve(), write_full_clean=not args.no_full_clean)


def ensure_dirs(c: Config) -> None:
    for sub in ["00_audit", "01_clean", "07_report_assets"]:
        (c.output_dir / sub).mkdir(parents=True, exist_ok=True)


def snake(name: str) -> str:
    text = str(name).strip().replace("/", "_")
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_").lower()
    return text


def raw_path(c: Config, dataset: str) -> Path:
    candidates = [
        c.input_dir / RAW_FILES[dataset],
        c.input_dir / "data" / "raw" / RAW_FILES[dataset],
        Path.cwd() / RAW_FILES[dataset],
        Path.cwd() / "data" / "raw" / RAW_FILES[dataset],
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Missing {RAW_FILES[dataset]}. Checked: {', '.join(str(x) for x in candidates)}")


def read_raw(c: Config, dataset: str) -> pd.DataFrame:
    # keep_default_na=False is essential: it preserves literal 'NA' procedure codes.
    return pd.read_csv(raw_path(c, dataset), dtype=str, keep_default_na=False, low_memory=False)


def save_csv(df: pd.DataFrame, path: Path, gzip: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gzip or str(path).endswith(".gz"):
        # compresslevel=1 keeps files small enough while avoiding slow maximum-compression exports.
        df.to_csv(path, index=False, na_rep="", compression={"method": "gzip", "compresslevel": 1})
    else:
        df.to_csv(path, index=False, na_rep="")


def clean_numeric_series(s: pd.Series) -> pd.DataFrame:
    raw = s.astype(str).str.strip()
    blank = raw.eq("") | raw.str.lower().isin(["nan", "none", "null", "n/a"])
    redacted = raw.eq("*")
    cleaned = raw.str.replace(",", "", regex=False)
    numeric = pd.to_numeric(cleaned.mask(blank | redacted), errors="coerce")
    non_numeric = (~blank & ~redacted & numeric.isna())
    negative = numeric < 0
    numeric = numeric.mask(negative)
    return pd.DataFrame(
        {
            "observed": numeric,
            "is_blank": blank,
            "is_redacted": redacted,
            "is_zero": numeric.eq(0).fillna(False),
            "is_negative_raw": negative.fillna(False),
            "is_non_numeric_raw": non_numeric.fillna(False),
        }
    )


def likely_numeric_columns(df: pd.DataFrame) -> List[str]:
    exclude = {HOST_COL, ORIGIN_COL, "Location Name", "Month", "Population type", "RSD procedure type / level"}
    numeric_cols: List[str] = []
    for col in df.columns:
        if col in exclude:
            continue
        if col == YEAR_COL:
            numeric_cols.append(col)
            continue
        raw = df[col].astype(str).str.strip()
        sample = raw.mask(raw.isin(["", "*"])).dropna()
        if len(sample) == 0:
            numeric_cols.append(col)
            continue
        numeric_fraction = pd.to_numeric(sample.str.replace(",", "", regex=False), errors="coerce").notna().mean()
        if numeric_fraction >= 0.95:
            numeric_cols.append(col)
    return numeric_cols


def audit_numeric(df: pd.DataFrame, dataset: str, col: str) -> dict:
    clean = clean_numeric_series(df[col])
    obs = clean["observed"]
    return {
        "dataset": dataset,
        "column": col,
        "rows": len(df),
        "observed_nonmissing_rows": int(obs.notna().sum()),
        "blank_rows": int(clean["is_blank"].sum()),
        "redacted_star_rows": int(clean["is_redacted"].sum()),
        "zero_rows": int(clean["is_zero"].sum()),
        "negative_raw_rows": int(clean["is_negative_raw"].sum()),
        "non_numeric_raw_rows": int(clean["is_non_numeric_raw"].sum()),
        "observed_sum": float(obs.sum(skipna=True)),
        "observed_min": float(obs.min(skipna=True)) if obs.notna().any() else np.nan,
        "observed_max": float(obs.max(skipna=True)) if obs.notna().any() else np.nan,
    }


@lru_cache(maxsize=None)
def country_lookup(name_raw: str) -> Tuple[str, str, str, bool]:
    name = str(name_raw).strip()
    if name in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[name]
    if not name:
        return COUNTRY_ALIASES[""]
    if pycountry is not None:
        try:
            country = pycountry.countries.lookup(name)
            std = getattr(country, "common_name", None) or country.name
            return (std, country.alpha_3, "pycountry_exact_or_alias", True)
        except Exception:
            pass
        # Use fuzzy matching only where it is safe. This keeps special labels from being forced onto wrong countries.
        low = name.lower()
        if len(name) >= 4 and not any(token in low for token in ["unknown", "various", "stateless"]):
            try:
                candidates = pycountry.countries.search_fuzzy(name)
                if candidates:
                    country = candidates[0]
                    std = getattr(country, "common_name", None) or country.name
                    return (std, country.alpha_3, "pycountry_fuzzy", True)
            except Exception:
                pass
    return (name, "UNMAPPED", "unmapped", False)


def enrich_country(df: pd.DataFrame, raw_col: str, prefix: str) -> pd.DataFrame:
    # Map unique country labels once, then broadcast. This is much faster than calling pycountry per row.
    raw = df[raw_col].fillna("").astype(str)
    unique_values = pd.Index(raw.unique())
    lookup = {value: country_lookup(value) for value in unique_values}
    mapped = raw.map(lookup)
    mapping = pd.DataFrame(
        mapped.tolist(),
        columns=[
            f"{prefix}_country_std",
            f"{prefix}_iso3",
            f"{prefix}_mapping_status",
            f"{prefix}_map_eligible_flag",
        ],
        index=df.index,
    )
    return pd.concat([df.reset_index(drop=True), mapping.reset_index(drop=True)], axis=1)


def add_numeric_flags(df: pd.DataFrame, raw_col: str, out_col: str) -> pd.DataFrame:
    cv = clean_numeric_series(df[raw_col])
    df[out_col] = cv["observed"]
    for flag in ["is_blank", "is_redacted", "is_zero", "is_negative_raw", "is_non_numeric_raw"]:
        df[f"{out_col}_{flag}"] = cv[flag]
    return df


def run_raw_audit(c: Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    inventory: List[dict] = []
    numeric_audit: List[dict] = []
    for dataset in RAW_FILES:
        df = read_raw(c, dataset)
        years = pd.to_numeric(df[YEAR_COL], errors="coerce") if YEAR_COL in df.columns else pd.Series(dtype=float)
        inventory.append(
            {
                "dataset": dataset,
                "file": RAW_FILES[dataset],
                "rows": len(df),
                "columns": len(df.columns),
                "year_min": int(years.min()) if years.notna().any() else np.nan,
                "year_max": int(years.max()) if years.notna().any() else np.nan,
                "raw_columns": " | ".join(df.columns),
            }
        )
        for col in likely_numeric_columns(df):
            numeric_audit.append(audit_numeric(df, dataset, col))
    inv = pd.DataFrame(inventory)
    audit = pd.DataFrame(numeric_audit)
    save_csv(inv, c.output_dir / "00_audit" / "dataset_inventory.csv")
    save_csv(audit, c.output_dir / "00_audit" / "numeric_quality_audit.csv")
    return inv, audit


def clean_resettlement(c: Config) -> pd.DataFrame:
    df = read_raw(c, "resettlement").rename(
        columns={HOST_COL: "host_country_raw", ORIGIN_COL: "origin_country_raw", YEAR_COL: "year", "Value": "value_raw"}
    )
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = add_numeric_flags(df, "value_raw", "resettlement_observed")
    df = enrich_country(df, "host_country_raw", "host")
    df = enrich_country(df, "origin_country_raw", "origin")
    df["dataset"] = "resettlement"
    df["metric_family"] = "durable_solution_flow"
    return df


def clean_asylum_seekers_monthly(c: Config) -> pd.DataFrame:
    df = read_raw(c, "asylum_seekers_monthly").rename(
        columns={HOST_COL: "host_country_raw", ORIGIN_COL: "origin_country_raw", YEAR_COL: "year", "Month": "month", "Value": "value_raw"}
    )
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month_num"] = df["month"].astype(str).str.strip().str.lower().map(MONTH_MAP).astype("Int64")
    df = add_numeric_flags(df, "value_raw", "applications_monthly_observed")
    df = enrich_country(df, "host_country_raw", "host")
    df = enrich_country(df, "origin_country_raw", "origin")
    df["dataset"] = "asylum_seekers_monthly"
    df["metric_family"] = "asylum_application_flow_monthly"
    return df


def clean_asylum_seekers(c: Config) -> pd.DataFrame:
    raw = read_raw(c, "asylum_seekers")
    df = raw.rename(
        columns={
            HOST_COL: "host_country_raw",
            ORIGIN_COL: "origin_country_raw",
            YEAR_COL: "year",
            "RSD procedure type / level": "rsd_procedure_raw",
            "Tota pending start-year": "pending_start_raw",
            "of which UNHCR-assisted(start-year)": "unhcr_assisted_start_raw",
            "Applied during year": "applications_raw",
            "decisions_recognized": "recognized_raw",
            "decisions_other": "other_decisions_raw",
            "Rejected": "rejected_raw",
            "Otherwise closed": "otherwise_closed_raw",
            "Total decisions": "total_decisions_raw",
            "Total pending end-year": "pending_end_raw",
            "of which UNHCR-assisted(end-year)": "unhcr_assisted_end_raw",
        }
    )
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    numeric_map = {
        "pending_start_raw": "pending_start_observed",
        "unhcr_assisted_start_raw": "unhcr_assisted_start_observed",
        "applications_raw": "applications_observed",
        "recognized_raw": "recognized_observed",
        "other_decisions_raw": "other_decisions_observed",
        "rejected_raw": "rejected_observed",
        "otherwise_closed_raw": "otherwise_closed_observed",
        "total_decisions_raw": "total_decisions_observed",
        "pending_end_raw": "pending_end_observed",
        "unhcr_assisted_end_raw": "unhcr_assisted_end_observed",
    }
    for raw_col, out_col in numeric_map.items():
        df = add_numeric_flags(df, raw_col, out_col)

    components = ["recognized_observed", "other_decisions_observed", "rejected_observed", "otherwise_closed_observed"]
    df["total_decisions_recomputed"] = df[components].sum(axis=1, min_count=1)
    # Methodological rule: keep reported total if present; fill only when total is missing.
    df["total_decisions_final"] = df["total_decisions_observed"].fillna(df["total_decisions_recomputed"])
    df["decision_total_mismatch"] = (
        df["total_decisions_observed"].notna()
        & df["total_decisions_recomputed"].notna()
        & (df["total_decisions_observed"].round(6) != df["total_decisions_recomputed"].round(6))
    )
    df["recognition_rate_observed"] = np.where(
        df["total_decisions_final"] > 0, df["recognized_observed"] / df["total_decisions_final"], np.nan
    )

    # Parse RSD procedure. keep_default_na=False has preserved literal 'NA'; we remap it to NEW.
    rsd = df["rsd_procedure_raw"].astype(str).str.strip().str.replace(" / ", "/", regex=False)
    parts = rsd.str.split("/", n=1, expand=True)
    df["rsd_authority"] = parts[0].replace({"": np.nan})
    if parts.shape[1] > 1:
        df["rsd_stage_code"] = parts[1].replace({"NA": "NEW", "": np.nan})
    else:
        df["rsd_stage_code"] = np.nan
    stage_group = {
        "FI": "first_instance",
        "AR": "appeal_review",
        "FA": "appeal_review",
        "RA": "reopened_or_repeat",
        "IN": "new_or_initial",
        "NEW": "new_or_initial",
        "EO": "other_or_ex_officio",
        "JR": "judicial_review",
        "SP": "subsidiary_protection",
        "TP": "temporary_protection",
    }
    df["rsd_stage_group"] = df["rsd_stage_code"].map(stage_group).fillna("other_or_unknown")

    df = enrich_country(df, "host_country_raw", "host")
    df = enrich_country(df, "origin_country_raw", "origin")
    df["dataset"] = "asylum_seekers"
    df["metric_family"] = "asylum_application_and_decision_flow"
    return df


def clean_demographics(c: Config) -> pd.DataFrame:
    df = read_raw(c, "demographics").rename(columns={HOST_COL: "host_country_raw", YEAR_COL: "year", "Location Name": "location_name"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    raw_numeric_cols = [col for col in df.columns if col not in ["year", "host_country_raw", "location_name"]]
    for col in raw_numeric_cols:
        out_col = snake(col) + "_observed"
        df = add_numeric_flags(df, col, out_col)

    def col(name: str) -> pd.Series:
        return df[name] if name in df.columns else pd.Series(np.nan, index=df.index)

    df["female_5_17_combined_observed"] = col("female_5_17_observed").fillna(
        col("female_5_11_observed") + col("female_12_17_observed")
    )
    df["male_5_17_combined_observed"] = col("male_5_17_observed").fillna(
        col("male_5_11_observed") + col("male_12_17_observed")
    )
    df["female_total_final"] = col("f_total_observed")
    df["male_total_final"] = col("m_total_observed")
    df["sex_total_observed"] = df["female_total_final"].fillna(0) + df["male_total_final"].fillna(0)
    df["female_share_observed"] = np.where(df["sex_total_observed"] > 0, df["female_total_final"] / df["sex_total_observed"], np.nan)
    df = enrich_country(df, "host_country_raw", "host")
    df["dataset"] = "demographics"
    df["metric_family"] = "demographics_stock"
    return df


def clean_persons_of_concern(c: Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = read_raw(c, "persons_of_concern").rename(columns={HOST_COL: "host_country_raw", ORIGIN_COL: "origin_country_raw", YEAR_COL: "year"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for col in list(POC_WIDE_TYPE_MAP.keys()) + ["Total Population"]:
        out_col = snake(col) + "_observed"
        df = add_numeric_flags(df, col, out_col)
    df = enrich_country(df, "host_country_raw", "host")
    df = enrich_country(df, "origin_country_raw", "origin")
    df["dataset"] = "persons_of_concern"
    df["metric_family"] = "population_stock_wide"

    long_frames: List[pd.DataFrame] = []
    base_cols = [
        "year",
        "host_country_raw",
        "origin_country_raw",
        "host_country_std",
        "host_iso3",
        "host_mapping_status",
        "host_map_eligible_flag",
        "origin_country_std",
        "origin_iso3",
        "origin_mapping_status",
        "origin_map_eligible_flag",
    ]
    for raw_col, population_type in POC_WIDE_TYPE_MAP.items():
        obs_col = snake(raw_col) + "_observed"
        tmp = df[base_cols + [obs_col, f"{obs_col}_is_blank", f"{obs_col}_is_redacted", f"{obs_col}_is_zero"]].copy()
        tmp = tmp.rename(
            columns={
                obs_col: "value_observed",
                f"{obs_col}_is_blank": "value_is_blank",
                f"{obs_col}_is_redacted": "value_is_redacted",
                f"{obs_col}_is_zero": "value_is_zero",
            }
        )
        tmp["population_type_raw"] = raw_col
        tmp["population_type_std"] = population_type
        tmp["dataset"] = "persons_of_concern_long_from_wide"
        tmp["metric_family"] = "population_stock_long"
        long_frames.append(tmp)
    long = pd.concat(long_frames, ignore_index=True)
    return df, long


def clean_time_series(c: Config) -> pd.DataFrame:
    df = read_raw(c, "time_series").rename(
        columns={HOST_COL: "host_country_raw", ORIGIN_COL: "origin_country_raw", YEAR_COL: "year", "Population type": "population_type_raw", "Value": "value_raw"}
    )
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = add_numeric_flags(df, "value_raw", "value_observed")
    df["population_type_std"] = df["population_type_raw"].map(TIME_TYPE_MAP).fillna(df["population_type_raw"])
    df = enrich_country(df, "host_country_raw", "host")
    df = enrich_country(df, "origin_country_raw", "origin")
    df["dataset"] = "time_series"
    df["metric_family"] = np.where(
        df["population_type_std"].isin(["Returned refugees", "Returned IDPs"]), "durable_solution_stock", "population_stock"
    )
    return df


def build_mapping_audit(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    parts: List[pd.DataFrame] = []
    for dataset, df in frames.items():
        for prefix in ["host", "origin"]:
            status_col = f"{prefix}_mapping_status"
            if status_col not in df.columns:
                continue
            tmp = (
                df.groupby([status_col, f"{prefix}_map_eligible_flag"], dropna=False)
                .size()
                .reset_index(name="rows")
                .rename(columns={status_col: "mapping_status", f"{prefix}_map_eligible_flag": "map_eligible_flag"})
            )
            tmp.insert(0, "dataset", dataset)
            tmp.insert(1, "country_role", prefix)
            parts.append(tmp)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def build_unmapped_values(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: List[dict] = []
    for dataset, df in frames.items():
        for prefix in ["host", "origin"]:
            status = f"{prefix}_mapping_status"
            raw_col = f"{prefix}_country_raw"
            if status not in df.columns or raw_col not in df.columns:
                continue
            bad = df[df[status].eq("unmapped")]
            for value, count in bad[raw_col].value_counts(dropna=False).items():
                rows.append({"dataset": dataset, "country_role": prefix, "raw_country_value": value, "rows": int(count)})
    return pd.DataFrame(rows).sort_values(["dataset", "country_role", "rows"], ascending=[True, True, False]) if rows else pd.DataFrame(columns=["dataset", "country_role", "raw_country_value", "rows"])


def build_hard_checks(c: Config, raw_inventory: pd.DataFrame, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: List[dict] = []
    raw_counts = raw_inventory.set_index("dataset")["rows"].to_dict()
    for dataset, df in frames.items():
        # Persons of concern has both wide and long; compare wide only for row-loss.
        raw_name = "persons_of_concern" if dataset == "persons_of_concern_wide" else dataset
        if raw_name in raw_counts:
            rows.append(
                {
                    "check": f"no_row_loss__{dataset}",
                    "status": "PASS" if int(raw_counts[raw_name]) == len(df) else "FAIL",
                    "detail": f"raw={raw_counts[raw_name]}, clean={len(df)}",
                }
            )

    # Numeric values should not be negative after cleaning.
    for dataset, df in frames.items():
        observed_cols = [col for col in df.columns if col.endswith("_observed") or col == "value_observed"]
        if not observed_cols:
            continue
        negatives = int((df[observed_cols] < 0).sum(numeric_only=True).sum())
        rows.append({"check": f"no_negative_observed_values__{dataset}", "status": "PASS" if negatives == 0 else "FAIL", "detail": f"negative_cells={negatives}"})

    unmapped = build_unmapped_values(frames)
    rows.append(
        {
            "check": "country_mapping_unmapped_rows",
            "status": "PASS" if len(unmapped) == 0 else "WARN",
            "detail": f"unique_unmapped_values={len(unmapped)}; see 00_audit/unmapped_country_values.csv",
        }
    )

    asylum = frames.get("asylum_seekers")
    if asylum is not None:
        mismatches = int(asylum["decision_total_mismatch"].sum())
        rows.append(
            {
                "check": "asylum_decision_total_mismatch_documented",
                "status": "DOCUMENTED",
                "detail": f"rows={mismatches}; reported totals are retained, missing totals are recomputed from components",
            }
        )
        na_raw = asylum["rsd_procedure_raw"].astype(str).str.contains("/ NA", regex=False).sum()
        new_stage = asylum["rsd_stage_code"].eq("NEW").sum()
        rows.append(
            {
                "check": "literal_NA_rsd_stage_protected",
                "status": "PASS" if int(na_raw) == int(new_stage) else "WARN",
                "detail": f"raw '/ NA' rows={int(na_raw)}, parsed NEW rows={int(new_stage)}",
            }
        )
    return pd.DataFrame(rows)




def build_clean_file_manifest(c: Config, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a compact manifest for teammates and the report appendix."""
    rows: List[dict] = []
    expected_files = {
        "resettlement": "resettlement_clean.csv.gz",
        "asylum_seekers_monthly": "asylum_seekers_monthly_clean.csv.gz",
        "asylum_seekers": "asylum_seekers_clean.csv.gz",
        "demographics": "demographics_clean.csv.gz",
        "persons_of_concern_wide": "persons_of_concern_clean_wide.csv.gz",
        "persons_of_concern_long": "persons_of_concern_clean_long.csv.gz",
        "time_series": "time_series_clean.csv.gz",
    }
    for dataset, filename in expected_files.items():
        path = c.output_dir / "01_clean" / filename
        df = frames.get(dataset)
        rows.append(
            {
                "dataset": dataset,
                "clean_file": str(path.relative_to(c.output_dir)) if path.exists() else filename,
                "exists": bool(path.exists()),
                "rows": int(len(df)) if df is not None else np.nan,
                "columns": int(len(df.columns)) if df is not None else np.nan,
                "size_mb": round(path.stat().st_size / 1_048_576, 3) if path.exists() else np.nan,
                "metric_family": str(df["metric_family"].iloc[0]) if df is not None and "metric_family" in df.columns and len(df) else "",
            }
        )
    return pd.DataFrame(rows)


def build_core_data_dictionary() -> pd.DataFrame:
    """Explain the core columns created by preprocessing.

    This file is intentionally concise so it can be copied into README/report material.
    """
    rows = [
        ("year", "integer", "Reporting year."),
        ("host_country_raw", "string", "Original country/territory of asylum or residence."),
        ("host_country_std", "string", "Standardised host/asylum country label used by charts."),
        ("host_iso3", "string", "ISO3-style host code; custom X_* codes indicate special/non-map entities."),
        ("host_mapping_status", "string", "Country-mapping method/status: manual_iso, pycountry, special_entity, historical/composite, etc."),
        ("host_map_eligible_flag", "boolean", "Whether the host entity can be safely plotted on country maps."),
        ("origin_country_raw", "string", "Original origin-country label."),
        ("origin_country_std", "string", "Standardised origin-country label used by charts."),
        ("origin_iso3", "string", "ISO3-style origin code; custom X_* codes indicate special/non-map entities."),
        ("origin_mapping_status", "string", "Country-mapping method/status for origin labels."),
        ("origin_map_eligible_flag", "boolean", "Whether the origin entity can be safely plotted on country maps."),
        ("value_observed", "float", "Cleaned observed population stock for time_series/persons_of_concern long data."),
        ("applications_observed", "float", "Cleaned observed asylum applications during year."),
        ("applications_monthly_observed", "float", "Cleaned observed monthly asylum applications."),
        ("resettlement_observed", "float", "Cleaned observed resettlement flow."),
        ("*_is_blank", "boolean", "Original cell was blank and is treated as missing, not zero."),
        ("*_is_redacted", "boolean", "Original cell was '*' and is treated as missing/redacted, not zero."),
        ("*_is_zero", "boolean", "Original numeric value is a valid reported zero."),
        ("*_is_negative_raw", "boolean", "Original numeric value was negative and was set to missing as an impossible count."),
        ("population_type_std", "string", "Standardised population category: Refugees, Asylum-seekers, IDPs, Stateless persons, etc."),
        ("metric_family", "string", "Analytical family: population stock, application flow, monthly flow, durable solution flow, demographic stock."),
    ]
    return pd.DataFrame(rows, columns=["column_pattern", "type", "definition"])


def write_preprocessing_handoff(c: Config, frames: Dict[str, pd.DataFrame], checks: pd.DataFrame) -> None:
    manifest = build_clean_file_manifest(c, frames)
    dictionary = build_core_data_dictionary()
    save_csv(manifest, c.output_dir / "00_audit" / "clean_file_manifest.csv")
    save_csv(dictionary, c.output_dir / "07_report_assets" / "core_clean_data_dictionary.csv")
    quality_gate = checks.copy()
    quality_gate["blocks_pipeline"] = quality_gate["status"].eq("FAIL")
    save_csv(quality_gate, c.output_dir / "00_audit" / "quality_gate_summary.csv")
    handoff = {
        "section": "preprocessing",
        "app_included": False,
        "clean_files_ready_for_eda": [row["clean_file"] for _, row in manifest[manifest["exists"]].iterrows()],
        "quality_gate": "PASS" if not quality_gate["blocks_pipeline"].any() else "FAIL",
        "methodological_notes": [
            "reported zeros are preserved",
            "blank and redacted values are missing with flags",
            "historical/composite countries are retained but marked map-ineligible",
            "stock and flow metrics are kept separate",
        ],
    }
    (c.output_dir / "00_audit" / "preprocessing_handoff_contract.json").write_text(json.dumps(handoff, indent=2), encoding="utf-8")

def write_methodology(c: Config, inv: pd.DataFrame, numeric: pd.DataFrame, checks: pd.DataFrame) -> None:
    total_rows = int(inv["rows"].sum())
    zero_cells = int(numeric["zero_rows"].sum()) if not numeric.empty else 0
    blank_cells = int(numeric["blank_rows"].sum()) if not numeric.empty else 0
    redacted_cells = int(numeric["redacted_star_rows"].sum()) if not numeric.empty else 0
    negative_cells = int(numeric["negative_raw_rows"].sum()) if not numeric.empty else 0
    text = f"""
# Preprocessing methodology

## Scope

This preprocessing layer uses six UNHCR-style datasets: `resettlement.csv`,
`asylum_seekers_monthly.csv`, `demographics.csv`, `asylum_seekers.csv`,
`persons_of_concern.csv`, and `time_series.csv`. Combined raw rows: **{total_rows:,}**.

## Core data decisions

1. Reported zero values are preserved as valid observations.
2. Redacted values (`*`), blanks, parse failures and impossible negative counts are converted to missing values and tracked through explicit flags.
3. Country names are standardised and enriched with ISO3 codes where possible.
4. Historical/composite entities are retained for ranked analysis but marked as `map_eligible_flag = False`.
5. Population-stock datasets (`time_series.csv`, `persons_of_concern.csv`) are kept separate from flow datasets (`asylum_seekers.csv`, `asylum_seekers_monthly.csv`, `resettlement.csv`).

## Numeric quality summary

- Zero cells preserved: **{zero_cells:,}**
- Blank cells flagged: **{blank_cells:,}**
- Redacted star cells flagged: **{redacted_cells:,}**
- Negative raw cells set to missing: **{negative_cells:,}**

## Why this matters for the dashboard

The dashboard combines time, geography, origin-destination relationships and multiple population categories. Clean ISO3 fields support maps; missingness flags support transparent reporting; and the separation between stock and flow metrics prevents misleading comparisons.

## Hard checks

{checks.to_markdown(index=False)}
""".strip()
    (c.output_dir / "07_report_assets" / "preprocessing_methodology.md").write_text(text, encoding="utf-8")


def run(c: Config) -> None:
    ensure_dirs(c)
    print(f"[1/5] Auditing raw files in {c.input_dir}")
    inv, numeric = run_raw_audit(c)

    print("[2/5] Cleaning all six datasets")
    res = clean_resettlement(c)
    monthly = clean_asylum_seekers_monthly(c)
    asylum = clean_asylum_seekers(c)
    demo = clean_demographics(c)
    poc_wide, poc_long = clean_persons_of_concern(c)
    ts = clean_time_series(c)

    clean_dir = c.output_dir / "01_clean"
    print(f"[3/5] Writing cleaned files to {clean_dir}")
    save_csv(res, clean_dir / "resettlement_clean.csv.gz", gzip=True)
    save_csv(monthly, clean_dir / "asylum_seekers_monthly_clean.csv.gz", gzip=True)
    save_csv(asylum, clean_dir / "asylum_seekers_clean.csv.gz", gzip=True)
    save_csv(demo, clean_dir / "demographics_clean.csv.gz", gzip=True)
    save_csv(poc_wide, clean_dir / "persons_of_concern_clean_wide.csv.gz", gzip=True)
    save_csv(poc_long, clean_dir / "persons_of_concern_clean_long.csv.gz", gzip=True)
    save_csv(ts, clean_dir / "time_series_clean.csv.gz", gzip=True)

    frames = {
        "resettlement": res,
        "asylum_seekers_monthly": monthly,
        "demographics": demo,
        "asylum_seekers": asylum,
        "persons_of_concern_wide": poc_wide,
        "persons_of_concern_long": poc_long,
        "time_series": ts,
    }
    print("[4/5] Writing mapping audit and hard checks")
    mapping = build_mapping_audit(frames)
    unmapped = build_unmapped_values(frames)
    checks = build_hard_checks(c, inv, frames)
    save_csv(mapping, c.output_dir / "00_audit" / "country_mapping_audit.csv")
    save_csv(unmapped, c.output_dir / "00_audit" / "unmapped_country_values.csv")
    save_csv(checks, c.output_dir / "00_audit" / "preprocessing_hard_checks.csv")

    write_methodology(c, inv, numeric, checks)
    write_preprocessing_handoff(c, frames, checks)
    manifest = {
        "input_dir": str(c.input_dir),
        "output_dir": str(c.output_dir),
        "raw_files": RAW_FILES,
        "clean_files": [p.name for p in sorted(clean_dir.glob("*.csv.gz"))],
    }
    (c.output_dir / "00_audit" / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("[5/5] Preprocessing complete")
    print(checks.to_string(index=False))
    if (checks["status"] == "FAIL").any():
        print("ERROR: one or more hard checks failed. Inspect 00_audit/preprocessing_hard_checks.csv", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run(parse_args())
