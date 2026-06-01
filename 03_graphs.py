#!/usr/bin/env python3
"""
SECTION 3 — GRAPH 5 AND GRAPH 6 ONLY
Global Refugee Movement Dashboard, Group 11

Purpose
-------
Render the two final ranked-bar figures requested for this section:

- Graph 5: Top origin countries
- Graph 6: Top host countries

This script intentionally does not build the full dashboard. It reads the chart-ready
CSV files created by 02_eda.py and exports polished PNG figures for report/slides/Shiny.

Run order
---------
python 01_preprocessing.py --input-dir data/raw --output-dir outputs
python 02_eda.py --output-dir outputs --top-n 10 --scope cross_border
python 03_graph5_6.py --output-dir outputs
"""
from __future__ import annotations

import argparse
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch, Rectangle

# A restrained palette designed for academic slides and final report figures.
COLORS = {
    "paper": "#F6F8FB",
    "card": "#FFFFFF",
    "ink": "#0F172A",
    "muted": "#64748B",
    "grid": "#E5E7EB",
    "track": "#EDF2F7",
    "origin": "#E8761A",
    "origin_dark": "#B45309",
    "host": "#12805C",
    "host_dark": "#065F46",
    "navy": "#172554",
}


@dataclass(frozen=True)
class Config:
    output_dir: Path
    dpi: int = 360
    export_svg: bool = False


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Render only Graph 5 and Graph 6 from EDA chart data.")
    parser.add_argument("--output-dir", default="outputs", help="Folder created by 01_preprocessing.py and 02_eda.py.")
    parser.add_argument("--dpi", type=int, default=360, help="PNG export resolution.")
    parser.add_argument("--export-svg", action="store_true", help="Also export SVG versions for LaTeX/report editing.")
    args = parser.parse_args()
    return Config(Path(args.output_dir).resolve(), args.dpi, args.export_svg)


def read_chart_data(output_dir: Path, filename: str) -> pd.DataFrame:
    path = output_dir / "03_chart_data" / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run 02_eda.py before this graph section.")
    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        raise ValueError(f"{path} is empty; cannot render a ranked chart.")
    return df


def read_eda_manifest(output_dir: Path) -> dict:
    path = output_dir / "02_eda" / "eda_manifest.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def ensure_dirs(output_dir: Path) -> Path:
    fig_dir = output_dir / "04_figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "07_report_assets").mkdir(parents=True, exist_ok=True)
    return fig_dir


def fmt_compact(value: float) -> str:
    if pd.isna(value):
        return ""
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"


def fmt_pct(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value * 100:.1f}%"


def wrap_label(value: object, width: int = 32) -> str:
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False))


def setup_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": COLORS["paper"],
            "axes.facecolor": COLORS["card"],
            "savefig.facecolor": COLORS["paper"],
            "axes.edgecolor": COLORS["grid"],
            "axes.labelcolor": COLORS["muted"],
            "xtick.color": COLORS["muted"],
            "ytick.color": COLORS["ink"],
            "text.color": COLORS["ink"],
            "axes.titleweight": "bold",
        }
    )


def add_card(fig: plt.Figure) -> None:
    card = FancyBboxPatch(
        (0.015, 0.018),
        0.97,
        0.962,
        boxstyle="round,pad=0.014,rounding_size=0.03",
        transform=fig.transFigure,
        linewidth=1.2,
        edgecolor="#D8E1EA",
        facecolor=COLORS["card"],
        zorder=-20,
    )
    fig.patches.append(card)


def add_badge(fig: plt.Figure, x: float, y: float, text: str, color: str) -> None:
    width = 0.045 + len(text) * 0.0082
    badge = FancyBboxPatch(
        (x, y),
        width,
        0.044,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        transform=fig.transFigure,
        linewidth=0,
        facecolor=color,
        zorder=3,
    )
    fig.patches.append(badge)
    fig.text(x + 0.015, y + 0.013, text, fontsize=9.5, fontweight="bold", color="#FFFFFF", zorder=4)


def validate_ranked_input(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    required = {"rank", label_col, "value_observed", "share_of_selected_total", "year", "population_scope"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Chart data is missing required columns: {missing}")
    d = df.copy()
    d["rank"] = pd.to_numeric(d["rank"], errors="coerce")
    d["value_observed"] = pd.to_numeric(d["value_observed"], errors="coerce")
    d["share_of_selected_total"] = pd.to_numeric(d["share_of_selected_total"], errors="coerce")
    d = d.dropna(subset=["rank", "value_observed"])
    d = d.sort_values("rank", ascending=True)
    if d.empty:
        raise ValueError("No valid rows remain after input validation.")
    return d


def ranked_bar_figure(
    df: pd.DataFrame,
    label_col: str,
    title: str,
    subtitle: str,
    output_path: Path,
    accent: str,
    accent_dark: str,
    footnote: str,
    dpi: int,
    export_svg: bool = False,
) -> None:
    setup_matplotlib()
    d = validate_ranked_input(df, label_col).copy()
    # Matplotlib barh plots bottom-to-top, so reverse the rank order for display.
    plot = d.sort_values("rank", ascending=False).copy()
    plot["label_wrapped"] = plot[label_col].map(lambda x: wrap_label(x, 26))

    n = len(plot)
    fig_h = max(7.2, 0.58 * n + 3.35)
    fig = plt.figure(figsize=(13.6, fig_h), facecolor=COLORS["paper"])
    add_card(fig)

    latest_year = int(d["year"].dropna().iloc[0]) if d["year"].notna().any() else None
    top_value = float(d["value_observed"].max())
    total_top = float(d["value_observed"].sum())

    # Header intentionally lives outside the plotting area so it never overlaps bars.
    fig.text(0.055, 0.94, title, fontsize=25, fontweight="bold", color=COLORS["ink"], ha="left", va="top")
    fig.text(0.055, 0.89, "\n".join(textwrap.wrap(subtitle, width=82)), fontsize=12.5, color=COLORS["muted"], ha="left", va="top", linespacing=1.25)
    add_badge(fig, 0.055, 0.785, "CLEANED DATA", accent_dark)
    add_badge(fig, 0.195, 0.785, "STOCK METRIC", COLORS["navy"])

    # KPI box in the header.
    kpi_x, kpi_y, kpi_w, kpi_h = 0.70, 0.795, 0.23, 0.11
    kpi = FancyBboxPatch(
        (kpi_x, kpi_y),
        kpi_w,
        kpi_h,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        transform=fig.transFigure,
        linewidth=1,
        edgecolor="#E2E8F0",
        facecolor="#F8FAFC",
        zorder=1,
    )
    fig.patches.append(kpi)
    fig.text(kpi_x + 0.018, kpi_y + 0.070, f"Top {len(d)} total", fontsize=10.5, color=COLORS["muted"], fontweight="bold")
    fig.text(kpi_x + 0.018, kpi_y + 0.026, fmt_compact(total_top), fontsize=24, color=accent_dark, fontweight="bold")
    if latest_year is not None:
        fig.text(kpi_x + 0.135, kpi_y + 0.034, f"year {latest_year}", fontsize=10.5, color=COLORS["muted"])

    ax = fig.add_axes([0.335, 0.17, 0.59, 0.59])
    y = np.arange(n)
    maxv = top_value * 1.18 if top_value > 0 else 1.0

    # Track bars communicate relative scale and make the graphic look dashboard-ready.
    ax.barh(y, [maxv] * n, color=COLORS["track"], height=0.67, edgecolor="none", zorder=1)
    ax.barh(y, plot["value_observed"], color=accent, height=0.67, edgecolor="none", zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(plot["label_wrapped"], fontsize=11.5)
    ax.set_xlim(0, maxv)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_compact(x)))
    ax.tick_params(axis="x", labelsize=10.5, length=0, pad=8)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.9, alpha=0.75, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Rank numbers placed in a separate left strip.
    x_rank = -0.42 * maxv
    for yi, (_, row) in enumerate(plot.iterrows()):
        rank_text = f"#{int(row['rank'])}"
        ax.text(x_rank, yi, rank_text, va="center", ha="center", fontsize=11, fontweight="bold", color=accent_dark, clip_on=False)
        value_label = f"{fmt_compact(row['value_observed'])}  ·  {fmt_pct(row['share_of_selected_total'])}"
        ax.text(row["value_observed"] + maxv * 0.015, yi, value_label, va="center", ha="left", fontsize=11, color=COLORS["ink"], fontweight="bold")

    ax.text(x_rank, n - 0.15, "Rank", fontsize=9.5, color=COLORS["muted"], ha="center", va="bottom", clip_on=False)
    ax.set_xlabel("Observed population stock", fontsize=10.5, color=COLORS["muted"], labelpad=14)

    # Footnote and methodology are visible but unobtrusive.
    fig.text(0.055, 0.095, footnote, fontsize=9.5, color=COLORS["muted"], ha="left", va="top")
    fig.text(
        0.055,
        0.055,
        "Method note: values are generated from chart-ready EDA tables built after preprocessing; zero values are preserved and missing/redacted cells are tracked separately.",
        fontsize=8.8,
        color="#7C8798",
        ha="left",
        va="top",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", pad_inches=0.14)
    if export_svg:
        fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)


def run(c: Config) -> None:
    fig_dir = ensure_dirs(c.output_dir)
    manifest = read_eda_manifest(c.output_dir)

    g5 = read_chart_data(c.output_dir, "graph5_top_origin_countries.csv")
    g6 = read_chart_data(c.output_dir, "graph6_top_host_countries.csv")

    year = manifest.get("year")
    scope_types = manifest.get("scope_types") or []
    scope_label = " + ".join(scope_types) if scope_types else str(g5.get("population_scope", pd.Series([""])).iloc[0]).replace("+", " + ")
    year_label = f"{year}" if year is not None else str(g5.get("year", pd.Series([""])).iloc[0])

    common_scope = f"Latest year {year_label} · Scope: {scope_label} · cleaned stock data."

    ranked_bar_figure(
        df=g5,
        label_col="origin_country_std",
        title="Graph 5 — Top Origin Countries",
        subtitle=f"Largest origin countries · {common_scope}",
        output_path=fig_dir / "graph5_top_origin_countries.png",
        accent=COLORS["origin"],
        accent_dark=COLORS["origin_dark"],
        footnote="Source: cleaned UNHCR six-dataset pipeline, using time_series_clean.csv.gz. Metric is observed population stock, not asylum-application flow.",
        dpi=c.dpi,
        export_svg=c.export_svg,
    )

    ranked_bar_figure(
        df=g6,
        label_col="host_country_std",
        title="Graph 6 — Top Host Countries",
        subtitle=f"Largest host countries · {common_scope}",
        output_path=fig_dir / "graph6_top_host_countries.png",
        accent=COLORS["host"],
        accent_dark=COLORS["host_dark"],
        footnote="Source: cleaned UNHCR six-dataset pipeline. Default host ranking excludes IDPs because IDPs describe internal displacement, not cross-border hosting.",
        dpi=c.dpi,
        export_svg=c.export_svg,
    )

    graph_manifest = {
        "section": "Graph 5 and Graph 6 only",
        "input_files": [
            "03_chart_data/graph5_top_origin_countries.csv",
            "03_chart_data/graph6_top_host_countries.csv",
        ],
        "output_files": [
            "04_figures/graph5_top_origin_countries.png",
            "04_figures/graph6_top_host_countries.png",
        ],
        "year": year_label,
        "scope": scope_label,
        "metric": "observed population stock from cleaned time_series data",
    }
    (c.output_dir / "07_report_assets" / "graph5_6_design_notes.md").write_text(
        "# Graph 5 and Graph 6 design notes\n\n"
        "These figures use ranked horizontal bars because forced-displacement distributions are highly skewed and country labels are long. "
        "The visual design prioritises readable country names, direct rank comparison, compact magnitude labels, and transparent methodology notes. "
        "Both charts are rendered only from chart-ready EDA outputs, not from raw CSV files.\n",
        encoding="utf-8",
    )
    (c.output_dir / "07_report_assets" / "graph5_6_manifest.json").write_text(json.dumps(graph_manifest, indent=2), encoding="utf-8")

    print("Graph section complete. Rendered only Graph 5 and Graph 6.")
    print(f"- {fig_dir / 'graph5_top_origin_countries.png'}")
    print(f"- {fig_dir / 'graph6_top_host_countries.png'}")


if __name__ == "__main__":
    run(parse_args())
