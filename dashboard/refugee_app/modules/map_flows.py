"""Spatial and corridor outputs for the excellent-rubric dashboard."""
from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs
from shinywidgets import render_widget

from refugee_app.constants import BLUE, CENTROIDS, GREEN, ORANGE, RED
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, build_corridors
from refugee_app.services.serializers import safe_fig

Point = Tuple[float, float]
MAP_BG = "#fffdf8"
LAND = "#f7f2e9"
OCEAN = "#fffdf8"
BORDER = "#b8c0c8"


def _is_finite(x: object) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _base_geo() -> dict:
    return {
        "projection_type": "natural earth",
        "showland": True,
        "landcolor": LAND,
        "showocean": True,
        "oceancolor": OCEAN,
        "showcountries": True,
        "countrycolor": BORDER,
        "showcoastlines": True,
        "coastlinecolor": BORDER,
        "showframe": False,
        "bgcolor": MAP_BG,
    }


def _focus_geo(points: Sequence[Point], *, global_when_wide: bool = True) -> dict:
    clean = [(float(a), float(b)) for a, b in points if _is_finite(a) and _is_finite(b)]
    geo = _base_geo()
    if len(clean) < 2:
        return geo
    lats = [p[0] for p in clean]
    lons = [p[1] for p in clean]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    lat_span = max(lat_max - lat_min, 8.0)
    lon_span = max(lon_max - lon_min, 12.0)
    if global_when_wide and (lon_span > 165 or lat_span > 125):
        return geo
    lat_pad = max(4.5, lat_span * 0.34)
    lon_pad = max(7.0, lon_span * 0.34)
    geo.update(
        {
            "lataxis_range": [max(-60, lat_min - lat_pad), min(82, lat_max + lat_pad)],
            "lonaxis_range": [max(-179, lon_min - lon_pad), min(179, lon_max + lon_pad)],
        }
    )
    return geo


def _curved_line(lat1: float, lon1: float, lat2: float, lon2: float, steps: int = 44) -> tuple[list[float], list[float]]:
    t = np.linspace(0, 1, steps)
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lats = lat1 + (lat2 - lat1) * t
    lons = lon1 + (lon2 - lon1) * t
    bend = math.sin((lon2 - lon1) * math.pi / 180.0) * 3.0
    lats = lats + bend * np.sin(np.pi * t)
    return lats.tolist(), lons.tolist()


def make_route_map_figure(corridors: pd.DataFrame, *, height: int = 600, max_routes: int = 12, route_color: str = BLUE, **_: object) -> go.Figure:
    if corridors is None or corridors.empty:
        return empty_fig("No origin-host corridors for this selection", height)
    required = {"origin_country_std", "host_country_std", "value_observed"}
    if not required.issubset(corridors.columns):
        return empty_fig("Route data is missing required columns", height)

    d = corridors.copy()
    d = d[d["value_observed"].fillna(0) > 0]
    d = d.sort_values("value_observed", ascending=False).head(int(max_routes)).reset_index(drop=True)
    if d.empty:
        return empty_fig("No positive corridor values for this selection", height)

    maxv = max(float(d["value_observed"].max()), 1.0)
    fig = go.Figure()
    focus_points: list[Point] = []
    origins_seen: set[str] = set()
    host_lats: list[float] = []
    host_lons: list[float] = []
    host_names: list[str] = []
    host_values: list[float] = []

    for i, (_, r) in enumerate(d.iterrows()):
        origin = str(r["origin_country_std"])
        host = str(r["host_country_std"])
        if origin not in CENTROIDS or host not in CENTROIDS:
            continue
        lat1, lon1 = CENTROIDS[origin]
        lat2, lon2 = CENTROIDS[host]
        value = float(r["value_observed"])
        rel = value / maxv if maxv else 0.0
        lats, lons = _curved_line(lat1, lon1, lat2, lon2)
        color = ORANGE if i == 0 else route_color
        opacity = 0.88 if i == 0 else 0.32
        width = 1.2 + 6.6 * (rel ** 0.65)
        if i != 0:
            width *= 0.66
        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                mode="lines",
                line={"width": width, "color": color},
                opacity=opacity,
                text=[f"{origin} → {host}"] * len(lats),
                customdata=[value] * len(lats),
                hovertemplate=f"{origin} → {host}<br><b>{value:,.0f}</b> people<extra></extra>",
                showlegend=False,
                name=f"Route {i+1}",
            )
        )
        host_lats.append(lat2); host_lons.append(lon2); host_names.append(host); host_values.append(value)
        focus_points.extend([(lat1, lon1), (lat2, lon2)])
        origins_seen.add(origin)

    if not fig.data:
        return empty_fig("Route centroids are unavailable for current top corridors", height)

    # Host endpoints.
    fig.add_trace(
        go.Scattergeo(
            lat=host_lats,
            lon=host_lons,
            mode="markers",
            marker={"size": 7, "color": GREEN, "line": {"width": 1.2, "color": "white"}},
            text=host_names,
            customdata=host_values,
            hovertemplate="Host: %{text}<br><b>%{customdata:,.0f}</b> people<extra></extra>",
            showlegend=False,
        )
    )

    # Origin points and subtle pressure rings for top origins.
    origin_lats, origin_lons, origin_text = [], [], []
    for origin in origins_seen:
        if origin in CENTROIDS:
            origin_lats.append(CENTROIDS[origin][0]); origin_lons.append(CENTROIDS[origin][1]); origin_text.append(origin)
    fig.add_trace(
        go.Scattergeo(
            lat=origin_lats,
            lon=origin_lons,
            mode="markers",
            marker={"size": 9, "color": RED, "line": {"width": 1.2, "color": "white"}},
            text=origin_text,
            hovertemplate="Origin: %{text}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_geos(**_focus_geo(focus_points))
    fig.update_layout(
        height=height,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=MAP_BG,
        plot_bgcolor=MAP_BG,
        dragmode="pan",
        uirevision=f"route-map-{len(d)}-{int(maxv)}",
    )
    return safe_fig(fig)


def host_map_impl(d: pd.DataFrame, height: int = 620, focus: bool = True) -> go.Figure:
    """Stable host-country choropleth for the geography slide.

    This view is intentionally static: it answers where hosting is located.
    Route movement is reserved for the corridor maps.
    """
    if d.empty:
        return empty_fig("No host geography for this selection", height)

    d = d.copy()
    if "host_map_eligible_flag" in d.columns:
        d = d[d["host_map_eligible_flag"] == True]
    if "host_iso3" not in d.columns or "host_country_std" not in d.columns:
        return empty_fig("Host map columns are unavailable", height)

    d = d[d["host_iso3"].notna()].copy()
    m = d.groupby(["host_country_std", "host_iso3"], as_index=False).agg(value_observed=("value_observed", "sum"))
    m = m[m["value_observed"].fillna(0) > 0]
    if m.empty:
        return empty_fig("No map-eligible host countries", height)

    fig = px.choropleth(
        m,
        locations="host_iso3",
        color="value_observed",
        hover_name="host_country_std",
        color_continuous_scale=[
            [0.00, "#eef3fb"],
            [0.25, "#d7e3f7"],
            [0.50, "#aac4ea"],
            [0.75, "#6d9fd7"],
            [1.00, "#2f66c5"],
        ],
        range_color=(0, float(m["value_observed"].max())),
    )
    fig.update_traces(
        marker_line_width=0.55,
        marker_line_color="rgba(17,24,39,.32)",
        hovertemplate="<b>%{hovertext}</b><br>%{z:,.0f} people<extra></extra>",
    )

    geo_cfg = _base_geo()
    geo_cfg.update({"domain": {"x": [0.00, 0.88], "y": [0.00, 1.00]}})

    if focus:
        points = [CENTROIDS[country] for country in m["host_country_std"].dropna().astype(str) if country in CENTROIDS]
        focus_cfg = _focus_geo(points)
        # Do not pass duplicate showframe/domain kwargs; merge into one dict.
        geo_cfg.update(focus_cfg)
        geo_cfg["domain"] = {"x": [0.00, 0.88], "y": [0.00, 1.00]}

    fig.update_geos(**geo_cfg)
    fig.update_layout(
        height=height,
        autosize=True,
        margin={"l": 0, "r": 4, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar={"title": {"text": "People", "side": "top"}, "tickformat": "~s", "thickness": 10, "len": 0.52, "x": 0.91, "xanchor": "left", "y": 0.50, "yanchor": "middle", "outlinewidth": 0},
        uirevision="host-map-stable",
    )
    return safe_fig(fig)



def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def host_map_large():
        return host_map_impl(state.selected_stock(), height=620, focus=True)

    @output
    @render_widget
    def flow_map():
        corridors = build_corridors(state.selected_stock(), min(state.top_n(), 12))
        return make_route_map_figure(corridors, height=620, max_routes=min(state.top_n(), 12))
