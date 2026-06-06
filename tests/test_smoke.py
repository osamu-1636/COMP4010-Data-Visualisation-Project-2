from __future__ import annotations

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "app.py",
    "refugee_app/modules/hero.py",
    "refugee_app/modules/filters.py",  # optional facade, checked below with fallback
    "refugee_app/modules/map_flows.py",
    "refugee_app/modules/sankey.py",
    "refugee_app/modules/rankings.py",
    "refugee_app/modules/storytelling.py",
    "refugee_app/services/data_loader.py",
    "refugee_app/services/filters_state.py",
    "refugee_app/services/serializers.py",
    "refugee_app/services/cache.py",
    "refugee_app/ui/theme.py",
    "refugee_app/ui/layout.py",
    "refugee_app/ui/sections.py",
    "refugee_app/www/styles.css",
    "refugee_app/www/app.js",
    "outputs/03_chart_data/metadata.json",
    "outputs/03_chart_data/stock.parquet",
]


def test_smoke():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    assert not missing, f"Missing files: {missing}"
    for p in ROOT.rglob("*.py"):
        if ".venv" not in p.parts and "__pycache__" not in p.parts:
            py_compile.compile(str(p), doraise=True)


if __name__ == "__main__":
    test_smoke()
    print("SMOKE TEST OK - modular app files and syntax are valid")
