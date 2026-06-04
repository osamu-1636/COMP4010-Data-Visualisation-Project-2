"""Top-level Shiny UI layout for the final core dashboard."""
from __future__ import annotations

from pathlib import Path

from shiny import ui

from refugee_app.constants import CRISIS_ORIGIN
from refugee_app.services.data_loader import DataStore
from refugee_app.ui.sections import (
    globe_svg,
    section_cover,
    section_crisis_hosts_scene,
    section_crisis_routes_scene,
    section_dataset_intro,
    section_flow,
    section_host_map_scene,
    section_host_rank_scene,
    section_host_snapshot,
    section_method_pipeline_scene,
    section_origin_rank_scene,
    section_pressure_scene,
    section_quality_scene,
    section_scale,
)


def build_ui(data: DataStore) -> ui.Tag:
    css_path = Path(__file__).resolve().parents[1] / "www" / "styles.css"
    js_path = Path(__file__).resolve().parents[1] / "www" / "app.js"

    return ui.page_fluid(
        ui.include_css(str(css_path)),
        ui.tags.script(js_path.read_text(encoding="utf-8")),
        ui.div(
            ui.div(
                ui.div(
                    ui.div(globe_svg(), class_="brand-icon"),
                    ui.div(
                        ui.div("VinUniversity | Group 11", class_="institution-tag"),
                        ui.h1("Forced Migration"),
                        ui.p("A focused UNHCR data story: scale, geography, corridors, rankings and crisis evidence."),
                        class_="brand-copy",
                    ),
                    ui.div(ui.div("Last data year"), ui.strong(str(data.year_max)), class_="year-badge"),
                    class_="brand-row",
                ),
                ui.div(
                    ui.div(
                        ui.input_slider("year", "Year", data.year_min, data.year_max, data.year_max, step=1),
                        class_="control control-year",
                    ),
                    ui.div(
                        ui.input_select("crisis", "Crisis", choices=list(CRISIS_ORIGIN.keys()), selected="All Crises"),
                        class_="control",
                    ),
                    ui.div(
                        ui.input_selectize("origin", "Origin", choices=data.origin_choices, selected="All"),
                        class_="control",
                    ),
                    ui.div(
                        ui.input_selectize("host", "Destination", choices=data.host_choices, selected="All"),
                        class_="control",
                    ),
                    ui.div(
                        ui.input_select(
                            "refugee_type",
                            "Population scope",
                            choices=[
                                "All cross-border",
                                "Refugees",
                                "Asylum-seekers",
                                "Others of concern",
                                "Active forced incl. IDPs",
                            ],
                            selected="All cross-border",
                        ),
                        class_="control",
                    ),
                    ui.div(
                        ui.input_slider("top_n", "Top N", 5, 50, 30, step=1),
                        class_="control control-topn",
                    ),
                    ui.div(
                        ui.input_action_button("apply_filters", "Apply", class_="apply-btn"),
                        class_="control action-control apply-control",
                    ),
                    ui.div(
                        ui.input_action_button("reset", "Reset", class_="reset-btn"),
                        class_="control action-control reset-control",
                    ),
                    class_="filter-row",
                ),
                class_="command-bar",
            ),
            ui.div(
                ui.tags.a("00", href="#slide-cover"),
                ui.tags.a("01", href="#slide-dataset"),
                ui.tags.a("02", href="#slide-scale"),
                ui.tags.a("03", href="#slide-host-snapshot"),
                ui.tags.a("04", href="#slide-flow"),
                ui.tags.a("05", href="#slide-space-map"),
                ui.tags.a("06", href="#slide-pressure"),
                ui.tags.a("07", href="#slide-origin-rank"),
                ui.tags.a("08", href="#slide-host-rank"),
                ui.tags.a("09", href="#slide-crisis-routes"),
                ui.tags.a("10", href="#slide-crisis-hosts"),
                ui.tags.a("11", href="#slide-method-pipeline"),
                ui.tags.a("12", href="#slide-quality"),
                class_="slide-dots",
            ),
            ui.div(
                section_cover(),
                section_dataset_intro(),
                section_scale(),
                section_host_snapshot(),
                section_flow(),
                section_host_map_scene(),
                section_pressure_scene(),
                section_origin_rank_scene(),
                section_host_rank_scene(),
                section_crisis_routes_scene(),
                section_crisis_hosts_scene(),
                section_method_pipeline_scene(),
                section_quality_scene(),
                class_="snap-container",
            ),
            class_="app-shell",
        ),
    )
