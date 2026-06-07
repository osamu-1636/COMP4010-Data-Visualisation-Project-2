"""Final excellent-rubric scroll-snap sections.

Design principle: fewer repeated views, clearer purpose per section.
Final story: Scale -> Geography -> Corridors -> Rankings -> Concentration -> Distance analytics -> Crisis -> Method.
"""
from __future__ import annotations

from shiny import ui
from shinywidgets import output_widget

from refugee_app.constants import BLUE, GREEN, ORANGE, PURPLE


def globe_svg() -> ui.Tag:
    return ui.HTML("""
    <svg class='globe-icon' viewBox='0 0 100 100' aria-hidden='true'>
      <circle cx='50' cy='50' r='44' fill='#e8f2fb' stroke='#111827' stroke-width='3.6'/>
      <path d='M21 36 C35 18 59 22 75 32 C60 38 62 49 71 59 C58 65 44 55 32 66 C28 55 13 51 21 36Z' fill='#9fc7e5' stroke='#111827' stroke-width='1.5'/>
      <path d='M10 50 H90 M50 6 C25 26 25 74 50 94 M50 6 C75 26 75 74 50 94' fill='none' stroke='#111827' stroke-width='2' opacity='.56'/>
    </svg>
    """)


def cover_sketch() -> ui.Tag:
    return ui.HTML("""
    <svg class='cover-sketch' viewBox='0 0 1180 660' role='img' aria-label='Refugee corridor atlas sketch'>
      <rect x='8' y='8' width='1164' height='644' rx='34' fill='#fffdf8' stroke='#111827' stroke-width='4'/>
      <g opacity='.16' stroke='#111827' stroke-width='2' fill='none'>
        <path d='M150 260 C230 190 310 205 390 150 C500 75 615 110 720 95 C825 80 925 95 1030 60'/>
        <path d='M120 395 C245 360 345 405 465 365 C575 330 675 350 760 310 C850 270 945 305 1060 250'/>
        <path d='M205 515 C310 465 420 500 535 458 C660 410 785 445 950 370'/>
      </g>
      <g stroke-linecap='round' fill='none'>
        <path id='cover-route-orange' class='sketch-route route-orange' d='M230 460 C380 410 455 470 585 420 C705 372 815 398 945 315'/>
        <path id='cover-route-blue' class='sketch-route route-blue' d='M260 255 C390 180 480 210 610 290 C720 360 830 355 945 315'/>
        <path id='cover-route-green' class='sketch-route route-green' d='M445 185 C515 260 560 330 625 410 C705 490 805 505 930 555'/>
        <path id='cover-route-purple' class='sketch-route route-purple' d='M310 510 C430 455 520 515 650 470 C760 430 820 470 900 445'/>
      </g>
      <g>
        <circle cx='230' cy='460' r='14' fill='#d45745' stroke='white' stroke-width='4'/>
        <circle cx='585' cy='420' r='10' fill='#111827' stroke='white' stroke-width='3'/>
        <circle cx='945' cy='315' r='14' fill='#6f9166' stroke='white' stroke-width='4'/>
        <circle cx='260' cy='255' r='14' fill='#d45745' stroke='white' stroke-width='4'/>
        <circle cx='610' cy='290' r='10' fill='#111827' stroke='white' stroke-width='3'/>
        <circle cx='930' cy='555' r='14' fill='#6f9166' stroke='white' stroke-width='4'/>
      </g>
      <g class='sketch-label'>
        <text x='72' y='88'>FROM CRISIS TO CORRIDOR</text>
        <text x='72' y='126' class='small'>Scale, host geography, corridor structure, rankings and distance analytics</text>
        <text x='72' y='594' class='tiny'>Red = crisis origin | Green = host destination | Line width = corridor magnitude</text>
      </g>
    
      <g class='cover-motion-layer' aria-hidden='true'>
        <circle class='cover-moving-dot cover-dot-blue' r='8'>
          <animateMotion dur='5.8s' repeatCount='indefinite' rotate='auto'>
            <mpath href='#cover-route-blue' xlink:href='#cover-route-blue'/>
          </animateMotion>
        </circle>
        <circle class='cover-moving-dot cover-dot-orange' r='8'>
          <animateMotion dur='6.4s' begin='.35s' repeatCount='indefinite' rotate='auto'>
            <mpath href='#cover-route-orange' xlink:href='#cover-route-orange'/>
          </animateMotion>
        </circle>
        <circle class='cover-moving-dot cover-dot-green' r='7'>
          <animateMotion dur='6.9s' begin='1.2s' repeatCount='indefinite' rotate='auto'>
            <mpath href='#cover-route-green' xlink:href='#cover-route-green'/>
          </animateMotion>
        </circle>
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
            ui.div(ui.div(title, class_="chart-title"), ui.div(subtitle, class_="chart-subtitle")),
            class_="chart-head",
        ),
        ui.div(output_widget(widget_id), class_="chart-body"),
        class_=f"chart-card {class_extra}".strip(),
    )


def explain_card(kicker: str, title: str, body: str, bullets: list[str] | None = None) -> ui.Tag:
    children: list[ui.Tag] = [ui.div(kicker, class_="explain-kicker"), ui.h3(title), ui.p(body)]
    if bullets:
        children.append(ui.tags.ul(*[ui.tags.li(b) for b in bullets]))
    return ui.div(*children, class_="explain-card")


def story_row(visual: ui.Tag, text: ui.Tag, reverse: bool = False) -> ui.Tag:
    return ui.div(text, visual, class_="story-row reverse") if reverse else ui.div(visual, text, class_="story-row")


def ui_slide(num: str, kicker: str, title: str, subtitle: str, content: ui.Tag, slide_id: str) -> ui.Tag:
    return ui.tags.section(
        ui.div(
            ui.div(
                ui.div(num, class_="slide-number"),
                ui.div(ui.div(kicker, class_="slide-kicker"), ui.h2(title), ui.p(subtitle)),
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
                    ui.div("GROUP 11 | UNHCR Refugee Data Finder / UNdata / HDX", class_="cover-kicker"),
                    ui.h1("From crisis to corridor"),
                    ui.h2("Visualizing forced migration as a data story"),
                    ui.p("A focused Python Shiny dashboard: displacement scale, host geography, corridor structure, country rankings, host concentration and distance analytics."),
                    ui.div(ui.span("Scale"), ui.span("Geography"), ui.span("Corridors"), ui.span("Rankings"), ui.span("Analytics"), class_="cover-tags"),
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


def section_scale() -> ui.Tag:
    return ui_slide(
        "01",
        "Shock becomes scale",
        "How large is the selected displacement system?",
        "The opening view establishes magnitude before the dashboard moves into geography and corridors.",
        ui.div(
            ui.div(
                metric_card("kpi_cross_border", "Cross-border scope", "CB", BLUE),
                metric_card("kpi_refugees", "Refugees", "R", GREEN),
                metric_card("kpi_idps", "Internally displaced", "IDP", ORANGE),
                metric_card("kpi_asylum", "Asylum-seekers", "A", PURPLE),
                metric_card("kpi_countries", "Countries & territories", "G", BLUE),
                class_="metric-grid",
            ),
            story_row(
                chart_card("2", "Displacement trend", "Observed population stock by year and population type", "trend_plot", "story-visual"),
                explain_card(
                    "Reading guide",
                    "Time shows whether the selected year is a spike or a plateau",
                    "The trend chart puts the selected year into historical context. It explains whether the dashboard is currently showing long-term displacement, a crisis spike, or a post-crisis plateau.",
                    ["Use the year and crisis filters to move from global scale to a focused case.", "Default scope is cross-border displacement; IDPs are shown separately in KPIs."],
                ),
            ),
            class_="story-stack",
        ),
        "slide-scale",
    )


def section_geography() -> ui.Tag:
    return ui_slide(
        "02",
        "Scale lands somewhere",
        "Where is hosting geographically concentrated?",
        "One spatial view is enough here: the host choropleth shows where the selected cross-border stock is located.",
        story_row(
            chart_card("3", "Host geography", "Map-eligible host countries; values are observed people", "host_map_large", "story-visual tall-map"),
            explain_card(
                "Map purpose",
                "Hosting is spatially uneven",
                "The choropleth reveals whether displacement remains regional or spreads globally. It avoids repeating multiple host maps in the main story.",
                ["Absolute values show scale.", "Graph 6 later gives exact host-country ranking."],
            ),
        ),
        "slide-geography",
    )


def section_flow() -> ui.Tag:
    return ui_slide(
        "03",
        "Geography becomes corridors",
        "How do origin-host routes become a movement system?",
        "The map preserves geography. The Sankey compresses the same route logic into a readable structure.",
        ui.div(
            ui.div(
                chart_card("1", "Global refugee flows", "Top origin to host corridors for the current selection", "flow_map", "story-visual flow-main compact-flow"),
                chart_card("4", "Origin to asylum country to status", "Sankey view of major corridors and population type", "sankey_plot", "story-visual sankey-card"),
                class_="dual-visual-row corridor-evidence-row",
            ),
            explain_card(
                "How to read this section",
                "The map shows where; the Sankey shows structure",
                "Graph 1 answers the geographic question: where do routes go? Graph 4 answers the structural question: which origins, hosts and status categories dominate the corridor system?",
                ["No third visual is added here; the section stays readable.", "Top N controls the complexity of both views."],
            ),
            class_="story-stack",
        ),
        "slide-flow",
    )


def section_rankings() -> ui.Tag:
    return ui_slide(
        "04",
        "Corridors have leaders",
        "Which countries dominate origins and hosting?",
        "Graph 5 and Graph 6 directly answer the two core ranking questions.",
        ui.div(
            story_row(
                chart_card("5", "Top origin countries", "Countries producing the largest selected displaced populations", "graph5_plot", "story-visual rank-card"),
                explain_card("Research question 1", "Where does displacement originate?", "Ranked bars are used because forced-displacement distributions are highly skewed. A few countries often account for a large share of the selected stock."),
            ),
            story_row(
                chart_card("6", "Top host countries", "Countries hosting the largest selected displaced populations", "graph6_plot", "story-visual rank-card"),
                ui.div(ui.output_ui("ranking_note"), class_="explain-card"),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-rankings",
    )


def section_treemap() -> ui.Tag:
    return ui_slide(
        "05",
        "Host concentration",
        "Does one host dominate the selected pattern?",
        "The treemap is placed after Graph 6 to show concentration by area rather than repeating another bar chart.",
        story_row(
            chart_card("6A", "Host concentration treemap", "Area encodes selected host-country stock", "host_treemap", "story-visual rank-card"),
            explain_card(
                "Why treemap?",
                "Concentration is easier to read by area",
                "Graph 6 gives precise rank order. The treemap complements it by showing whether the hosting pattern is dominated by one or two countries or spread across many destinations.",
                ["Adds a distinct chart type for the rubric.", "Useful for non-technical viewers."],
            ),
        ),
        "slide-treemap",
    )


def section_distance_analytics() -> ui.Tag:
    return ui_slide(
        "06",
        "Distance analytics and ML visualized",
        "Can historical corridor features predict where displaced populations move?",
        "This section shows observed movement structure, model learning, prediction output, host-destination ranking and corridor similarity.",
        ui.div(
            story_row(
                chart_card(
                    "6B",
                    "Observed distance-band profile",
                    "Actual near / regional / far share of corridor stock",
                    "ml_observed_distance_stack_plot",
                    "story-visual rank-card",
                ),
                explain_card(
                    "Observed pattern",
                    "First measure the distance structure",
                    "For every origin-host pair, the app computes centroid distance using the haversine formula and bins corridors into near, regional and far movement.",
                    [
                        "Near: < 1,000 km.",
                        "Regional: 1,000?3,000 km.",
                        "Far: > 3,000 km.",
                    ],
                ),
            ),
            ui.div(
                ui.output_ui("ml_pipeline_card"),
                class_="explain-card mlv-wide-card",
            ),
            story_row(
                chart_card(
                    "ML",
                    "Actual vs ML-predicted distance mix",
                    "RandomForest prediction aggregated into distance bands",
                    "ml_prediction_mix_plot",
                    "story-visual rank-card",
                ),
                explain_card(
                    "Prediction check",
                    "Can the model reproduce movement structure?",
                    "The model predicts log(1 + corridor flow) for origin-host-year corridors. Predicted flows are then aggregated into near, regional and far bands.",
                    [
                        "This is supervised prediction, not causal war forecasting.",
                        "Features include distance, year and lagged corridor pressure.",
                        "Uncertainty is approximated from the tree ensemble.",
                    ],
                ),
            ),
            story_row(
                chart_card(
                    "ML-D",
                    "Top predicted host destinations",
                    "Actual vs model-predicted host country flow",
                    "ml_top_destination_plot",
                    "story-visual rank-card",
                ),
                explain_card(
                    "Destination ranking",
                    "A recommender-style view of refugee corridors",
                    "This visual reframes the model as a destination recommender: given an origin-year context, which host countries are expected to receive the largest corridor flows?",
                ),
                reverse=True,
            ),
            story_row(
                chart_card(
                    "ML-S",
                    "Corridor similarity explorer",
                    "Similar origin-host-year corridors appear close together",
                    "ml_similarity_plot",
                    "story-visual rank-card",
                ),
                explain_card(
                    "Distance-based exploration",
                    "Similar corridors cluster together",
                    "Each point is a corridor-year feature vector. The 2D embedding helps reveal whether selected crisis corridors resemble near, regional or far historical movement patterns.",
                ),
            ),
            class_="story-stack mlv-section-stack",
        ),
        "slide-distance",
    )


def section_crisis() -> ui.Tag:
    return ui_slide(
        "07",
        "One crisis, concrete evidence",
        "How does a crisis create routes and host pressure?",
        "The crisis case study connects the global pattern to a specific humanitarian story.",
        ui.div(
            story_row(
                chart_card("7A", "Crisis routes", "Top host destinations from the selected crisis origin", "crisis_routes", "story-visual"),
                ui.div(ui.output_ui("crisis_timeline"), class_="timeline-panel explain-card"),
            ),
            story_row(
                chart_card("7B", "Top crisis host countries", "Ranked host destinations for the selected crisis and year", "crisis_hosts", "story-visual compact"),
                explain_card("Host concentration", "Regional neighbours often absorb the first burden", "This ranking clarifies whether the selected crisis remains regional or extends toward more distant host countries."),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-crisis",
    )


def section_method() -> ui.Tag:
    return ui_slide(
        "08",
        "Method and reproducibility",
        "Why the dashboard is defensible",
        "The app reads cleaned and chart-ready data only; raw CSV files are handled upstream by preprocessing and EDA.",
        ui.div(
            story_row(
                ui.div(ui.output_ui("method_cards"), class_="method-card"),
                explain_card("Pipeline", "A reproducible data handoff", "The Shiny app is a presentation layer over cleaned/chart-ready outputs. This supports stable demo behavior and explains the stock-vs-flow distinction."),
            ),
            story_row(
                ui.div(ui.output_ui("quality_cards"), class_="method-card"),
                ui.div(
                    ui.h3("What to say in the demo"),
                    ui.tags.ol(
                        ui.tags.li("Graph 5/6 use population-stock data."),
                        ui.tags.li("Asylum datasets support application-flow analysis, not stock rankings."),
                        ui.tags.li("Distance bands are analytical features, not causal predictions."),
                        ui.tags.li("The app is modular and reads outputs from preprocessing + EDA."),
                    ),
                    class_="explain-card",
                ),
                reverse=True,
            ),
            class_="story-stack",
        ),
        "slide-method",
    )
