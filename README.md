# Forced Migration Dashboard — Hybrid Excellent Final

This folder is the final merged codebase for the COMP4010 Project 2 forced migration dashboard.
It preserves the clean modular GitHub architecture and adds only the final selected rubric-facing improvements.

## Final story

**From crisis to corridor**

1. **Scale** — KPI cards and displacement trend establish magnitude.
2. **Host geography** — one choropleth shows where hosting is concentrated.
3. **Corridor evidence** — Graph 1 flow map + Graph 4 Sankey connect geography with route structure.
4. **Rankings** — Graph 5 and Graph 6 answer the top-origin and top-host questions.
5. **Host concentration** — treemap after Graph 6 shows whether one host dominates.
6. **Distance analytics** — stacked area chart answers whether refugees move near, regionally, or far.
7. **Crisis case** — selected crisis turns the global pattern into a concrete humanitarian story.
8. **Method** — preprocessing, EDA, and reproducibility handoff.

## What is preserved from the GitHub base

- Thin `app.py` entry point.
- `refugee_app/services/` data loading, caching, filtering and JSON safety.
- `refugee_app/modules/` separation for hero, maps, rankings, Sankey, storytelling, analytics and method.
- `refugee_app/ui/` layout/sections separation.
- Clean handoff from preprocessing/EDA outputs.
- Tests for smoke, JSON safety and data contract.

## What is added from the final dashboard work

- Graph 4 Sankey is active and shown next to Graph 1.
- Treemap is placed after Graph 6 to show host concentration without repeating another host bar chart.
- Distance-band analytics computes haversine origin-host distance and bins corridors into near/regional/far.
- Route maps have lightweight moving dots via client-side Plotly `restyle`; no Plotly frames are used.
- Cover SVG has lightweight motion for storytelling.
- Top filters use an Apply button so expensive charts rerender only after the presenter commits the filter state.

## Runtime design contract

- The Shiny app reads cleaned/chart-ready outputs only.
- The app does **not** read raw CSV files during live runtime.
- Graph 5 and Graph 6 use population-stock data, not asylum-application flow data.
- Distance analytics is a spatial analytics / feature-engineering layer, not a causal ML prediction model.
- The final UI avoids repeated host maps, repeated host bars, network clutter and heavy Plotly frame animation.

## Run on Windows PowerShell

```powershell
cd "D:\refugee_dashboard_hybrid_excellent_final_v2"
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

If Chrome caches old Shiny assets, use `Ctrl+Shift+R` or an incognito tab.

## Recommended demo path

Use sections 00–08 in order. If time is short, skip the Method slide during live demo and mention it in Q&A/report.

## Short explanation for analytics

The distance-band chart answers: **when crisis displacement happens, do refugees move near, regionally, or far?**
For each origin-host corridor, the app computes centroid distance using the haversine formula and groups displacement into distance bands. This is a defensible spatial analytics layer and a baseline for later predictive modeling, but it is not a full ML model by itself.
