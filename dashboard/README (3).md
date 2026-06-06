# Forced Migration Dashboard — COMP4010 Project 2

**Group 11 — Forced Migration / Refugee Flow Dashboard**  
**Main story:** *From crisis to corridor*

This repository contains the final Python Shiny dashboard for COMP4010 Project 2. The dashboard visualizes global forced-migration patterns using cleaned UNHCR-style displacement data and a modular Python Shiny architecture. It is designed as an interactive data story rather than a gallery of charts: users move from global scale, to host geography, to origin-host corridors, to country rankings, to a crisis case study, and finally to an ML visual analytics section.

The final design is based on the improved modular GitHub codebase and selected final dashboard additions: Graph 4 Sankey, treemap host concentration, distance analytics, and a supervised ML baseline for corridor-flow prediction.

---

## 1. Project question

Forced displacement is difficult to understand because it combines time, geography, origin-host country relationships, population categories, and highly skewed counts.

This dashboard answers:

> **How does forced migration evolve from crisis pressure into observable global origin-host corridors, and can historical corridor features help predict where displaced populations move?**

The dashboard focuses on four analytical questions:

1. **Scale:** How large is the selected displacement system?
2. **Geography:** Where are displaced populations hosted?
3. **Corridors:** Which origin-host routes organize displacement?
4. **Prediction / analytics:** Can historical corridor features predict destination pressure and near/regional/far movement patterns?

---

## 2. Final dashboard story

The final UI is intentionally concise. It avoids repeated host maps, repeated bar charts, network clutter, and unstable heavy animation.

```text
00 Cover
01 Scale
02 Host geography
03 Corridor evidence
04 Country rankings
05 Host concentration
06 Distance analytics and ML visualized
07 Crisis case study
08 Method and reproducibility
```

| Section | Dashboard component | Purpose |
|---|---|---|
| **00 Cover** | Animated SVG movement story | Introduces the “crisis → corridor” narrative. |
| **01 Scale** | KPI cards + displacement trend | Establishes magnitude and time context. |
| **02 Host geography** | Host-country choropleth | Shows where displaced populations are hosted. |
| **03 Corridor evidence** | Graph 1 flow map + Graph 4 Sankey | Connects geography with origin-host-status route structure. |
| **04 Country rankings** | Graph 5 top origins + Graph 6 top hosts | Answers the core country-ranking research questions. |
| **05 Host concentration** | Treemap after Graph 6 | Shows whether hosting is dominated by one or a few countries. |
| **06 Distance analytics and ML visualized** | Observed distance profile, actual-vs-predicted mix, top predicted hosts, similarity explorer, model cards | Embeds a predictive ML workflow into the visual analytics story. |
| **07 Crisis case study** | Crisis route map + crisis host ranking | Converts the global pattern into one concrete humanitarian case. |
| **08 Method and reproducibility** | Pipeline, data contract, quality notes | Explains why the dashboard is technically defensible. |

---

## 3. Repository architecture

```text
refugee_dashboard/
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
│   ├── 03_chart_data/
│   └── 07_report_assets/
├── scripts/
│   ├── 01_preprocessing.py
│   ├── 02_eda.py
│   └── 03_graphs.py
├── tests/
│   ├── test_smoke.py
│   ├── test_json_safety.py
│   └── test_data_contract.py
├── requirements.txt
└── README.md
```

The package uses `refugee_app/` rather than `app/` to avoid Python import ambiguity with `app.py`.

---

## 4. What is preserved from the GitHub base

The final app keeps the strongest parts of the GitHub codebase:

- Thin `app.py` entry point.
- Modular `refugee_app/modules/` structure.
- Service-layer data loading, caching, filtering, and JSON-safe Plotly serialization.
- `refugee_app/ui/` separation for layout and sections.
- Clean handoff from preprocessing + EDA outputs.
- Tests for smoke, JSON safety, and data contract.
- Apply-button filter state to reduce unnecessary reactivity and improve demo stability.

The final app does **not** return to a single-file `shiny_.py` structure. The single-file prototype was useful for visual inspiration, but the final submission uses a modular architecture for reproducibility and maintainability.

---

## 5. Runtime design contract

The dashboard follows this runtime contract:

- The Shiny app reads **cleaned/chart-ready outputs only**.
- The app does **not** read raw CSV files during live runtime.
- Parquet is preferred when available; CSV fallback is included for local reproducibility.
- Plotly figures are sanitized before Shiny serializes them.
- Graph 5 and Graph 6 use **population-stock data**, not asylum-application flow data.
- IDPs are not mixed into the default cross-border host ranking.
- Heavy Plotly frame animation and WebGL/iframe experiments are excluded from the final UI.
- Route motion is limited to lightweight client-side movement on flow maps, not full Plotly frame animation.

---

## 6. Data pipeline

The app expects the preprocessing and EDA scripts to produce cleaned and chart-ready files.

```text
raw UNHCR-style CSV files
→ scripts/01_preprocessing.py
→ outputs/01_clean/
→ scripts/02_eda.py
→ outputs/03_chart_data/
→ Python Shiny dashboard
```

Core expected outputs include:

```text
outputs/01_clean/time_series_clean.csv.gz
outputs/03_chart_data/stock.parquet
outputs/03_chart_data/trends.parquet
outputs/03_chart_data/top_origin_host_corridors.csv
outputs/03_chart_data/sankey_top_corridors.csv
outputs/03_chart_data/graph5_top_origin_countries.csv
outputs/03_chart_data/graph6_top_host_countries.csv
outputs/03_chart_data/choropleth_host_latest.csv
outputs/03_chart_data/forecast_global_active_forced_displacement.csv
```

---

## 7. Visualizations

The dashboard includes more than five charts and more than three chart types.

| Chart / component | Chart type | Analytical role |
|---|---|---|
| KPI cards | summary cards | Scale overview |
| Displacement trend | line chart | Time-series context |
| Host geography | choropleth map | Spatial distribution |
| Graph 1 flow map | origin-host flow map | Geographic corridors |
| Graph 4 Sankey | Sankey diagram | Origin → host → status structure |
| Graph 5 top origins | horizontal bar chart | Main origin-country research question |
| Graph 6 top hosts | horizontal bar chart | Main host-country research question |
| Host concentration | treemap | Concentration after Graph 6 |
| Observed distance profile | stacked area chart | Near / regional / far movement structure |
| ML predicted distance mix | grouped bar chart | Actual vs predicted distance structure |
| Top predicted hosts | grouped horizontal bar chart | Destination prediction / recommender-style view |
| Corridor similarity explorer | scatter plot / embedding | Distance-based ML exploration |
| Crisis case study | route map + bar chart | Focused humanitarian narrative |

---

## 8. Interactivity

Global filters:

- **Year**
- **Crisis**
- **Origin**
- **Destination / host**
- **Population scope**
- **Top N**
- **Apply**
- **Reset**

Design choice:

- Filters do not trigger every graph immediately.
- The app uses an **Apply** button to update the applied state.
- This reduces redundant recomputation and makes the live demo smoother.

---

## 9. ML / analytics section

### 9.1 ML question

> **Can historical corridor features predict where displaced populations move?**

The ML task is not “predict war.” It is a **corridor-response prediction** problem.

### 9.2 Model

```text
Model: RandomForestRegressor
Target: log(1 + corridor refugee count)
Unit of observation: origin-host-year corridor
```

### 9.3 Features

The model uses historical and spatial corridor features:

```text
year
distance_km
distance_band
previous_year_flow
origin_total_previous_year
host_total_previous_year
```

### 9.4 Outputs visualized in the dashboard

The ML section is presented in an “ML visualized” style: the dashboard shows the pipeline, not only a metric.

```text
1. Observed near / regional / far distance-band profile
2. ML pipeline card: features → model → target → output
3. Actual vs ML-predicted distance mix
4. Top predicted host destinations vs actual observed
5. Corridor similarity explorer using PCA on engineered corridor features
6. Train/test metrics: MAE on log target and R²
7. Feature importance
8. Uncertainty approximation from tree-level RandomForest predictions
```

### 9.5 Interpretation

The model is a **supervised predictive baseline**, not a causal conflict model.

Use this wording in presentation:

> The model predicts corridor response, not war. It estimates corridor-flow strength from historical origin-host features, then aggregates predicted flows into near, regional, and far movement bands.

---

## 10. Running the dashboard on Windows PowerShell

Run from the dashboard folder containing `app.py`.

```powershell
cd "D:\refugee_dashboard"

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

If Chrome caches old Shiny assets:

```text
Ctrl + Shift + R
```

or use an incognito tab:

```text
Ctrl + Shift + N
```

---

## 11. Tests

Run before final presentation:

```powershell
python -m py_compile app.py
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
```

Expected:

```text
SMOKE TEST OK
JSON SAFETY OK
DATA CONTRACT OK
```

---

## 12. Recommended demo path

For an eight-minute presentation:

```text
0:00–0:45  Problem and story
0:45–1:30  Scale / displacement trend
1:30–2:15  Host geography
2:15–3:30  Flow map + Sankey
3:30–4:30  Graph 5 + Graph 6
4:30–5:10  Treemap / host concentration
5:10–6:40  ML visualized section
6:40–7:30  Crisis case study
7:30–8:00  Method and reproducibility
```

If time is short, skip the Method slide during live demo and mention it during Q&A or in the report.

---

## 13. Presentation script

Use this opening:

> This dashboard tells one story: forced displacement begins as crisis pressure, grows into scale, lands unevenly across host geographies, forms origin-host corridors, and can be analyzed through rankings, concentration, distance structure, and predictive corridor response.

For the ML section:

> This section follows an ML-visualized approach. We first show the observed near/regional/far movement pattern. Then we expose the model pipeline: engineered features, RandomForestRegressor, target variable, prediction output, feature importance and validation metrics. The model predicts log-transformed corridor flow, not war itself.

For limitations:

> The model is a baseline. It does not use external conflict-event data such as ACLED or UCDP, and it does not make causal claims. It predicts corridor response from historical corridor patterns.

---

## 14. Rubric alignment

| Rubric area | How this dashboard addresses it |
|---|---|
| Visualization quality | Scroll-based story, clean layout, purposeful charts, no repeated host maps. |
| Chart requirements | More than 5 charts and more than 3 chart types. |
| Interactivity | Year, crisis, origin, host, population scope, Top N, Apply, Reset, hover tooltips. |
| Technical complexity | Clean data pipeline, spatial maps, flow map, Sankey, treemap, ML feature engineering, similarity explorer. |
| ML / analytics | RandomForestRegressor corridor-flow prediction, actual-vs-predicted distance mix, feature importance, similarity explorer. |
| Proper Python Shiny | Thin `app.py`, modular server registration, service-layer state/filtering. |
| Reproducibility | README, pinned requirements, tests, cleaned/chart-ready data handoff. |
| Repository organization | Code, services, UI, outputs, scripts and tests are separated. |
| Presentation | Demo path and explanation scripts are included. |

---

## 15. Final notes

Do not describe the model as predicting war.  
Do describe it as:

```text
a supervised corridor-response baseline
```

Do not claim the distance bands are individual-level movement.  
Do describe them as:

```text
country-centroid based origin-host corridor distance categories
```

Do not show every auxiliary chart during the live demo.  
Prioritize:

```text
Scale → Geography → Flow + Sankey → Rankings → ML visualized → Crisis case
```
