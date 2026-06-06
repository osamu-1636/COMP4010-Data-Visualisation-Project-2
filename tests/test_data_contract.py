from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_data_contract():
    meta = json.loads((ROOT / "outputs/03_chart_data/metadata.json").read_text(encoding="utf-8"))
    assert meta["data_contract"].startswith("Shiny app reads cleaned")
    assert "kpis" in meta["files"]
    assert "origin_rankings" in meta["files"]
    assert "host_rankings" in meta["files"]


if __name__ == "__main__":
    test_data_contract()
    print("DATA CONTRACT OK")
