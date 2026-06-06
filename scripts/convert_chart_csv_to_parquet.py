from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "outputs" / "03_chart_data"

ALIASES = {
    "kpis.csv": "kpis.parquet",
    "trends.csv": "trends.parquet",
    "host_rankings.csv": "host_rankings.parquet",
    "origin_rankings.csv": "origin_rankings.parquet",
    "sankey_links.csv": "sankey_links.parquet",
    "choropleth.csv": "choropleth.parquet",
    "corridors.csv": "corridors.parquet",
    "animated_host_map.csv": "animated_host_map.parquet",
    "role_scatter.csv": "role_scatter.parquet",
    "host_pressure.csv": "host_pressure.parquet",
}

for csv_name, parquet_name in ALIASES.items():
    p = CHART / csv_name
    if p.exists():
        df = pd.read_csv(p, low_memory=False)
        df.to_parquet(CHART / parquet_name, index=False)
        print(f"wrote {parquet_name}")
print("Parquet conversion complete")
