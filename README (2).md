# Forced Migration Dashboard

This repository contains the final COMP4010 Project 2 dashboard for **Group 11**.

The dashboard tells a focused data story:

> **From crisis to corridor** — forced displacement begins as crisis pressure, grows into measurable scale, lands unevenly across host geographies, becomes visible through origin-host corridors, and can be analyzed through rankings, host concentration, distance structure, and a supervised ML baseline.

---

## 1. Project question

The dashboard answers:

1. **How large is the selected displaced population?**
2. **Where is hosting geographically concentrated?**
3. **Which origin-host corridors structure forced migration?**
4. **Which countries dominate origins and hosting?**
5. **Is hosting concentrated in one or two destination countries?**
6. **When crisis displacement happens, do people move near, regionally, or far?**
7. **Can historical corridor features predict where displaced populations move?**
8. **How does one crisis case translate the global pattern into a concrete story?**

---

## 2. Final dashboard story

The final presentation path is intentionally compact. It avoids repeated maps, repeated host bars, network clutter, and unstable heavy animation.

| Section | Purpose | Main evidence |
|---|---|---|
| **00 Cover** | Introduce the story | Code-driven cover visual |
| **01 Scale** | Establish magnitude and time context | KPI cards + displacement trend |
| **02 Host geography** | Show where hosting is spatially concentrated | One host choropleth |
| **03 Corridor evidence** | Connect geography with movement structure | Graph 1 flow map + Graph 4 Sankey |
| **04 Rankings** | Answer the core origin and host questions | Graph 5 top origins + Graph 6 top hosts |
| **05 Host concentration** | Show whether one host dominates | Treemap after Graph 6 |
| **06 Distance analytics and ML visualized** | Explain observed distance structure and predicted corridor response | Observed distance profile, ML pipeline, actual-vs-predicted distance mix, top predicted hosts, similarity explorer |
| **07 Crisis case** | Turn the global pattern into one humanitarian case | Crisis route map + crisis timeline/host ranking |
| **08 Method** | Explain data contract, architecture, and reproducibility | Method and pipeline notes |

---

## 3. Repository architecture

```text
COMP4010-Data-Visualisation-Project-2/
├── app.py
├── refugee_app/
│   ├── modules/
│   │   ├── hero.py
│   │   ├── map_flows.py
│   │   ├── sankey.py
│   │   ├── rankings.py
│   │   ├── storytelling.py
│   │   ├── advanced_viz.py
│   │   ├── ml_visualized.py
│   │   └── method.py
│   ├── services/
│   │   ├── data_loader.py
│   │   ├── filters_state.py
│   │   ├── serializers.py
│   │   └── cache.py
│   ├── ui/
│   │   ├── layout.py
│   │   ├── sections.py
│   │   └── theme.py
│   └── www/
│       ├── styles.css
│       └── app.js
├── outputs/
│   ├── 00_audit/
│   ├── 01_clean/
│   └── 03_chart_data/
├── scripts/
├── tests/
│   ├── test_smoke.py
│   ├── test_json_safety.py
│   └── test_data_contract.py
├── requirements.txt
└── README.md
```

The app uses `refugee_app/` instead of a folder named `app/` to avoid Python import ambiguity with `app.py`.

---

## 4. What is preserved from the GitHub base

The final dashboard keeps the improved GitHub architecture:

- `app.py` remains a thin entry point.
- `refugee_app/services/` handles data loading, filtering state, caching, and Plotly JSON safety.
- `refugee_app/modules/` separates maps, rankings, Sankey, storytelling, advanced analytics, ML visualization, and method outputs.
- `refugee_app/ui/` owns the layout, scroll-based story sections, and presentation shell.
- `outputs/` provides the cleaned/chart-ready data handoff.
- `tests/` checks smoke behavior, JSON safety, and data contract assumptions.

This separation is intentional: the Shiny app is the presentation layer, not the raw-data cleaning pipeline.

---

## 5. Runtime design contract

The dashboard follows these rules:

- The app reads **cleaned and chart-ready outputs only**.
- The app does **not** read raw UNHCR CSV files during live Shiny runtime.
- Graph 5 and Graph 6 use **population-stock** data, not asylum-application flow data.
- The default scope is cross-border displacement; IDPs are handled separately because they are internal displacement, not host-country reception.
- The crisis filter is a **case/origin focus filter**, not a full crisis-period time-span filter.
- Heavy Plotly frame animation, WebGL/PyDeck iframes, and cluttered network graphs are avoided in the final presentation path.

---

## 6. Interactivity

The top control bar includes:

- **Year** — selects the year snapshot.
- **Crisis focus** — maps a named crisis to its origin country.
- **Origin** — manually selects an origin country.
- **Destination** — manually selects a host/destination country.
- **Population scope** — selects cross-border or active forced-displacement categories.
- **Top N** — controls how many ranked countries/corridors are shown.
- **Apply** — commits the selected filter state and reduces unnecessary rerenders.
- **Reset** — returns to the default story view.

### Crisis filter behavior

The crisis filter does **not** automatically apply a start/end time span. It focuses the selected crisis by origin country:

```text
Syrian Civil War           -> Syrian Arab Republic
Afghanistan displacement   -> Afghanistan
South Sudan crisis         -> South Sudan
Iraq conflict              -> Iraq
Somalia crisis             -> Somalia
```

The **year slider** still controls the temporal snapshot.

---

## 7. Visualization design

The final dashboard uses multiple chart types without turning the project into a chart gallery:

| Chart type | Use |
|---|---|
| KPI cards | Quick scale summary |
| Line chart | Displacement trend over time |
| Choropleth map | Host geography |
| Flow map | Origin-host corridors |
| Sankey | Origin → host/asylum country → population status |
| Horizontal ranked bars | Graph 5 and Graph 6 |
| Treemap | Host concentration after Graph 6 |
| Stacked area chart | Observed near/regional/far distance mix |
| Grouped bar chart | Actual vs ML-predicted distance mix |
| Similarity scatter | Corridor similarity explorer |

---

## 8. ML / analytics component

The final ML section is not just a distance chart. It visualizes a full supervised baseline.

### ML question

> Can historical origin-host-year corridor features predict where displaced populations move?

### Prediction task

For each origin-host-year corridor, predict:

```text
target = log(1 + refugee_count)
```

### Model

```text
RandomForestRegressor
```

### Features

```text
year
distance_km
distance_band
previous_year_flow
origin_total_previous_year
host_total_previous_year
```

### Outputs shown in the dashboard

1. **Observed distance-band profile**  
   Actual near/regional/far shares over time.

2. **ML pipeline card**  
   Features → RandomForestRegressor → log target → predicted destination/distance mix.

3. **Actual vs ML-predicted distance mix**  
   Compares observed and predicted near/regional/far shares for the selected year.

4. **Top predicted host destinations**  
   Shows actual vs predicted host-country flow for the selected context.

5. **Corridor similarity explorer**  
   Uses corridor feature vectors and a 2D projection to show which origin-host-year corridors are structurally similar.

6. **Model diagnostics**  
   Train rows, test rows, MAE on log target, R², tree-ensemble uncertainty interval, and feature importance.

### Interpretation

This model predicts **corridor response**, not war.

It should be explained as:

> A supervised predictive baseline for corridor-flow strength using historical origin-host-year features. It is not a causal war forecasting model.

---

## 9. Run on Windows PowerShell

From the repository root:

```powershell
cd "D:\COMP4010-Data-Visualisation-Project-2"

py -m venv .venv

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

python tests\test_smoke.py

python tests\test_json_safety.py

python tests\test_data_contract.py

python -m shiny run --launch-browser --port 8050 app.py
```

Open:

```text
http://127.0.0.1:8050
```

If Chrome caches old Shiny assets, use:

```text
Ctrl + Shift + R
```

or open an incognito window.

---

## 10. Test checklist before demo

Run:

```powershell
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
python -m py_compile app.py
```

Then manually check:

- Reset button.
- Apply button.
- Year slider.
- Crisis focus selector.
- Graph 1 flow map.
- Graph 4 Sankey.
- Graph 5 and Graph 6.
- Treemap.
- ML section.
- Crisis case section.
- Method section.

---

## 11. Recommended demo script

Use this sequence:

1. **Cover** — “The story is from crisis to corridor.”
2. **Scale** — “First we establish magnitude and time context.”
3. **Host geography** — “Then we ask where hosting is concentrated.”
4. **Corridors** — “The map shows where routes go; the Sankey shows structure.”
5. **Rankings** — “Graph 5 and Graph 6 answer the core origin and host questions.”
6. **Treemap** — “Graph 6 gives exact rank; treemap shows concentration.”
7. **ML visualized** — “We predict corridor response, not war.”
8. **Crisis case** — “One crisis turns the global pattern into a concrete story.”
9. **Method** — “The app reads cleaned/chart-ready data and keeps preprocessing upstream.”

Short ML explanation:

> We engineer corridor features such as distance, previous-year flow, origin pressure, host pressure, and year. A RandomForestRegressor predicts log(1 + refugee count). We aggregate predicted flows into near, regional, and far distance bands and compare them with observed shares.

---

## 12. Limitations

- Country centroids are approximate and used for dashboard-level spatial analytics, not official geodesic measurement.
- The ML model is a predictive baseline, not a causal model.
- The crisis filter focuses origin country; it does not enforce crisis start/end spans.
- Prediction quality depends on historical corridor coverage and the cleaned data available in `outputs/`.
- The dashboard prioritizes stable live demo behavior over heavy animation or complex WebGL scenes.

---

## 13. Final submission note

For final presentation, use the dashboard as a story, not as a list of charts:

```text
Scale
→ Geography
→ Corridors
→ Rankings
→ Host concentration
→ ML visualized
→ Crisis case
→ Method
```

This version is designed to be reproducible, rubric-aligned, and explainable to both technical and non-technical viewers.
