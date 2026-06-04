"""Reusable UI blocks and final scroll-snap dashboard sections.

Final story design:
Scale -> Geography -> Corridors -> Rankings -> Crisis -> Method.
Weak bonus sections are intentionally not shown in the final UI.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from shiny import ui
from shinywidgets import output_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE


def globe_svg() -> ui.Tag:
    """Render the VinUni logo if available, otherwise use a neutral globe icon."""
    logo_dir = Path(__file__).resolve().parents[1] / "www"
    for ext in ("svg", "png", "jpg", "jpeg", "webp"):
        logo_path = logo_dir / f"vinuni_logo.{ext}"
        if logo_path.exists():
            mime = mimetypes.guess_type(str(logo_path))[0] or "image/png"
            encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            return ui.tags.img(
                src=f"data:{mime};base64,{encoded}",
                class_="vinuni-logo-img",
                alt="VinUniversity logo",
            )

    return ui.HTML("""
    <svg class='globe-icon' viewBox='0 0 100 100' aria-hidden='true'>
      <circle cx='50' cy='50' r='44' fill='#e8f2fb' stroke='#111827' stroke-width='3.6'/>
      <path d='M21 36 C35 18 59 22 75 32 C60 38 62 49 71 59 C58 65 44 55 32 66 C28 55 13 51 21 36Z' fill='#9fc7e5' stroke='#111827' stroke-width='1.5'/>
      <path d='M10 50 H90 M50 6 C25 26 25 74 50 94 M50 6 C75 26 75 74 50 94' fill='none' stroke='#111827' stroke-width='2' opacity='.56'/>
    </svg>
    """)


def cover_sketch() -> ui.Tag:
    return ui.HTML("""
    <svg class='cover-sketch' viewBox='0 0 1180 660' role='img' aria-label='Sketch map of refugee movement corridors'>
      <rect x='8' y='8' width='1164' height='644' rx='34' fill='#fffdf8' stroke='#111827' stroke-width='4'/>
      <g opacity='.18' stroke='#111827' stroke-width='2' fill='none'>
        <path d='M150 260 C230 190 310 205 390 150 C500 75 615 110 720 95 C825 80 925 95 1030 60'/>
        <path d='M120 395 C245 360 345 405 465 365 C575 330 675 350 760 310 C850 270 945 305 1060 250'/>
        <path d='M205 515 C310 465 420 500 535 458 C660 410 785 445 950 370'/>
        <path d='M290 210 C340 260 410 285 470 340 C525 390 570 450 620 520'/>
        <path d='M725 160 C690 245 700 335 675 430 C660 485 655 535 620 600'/>
      </g>
      <g stroke-linecap='round' fill='none'>
        <path class='sketch-route route-blue' d='M260 255 C390 180 480 210 610 290 C720 360 830 355 945 315'/>
        <path class='sketch-route route-orange' d='M430 410 C545 300 660 315 780 240 C865 188 955 175 1060 140'/>
        <path class='sketch-route route-purple' d='M210 470 C360 420 455 475 575 435 C690 395 760 455 870 430'/>
        <path class='sketch-route route-green' d='M530 195 C590 260 560 345 625 410 C705 490 805 505 930 555'/>
      </g>
      <g>
        <circle cx='260' cy='255' r='14' fill='#6f9166' stroke='white' stroke-width='4'/>
        <circle cx='610' cy='290' r='11' fill='#111827' stroke='white' stroke-width='3'/>
        <circle cx='945' cy='315' r='14' fill='#df7a26' stroke='white' stroke-width='4'/>
        <circle cx='430' cy='410' r='14' fill='#6f9166' stroke='white' stroke-width='4'/>
        <circle cx='780' cy='240' r='11' fill='#111827' stroke='white' stroke-width='3'/>
        <circle cx='1060' cy='140' r='14' fill='#df7a26' stroke='white' stroke-width='4'/>
        <circle cx='210' cy='470' r='14' fill='#6f9166' stroke='white' stroke-width='4'/>
        <circle cx='575' cy='435' r='11' fill='#111827' stroke='white' stroke-width='3'/>
        <circle cx='870' cy='430' r='14' fill='#df7a26' stroke='white' stroke-width='4'/>
      </g>
      <g class='sketch-label'>
        <text x='72' y='88'>FORCED MIGRATION</text>
        <text x='72' y='126' class='small'>Scale, geography, origin-host corridors and crisis storytelling</text>
        <text x='72' y='594' class='tiny'>Green = origin | Orange = host | Black = moving groups | Lines = corridors</text>
      </g>
    </svg>
    """)


def metric_card(value_id: str, label: str, icon: str, accent: str) -> ui.Tag:
    return ui.div(
        ui.div(icon, class_="metric-icon"),
        ui.div(ui.output_text(value_id), class_="metric-value", style=f"color:{accent}"),
        ui.div(label, class_="metric-label"),
        class_="metric-card",
    )


def chart_card(num: str, title: str, subtitle: str, widget_id: str, class_extra: str = "") -> ui.Tag:
    return ui.div(
        ui.div(
            ui.span(num, class_="chart-num"),
            ui.div(
                ui.div(title, class_="chart-title"),
                ui.div(subtitle, class_="chart-subtitle"),
            ),
            class_="chart-head",
        ),
        ui.div(output_widget(widget_id), class_="chart-body"),
        class_=f"chart-card {class_extra}".strip(),
    )


def explain_card(kicker: str, title: str, body: str, bullets: list[str] | None = None, output_id: str | None = None) -> ui.Tag:
    children: list[ui.Tag] = [
        ui.div(kicker, class_="explain-kicker"),
        ui.h3(title),
        ui.p(body),
    ]
    if bullets:
        children.append(ui.tags.ul(*[ui.tags.li(x) for x in bullets]))
    if output_id:
        children.append(ui.output_ui(output_id))
    return ui.div(*children, class_="explain-card")


def story_row(visual: ui.Tag, text: ui.Tag, reverse: bool = False) -> ui.Tag:
    return ui.div(text, visual, class_="story-row reverse") if reverse else ui.div(visual, text, class_="story-row")


def ui_slide(num: str, kicker: str, title: str, subtitle: str, content: ui.Tag, slide_id: str) -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.div(
                ui.div(num, class_="slide-number"),
                ui.div(
                    ui.div(kicker, class_="slide-kicker"),
                    ui.h2(title),
                    ui.p(subtitle),
                ),
                class_="slide-title",
            ),
            content,
            class_="slide-inner",
        ),
        id=slide_id,
        class_="story-slide",
    )


def section_cover() -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.div(
                ui.div(
                    ui.div("Group 11 | UNHCR Refugee Data Finder / UNdata / HDX", class_="cover-kicker"),
                    ui.h1("Forced Migration"),
                    ui.h2("Visualizing Global Refugee Flows"),
                    ui.p("A focused scroll-based dashboard: scale, time, geography, origin-host corridors, country rankings and one crisis case study."),
                    ui.div(
                        ui.span("Scale"),
                        ui.span("Time"),
                        ui.span("Geography"),
                        ui.span("Corridors"),
                        ui.span("Rankings"),
                        ui.span("Crisis"),
                        class_="cover-tags",
                    ),
                    class_="cover-copy",
                ),
                ui.div(cover_sketch(), class_="cover-art-card"),
                class_="cover-layout",
            ),
            class_="slide-inner",
        ),
        id="slide-cover",
        class_="story-slide cover-slide",
    )


def section_executive() -> ui.Tag:
    return ui_slide(
        "01",
        "Executive overview",
        "Start with scale, then locate it geographically",
        "This section frames the dashboard before moving into origins, hosts and corridors.",
        ui.div(
            ui.div(
                metric_card("kpi_cross_border", "Cross-border scope", "CB", BLUE),
                metric_card("kpi_refugees", "Refugees", "R", GREEN),
                metric_card("kpi_idps", "Internally displaced", "IDP", ORANGE),
                metric_card("kpi_asylum", "Asylum-seekers", "A", PURPLE),
                metric_card("kpi_countries", "Countries and territories", "G", BLUE),
                class_="metric-grid",
            ),
            story_row(
                chart_card("2", "Displacement trend", "Observed population stock by year and population type", "trend_plot", "story-visual"),
                explain_card(
                    "Reading guide",
                    "Why begin with time?",
                    "The line chart shows whether the selected year belongs to a long-term increase, a crisis spike or a post-crisis plateau.",
                    ["Use the top filters to isolate scope and crisis.", "The selected year controls maps and rankings."],
                ),
            ),
            story_row(
                chart_card("3", "Host geography", "Host countries by observed stock for the selected year", "host_map", "story-visual"),
                ui.div(ui.output_ui("executive_insight"), class_="explain-card"),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-exec",
    )


def section_spatial() -> ui.Tag:
    return ui_slide(
        "02",
        "Spatial view",
        "Where is hosting concentrated?",
        "This slide keeps only the strongest spatial evidence and avoids crowded three-chart rows.",
        ui.div(
            story_row(
                chart_card("3A", "Host-country choropleth", "Map-eligible host countries; values are observed people", "host_map_large", "story-visual tall-map"),
                explain_card(
                    "Map purpose",
                    "Absolute hosting geography",
                    "The choropleth identifies where the selected displaced population is hosted. It is useful for concentration and regional-burden analysis.",
                    ["Values are observed people, not imputed totals.", "Map-eligible entities only are shown."],
                ),
            ),
            story_row(
                chart_card("3B", "Host burden ranking", "Host stock or per-capita pressure when available", "host_pressure_plot", "story-visual"),
                explain_card(
                    "Pressure reading",
                    "Burden is not only raw totals",
                    "A smaller country may face greater proportional pressure than a large country with a higher absolute stock. This chart supports the hosting-pressure research question.",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-space",
    )


def section_flow() -> ui.Tag:
    return ui_slide(
        "04",
        "Movement structure",
        "How origin-host corridors organize displacement",
        "The flow map is the main corridor visual. It receives its own row so route patterns remain readable.",
        ui.div(
            story_row(
                chart_card("1", "Global refugee corridors", "Curved origin-host routes with dynamic map focus", "flow_map", "story-visual flow-main"),
                explain_card(
                    "Main message",
                    "Displacement forms corridors, not random scatter",
                    "The route map shows dominant origin-host corridors under the current filters. Line width reflects magnitude and the map focuses on the current selection.",
                    ["Increase Top N for overview mode.", "Select a crisis or origin for focus mode."],
                ),
            ),
            class_="story-stack",
        ),
        "slide-flow",
    )


def section_rankings() -> ui.Tag:
    return ui_slide(
        "04",
        "Country rankings",
        "Graph 5 and Graph 6 answer the core research questions",
        "The two ranking charts are separated into two rows to avoid compressed scales.",
        ui.div(
            story_row(
                chart_card("5", "Top origin countries", "Countries producing the largest selected displaced populations", "graph5_plot", "story-visual rank-card"),
                explain_card(
                    "Research question 1",
                    "Where does displacement originate?",
                    "Graph 5 identifies the countries that account for the largest selected displaced population stock. Ranked bars are clearer than pie charts because the distribution is highly skewed.",
                ),
            ),
            story_row(
                chart_card("6", "Top host countries", "Countries hosting the largest selected displaced populations", "graph6_plot", "story-visual rank-card"),
                ui.div(ui.output_ui("ranking_note"), class_="explain-card"),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-rank",
    )


def section_storytelling() -> ui.Tag:
    return ui_slide(
        "05",
        "Crisis case study",
        "Follow one crisis from timeline to destinations",
        "This slide keeps the crisis story simple: timeline, routes and host ranking.",
        ui.div(
            story_row(
                chart_card("7A", "Main migration routes", "Top host destinations from the selected crisis origin", "crisis_routes", "story-visual"),
                ui.div(ui.output_ui("crisis_timeline"), class_="timeline-panel explain-card"),
            ),
            story_row(
                chart_card("7B", "Top crisis host countries", "Ranked host destinations for the selected crisis and year", "crisis_hosts", "story-visual compact"),
                explain_card(
                    "Host concentration",
                    "Regional neighbours often absorb the first burden",
                    "This ranking clarifies whether displacement remains regional or extends toward more distant host countries.",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-crisis",
    )


def section_method() -> ui.Tag:
    return ui_slide(
        "06",
        "Method and reproducibility",
        "Why the dashboard is defensible",
        "The app reads cleaned and chart-ready data only. Raw CSV files are processed upstream by preprocessing and EDA scripts.",
        ui.div(
            story_row(
                ui.div(ui.output_ui("method_cards"), class_="method-card"),
                explain_card(
                    "Pipeline",
                    "A reproducible data handoff",
                    "The dashboard is not cleaning raw CSV files live. Preprocessing and EDA create stable chart-ready data for the app.",
                ),
            ),
            story_row(
                ui.div(ui.output_ui("quality_cards"), class_="method-card"),
                ui.div(
                    ui.h3("Pipeline handoff"),
                    ui.tags.ol(
                        ui.tags.li("Six raw UNHCR-style CSV files are cleaned by 01_preprocessing.py."),
                        ui.tags.li("02_eda.py creates chart-ready tables in outputs/03_chart_data."),
                        ui.tags.li("app.py renders interactive views from cleaned/chart-ready data only."),
                        ui.tags.li("Graph 5/6 use population-stock data; asylum files remain flow datasets."),
                    ),
                    class_="explain-card",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-method",
    )


def section_dataset_intro() -> ui.Tag:
    return ui_slide(
        "01",
        "Dataset introduction",
        "What does this dashboard measure?",
        "The story combines cleaned UNHCR-style population stocks and movement-flow tables to explain the scale, geography and structure of forced migration.",
        ui.div(
            ui.div(
                metric_card("kpi_cross_border", "Cross-border scope", "CB", BLUE),
                metric_card("kpi_refugees", "Refugees", "R", GREEN),
                metric_card("kpi_idps", "Internally displaced", "IDP", ORANGE),
                metric_card("kpi_asylum", "Asylum-seekers", "A", PURPLE),
                metric_card("kpi_countries", "Countries and territories", "G", BLUE),
                class_="metric-grid dataset-metric-grid",
            ),
            ui.div(
                ui.div(
                    ui.div("Population stock", class_="dataset-kicker"),
                    ui.h3("Who is displaced?"),
                    ui.p("Annual observations cover refugees, asylum-seekers, internally displaced people and other populations of concern."),
                    class_="dataset-card",
                ),
                ui.div(
                    ui.div("Geography", class_="dataset-kicker"),
                    ui.h3("Where do people move?"),
                    ui.p("Standardized origin and host countries connect displacement totals to maps, rankings and origin-host corridors."),
                    class_="dataset-card",
                ),
                ui.div(
                    ui.div("Time", class_="dataset-kicker"),
                    ui.h3("How does displacement change?"),
                    ui.p("Annual and monthly records reveal long-term trends, crisis spikes and changes in hosting patterns."),
                    class_="dataset-card",
                ),
                ui.div(
                    ui.div("Evidence", class_="dataset-kicker"),
                    ui.h3("How is quality protected?"),
                    ui.p("The dashboard reads cleaned, audited and chart-ready outputs rather than processing raw files during interaction."),
                    class_="dataset-card",
                ),
                class_="dataset-intro-grid",
            ),
            class_="dataset-intro",
        ),
        "slide-dataset",
    )


def section_scale() -> ui.Tag:
    return ui_slide(
        "02",
        "Trend visualization",
        "How has forced migration changed over time?",
        "This standalone visualization reveals long-term growth, crisis spikes and changes across population types.",
        ui.div(
            story_row(
                chart_card("2", "Displacement trend", "Observed population stock by year and population type", "trend_plot", "story-visual"),
                explain_card(
                    "Reading guide",
                    "Why begin with time?",
                    "The line chart shows whether the selected year belongs to a long-term increase, a crisis spike or a post-crisis plateau.",
                    ["Use the top filters to isolate scope and crisis.", "The selected year controls maps and rankings."],
                ),
            ),
            class_="story-stack",
        ),
        "slide-scale",
    )


def section_host_snapshot() -> ui.Tag:
    return ui_slide(
        "03",
        "Executive overview",
        "Then locate the selected year",
        "The same filters now turn the global trend into a geographic hosting snapshot.",
        ui.div(
            story_row(
                chart_card("3", "Host geography", "Host countries by observed stock for the selected year", "host_map", "story-visual tall-map"),
                ui.div(ui.output_ui("executive_insight"), class_="explain-card"),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-host-snapshot",
    )


def section_host_map_scene() -> ui.Tag:
    return ui_slide(
        "05",
        "Spatial view",
        "Where is hosting concentrated?",
        "This scene gives the host-country map enough space to be read as geography, not decoration.",
        ui.div(
            story_row(
                chart_card("3A", "Host-country choropleth", "Map-eligible host countries; values are observed people", "host_map_large", "story-visual tall-map"),
                explain_card(
                    "Map purpose",
                    "Absolute hosting geography",
                    "The choropleth identifies where the selected displaced population is hosted. It is useful for concentration and regional-burden analysis.",
                    ["Values are observed people, not imputed totals.", "Map-eligible entities only are shown."],
                ),
            ),
            class_="story-stack",
        ),
        "slide-space-map",
    )


def section_pressure_scene() -> ui.Tag:
    return ui_slide(
        "06",
        "Spatial view",
        "Burden is not only raw totals",
        "A smaller host country can face greater proportional pressure than a larger country with a higher absolute stock.",
        ui.div(
            story_row(
                chart_card("3B", "Host burden ranking", "Host stock or per-capita pressure when available", "host_pressure_plot", "story-visual"),
                explain_card(
                    "Pressure reading",
                    "Compare scale with pressure",
                    "This chart supports the hosting-pressure research question by separating absolute stock from proportional burden.",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-pressure",
    )


def section_origin_rank_scene() -> ui.Tag:
    return ui_slide(
        "07",
        "Country rankings",
        "Where does displacement originate?",
        "Graph 5 identifies the countries that account for the largest selected displaced population stock.",
        ui.div(
            story_row(
                chart_card("5", "Top origin countries", "Countries producing the largest selected displaced populations", "graph5_plot", "story-visual rank-card"),
                explain_card(
                    "Research question 1",
                    "Ranked bars reveal concentration",
                    "The distribution is highly skewed, so a ranked bar chart is clearer than a pie chart for comparing origin countries.",
                ),
            ),
            class_="story-stack",
        ),
        "slide-origin-rank",
    )


def section_host_rank_scene() -> ui.Tag:
    return ui_slide(
        "08",
        "Country rankings",
        "Which countries host the largest populations?",
        "Graph 6 answers the host-country side of the core research question.",
        ui.div(
            story_row(
                chart_card("6", "Top host countries", "Countries hosting the largest selected displaced populations", "graph6_plot", "story-visual rank-card"),
                ui.div(ui.output_ui("ranking_note"), class_="explain-card"),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-host-rank",
    )


def section_crisis_routes_scene() -> ui.Tag:
    return ui_slide(
        "09",
        "Crisis case study",
        "Follow one crisis through its main routes",
        "The crisis route map focuses the story on destinations connected to the selected crisis origin.",
        ui.div(
            story_row(
                chart_card("7A", "Main migration routes", "Top host destinations from the selected crisis origin", "crisis_routes", "story-visual"),
                ui.div(ui.output_ui("crisis_timeline"), class_="timeline-panel explain-card"),
            ),
            class_="story-stack",
        ),
        "slide-crisis-routes",
    )


def section_crisis_hosts_scene() -> ui.Tag:
    return ui_slide(
        "10",
        "Crisis case study",
        "Then compare the top crisis hosts",
        "The ranking clarifies whether displacement remains regional or extends toward more distant host countries.",
        ui.div(
            story_row(
                chart_card("7B", "Top crisis host countries", "Ranked host destinations for the selected crisis and year", "crisis_hosts", "story-visual compact"),
                explain_card(
                    "Host concentration",
                    "Regional neighbours often absorb the first burden",
                    "Use this scene after the route map to compare host destinations without the geographic clutter.",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-crisis-hosts",
    )


def section_method_pipeline_scene() -> ui.Tag:
    return ui_slide(
        "11",
        "Method and reproducibility",
        "Why the dashboard is defensible",
        "The app reads cleaned and chart-ready data only, with raw CSV processing handled upstream.",
        ui.div(
            story_row(
                ui.div(ui.output_ui("method_cards"), class_="method-card"),
                explain_card(
                    "Pipeline",
                    "A reproducible data handoff",
                    "Preprocessing and EDA create stable chart-ready data for the dashboard, so the app itself is focused on interaction and storytelling.",
                ),
            ),
            class_="story-stack",
        ),
        "slide-method-pipeline",
    )


def section_quality_scene() -> ui.Tag:
    return ui_slide(
        "12",
        "Method and reproducibility",
        "Quality checks close the story",
        "The final scene documents the pipeline handoff and data-quality evidence behind the dashboard.",
        ui.div(
            story_row(
                ui.div(ui.output_ui("quality_cards"), class_="method-card"),
                ui.div(
                    ui.h3("Pipeline handoff"),
                    ui.tags.ol(
                        ui.tags.li("Six raw UNHCR-style CSV files are cleaned by 01_preprocessing.py."),
                        ui.tags.li("02_eda.py creates chart-ready tables in outputs/03_chart_data."),
                        ui.tags.li("app.py renders interactive views from cleaned/chart-ready data only."),
                        ui.tags.li("Graph 5/6 use population-stock data; asylum files remain flow datasets."),
                    ),
                    class_="explain-card",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-quality",
    )
