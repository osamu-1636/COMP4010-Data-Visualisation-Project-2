# Forced Migration Dashboard - Modular Python Shiny App

This is the professor-grade modular version of the Group 11 forced migration dashboard.
It follows a production-style architecture inspired by well-known PyShiny examples: small
modules, service-layer data loading, JSON-safe Plotly serialization, scroll-snap storytelling,
and a clean app handoff from preprocessing + EDA outputs.

## Architecture

```text
refugee_dashboard/
├── app.py
├── refugee_app/
│   ├── modules/
│   │   ├── hero.py
│   │   ├── filters.py
│   │   ├── map_flows.py
│   │   ├── sankey.py
│   │   ├── rankings.py
│   │   ├── storytelling.py
│   │   ├── analytics.py
│   │   └── method.py
│   ├── services/
│   │   ├── data_loader.py
│   │   ├── filters_state.py
│   │   ├── serializers.py
│   │   └── cache.py
│   ├── ui/
│   │   ├── theme.py
│   │   ├── layout.py
│   │   └── sections.py
│   └── www/
│       ├── styles.css
│       └── app.js
├── outputs/
│   ├── 01_clean/
│   └── 03_chart_data/
├── tests/
│   ├── test_smoke.py
│   ├── test_json_safety.py
│   └── test_data_contract.py
├── requirements.txt
└── README.md
```

The package uses `refugee_app/` rather than `app/` to avoid Python import ambiguity with `app.py`.

## Run on Windows PowerShell

```powershell
cd "D:\refugee_dashboard_modular_10_10"
py -m venv C:\venvs\comp4010-dashboard
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
C:\venvs\comp4010-dashboard\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python tests\test_smoke.py
python tests\test_json_safety.py
python tests\test_data_contract.py
python -m shiny run --launch-browser --port 8001 app.py
```

## Design contract

- The app does not read raw CSV files.
- The app reads cleaned data from `outputs/01_clean/` and chart-ready data from `outputs/03_chart_data/`.
- Parquet is preferred when available; CSV fallback is included for easy local reproducibility.
- Plotly figures are sanitized before Shiny serializes them, preventing `NaN is not JSON compliant` errors.
- Graph 5 and Graph 6 use population-stock data, not asylum-application flow data.

## Dashboard story

1. Executive overview
2. Spatial view
3. Movement structure
4. Graph 5 and Graph 6 rankings
5. Crisis storytelling
6. Analytical appendix
7. Method and reproducibility
