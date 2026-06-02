"""Methodology and reproducibility outputs."""
from __future__ import annotations

from shiny import Inputs, Outputs, render, ui

from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState


def _quality_rows(data: DataStore):
    q = data.quality_gate
    if q.empty:
        return [ui.div(ui.span("Preprocessing quality gates"), ui.strong("Available in outputs/00_audit"), class_="quality-line")]
    cols = q.columns.tolist()
    label_col = cols[0]
    status_col = cols[-1]
    rows = []
    for _, r in q.head(8).iterrows():
        rows.append(ui.div(ui.span(str(r[label_col])), ui.strong(str(r[status_col])), class_="quality-line"))
    return rows


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render.ui
    def method_cards():
        return ui.div(
            ui.h3("Architecture"),
            ui.tags.ul(
                ui.tags.li("app.py is a thin entry point."),
                ui.tags.li("refugee_app/services handles data loading, filters and JSON safety."),
                ui.tags.li("refugee_app/modules separates hero, maps, rankings, storytelling and method notes."),
                ui.tags.li("refugee_app/ui owns theme, layout and scroll-snap sections."),
            ),
            ui.h3("Data contract"),
            ui.p("The Shiny app reads only cleaned/chart-ready outputs. Raw CSV files are processed upstream by preprocessing and EDA scripts."),
        )

    @output
    @render.ui
    def quality_cards():
        return ui.div(
            ui.h3("Quality gates"),
            *_quality_rows(data),
            ui.h3("Method note"),
            ui.p("Graph 5 and Graph 6 use population-stock data. Asylum seeker files are treated as flow data for applications and corridor context. IDPs are separated from default cross-border host rankings."),
        )
