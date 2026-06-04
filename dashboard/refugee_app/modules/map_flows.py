"""Spatial, flow-map and network outputs.

This module contains the production map layer for the dashboard:
- dynamic choropleth fitting
- curved origin-host corridor routes
- moving-group route markers animated by app.js
- host-pressure and network supporting views
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shiny import Inputs, Outputs
from shinywidgets import render_widget

from refugee_app.constants import BLUE, CENTROIDS, GREEN, ORANGE, PURPLE
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, build_corridors
from refugee_app.services.serializers import safe_fig

Point = Tuple[float, float]


def _is_finite(x: object) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _base_geo() -> dict:
    return {
        "projection_type": "natural earth",
        "showland": True,
        "landcolor": "rgb(245,241,233)",
        "showcountries": True,
        "countrycolor": "rgba(17,24,39,.24)",
        "showcoastlines": False,
        "showocean": True,
        "oceancolor": "rgb(252,249,243)",
        "bgcolor": "rgba(0,0,0,0)",
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

    lat_low = max(-60.0, lat_min - lat_pad)
    lat_high = min(82.0, lat_max + lat_pad)
    lon_low = max(-179.0, lon_min - lon_pad)
    lon_high = min(179.0, lon_max + lon_pad)

    effective_span = max(lon_span, lat_span * 1.75, 18.0)

    geo.update(
        {
            "center": {
                "lat": (lat_low + lat_high) / 2,
                "lon": (lon_low + lon_high) / 2,
            },
            "projection_scale": max(0.92, min(5.4, 106.0 / effective_span)),
            "lataxis_range": [lat_low, lat_high],
            "lonaxis_range": [lon_low, lon_high],
        }
    )

    return geo


def _curved_line(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    steps: int = 44,
) -> tuple[list[float], list[float]]:
    """Return a visual curve for display. It is not a geodesic measurement."""
    t = np.linspace(0, 1, steps)

    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    lats = lat1 + (lat2 - lat1) * t
    lons = lon1 + (lon2 - lon1) * t

    bend = math.sin((lon2 - lon1) * math.pi / 180.0) * 3.0
    lats = lats + bend * np.sin(np.pi * t)

    return lats.tolist(), lons.tolist()


def make_route_map_figure(
    corridors: pd.DataFrame,
    *,
    height: int = 600,
    max_routes: int = 15,
    route_color: str = BLUE,
    moving: bool = True,
    **_: object,
) -> go.Figure:
    """Build a focused route map with optional moving-group markers.

    app.js animates the trace named "Moving groups" by restyling its lat/lon
    along the visible route lines. This avoids Plotly frame instability in Shiny.
    """
    if corridors is None or corridors.empty:
        return empty_fig("No origin-host corridors for this selection", height)

    required = {"origin_country_std", "host_country_std", "value_observed"}
    if not required.issubset(set(corridors.columns)):
        return empty_fig("Route data is missing required columns", height)

    d = corridors.copy()
    d = d[d["value_observed"].fillna(0) > 0]
    d = d.sort_values("value_observed", ascending=False).head(int(max_routes))

    if d.empty:
        return empty_fig("No positive corridor values for this selection", height)

    maxv = float(d["value_observed"].max()) if len(d) else 0.0

    fig = go.Figure()

    focus_points: List[Point] = []
    moving_lat: list[float] = []
    moving_lon: list[float] = []
    moving_text: list[str] = []
    moving_values: list[float] = []

    origin_seen: list[str] = []
    host_lats: list[float] = []
    host_lons: list[float] = []
    host_names: list[str] = []
    host_values: list[float] = []

    plotted = 0

    for route_index, (_, r) in enumerate(d.iterrows()):
        origin = str(r["origin_country_std"])
        host = str(r["host_country_std"])

        if origin not in CENTROIDS or host not in CENTROIDS:
            continue

        lat1, lon1 = CENTROIDS[origin]
        lat2, lon2 = CENTROIDS[host]

        value = float(r["value_observed"]) if _is_finite(r["value_observed"]) else 0.0
        rel = value / maxv if maxv else 0.0

        lats, lons = _curved_line(lat1, lon1, lat2, lon2)

        width = 1.05 + 6.2 * rel
        opacity = 0.30 + 0.50 * rel

        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                mode="lines",
                line={"width": width, "color": route_color},
                opacity=opacity,
                text=[f"{origin} to {host}"] * len(lats),
                customdata=[value] * len(lats),
                hovertemplate=f"{origin} to {host}<br><b>{value:,.0f}</b> people<extra></extra>",
                showlegend=False,
                name="Route line",
            )
        )

        host_lats.append(lat2)
        host_lons.append(lon2)
        host_names.append(host)
        host_values.append(value)

        focus_points.extend([(lat1, lon1), (lat2, lon2)])
        plotted += 1

        if origin not in origin_seen:
            origin_seen.append(origin)

        if moving and lats:
            idx = (route_index * 7) % len(lats)
            moving_lat.append(lats[idx])
            moving_lon.append(lons[idx])
            moving_text.append(f"{origin} to {host}")
            moving_values.append(value)

    if plotted == 0:
        return empty_fig("Route centroids are not available for this selection", height)

    fig.add_trace(
        go.Scattergeo(
            lat=host_lats,
            lon=host_lons,
            mode="markers",
            marker={
                "size": 7,
                "color": ORANGE,
                "line": {"width": 1.1, "color": "white"},
            },
            text=host_names,
            customdata=host_values,
            hovertemplate="Host: %{text}<br><b>%{customdata:,.0f}</b> people<extra></extra>",
            showlegend=False,
            name="Host markers",
        )
    )

    origin_lats: list[float] = []
    origin_lons: list[float] = []
    origin_text: list[str] = []

    for origin in origin_seen:
        if origin in CENTROIDS:
            origin_lats.append(CENTROIDS[origin][0])
            origin_lons.append(CENTROIDS[origin][1])
            origin_text.append(origin)

    fig.add_trace(
        go.Scattergeo(
            lat=origin_lats,
            lon=origin_lons,
            mode="markers+text" if len(origin_text) <= 3 else "markers",
            text=origin_text,
            textposition="top center",
            marker={
                "size": 10,
                "color": GREEN,
                "line": {"width": 1.2, "color": "white"},
            },
            hovertemplate="Origin: %{text}<extra></extra>",
            showlegend=False,
            name="Origin markers",
        )
    )

    if moving_lat:
        fig.add_trace(
            go.Scattergeo(
                lat=moving_lat,
                lon=moving_lon,
                mode="markers",
                marker={
                    "size": 9,
                    "color": "#111827",
                    "line": {"width": 1.6, "color": "white"},
                },
                text=moving_text,
                customdata=moving_values,
                hovertemplate="Moving group<br>%{text}<br><b>%{customdata:,.0f}</b> people<extra></extra>",
                showlegend=False,
                name="Moving groups",
            )
        )

    fig.update_geos(**_focus_geo(focus_points))

    fig.update_layout(
        height=height,
        autosize=True,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",
        hovermode="closest",
        uirevision=f"route-map-{len(d)}-{int(maxv) if maxv else 0}",
    )

    return safe_fig(fig)


def host_map_impl(d: pd.DataFrame, height: int = 620, focus: bool = True) -> go.Figure:
    if d.empty:
        return empty_fig("No host geography for this selection", height)

    d = d[(d["host_map_eligible_flag"] == True) & d["host_iso3"].notna()].copy()

    m = (
        d.groupby(["host_country_std", "host_iso3"], as_index=False)
        .agg(value_observed=("value_observed", "sum"))
    )
    m = m[m["value_observed"].fillna(0) > 0]

    if m.empty:
        return empty_fig("No map-eligible host countries", height)

    points = [
        CENTROIDS[country]
        for country in m["host_country_std"].dropna().astype(str)
        if country in CENTROIDS
    ]

    fig = px.choropleth(
        m,
        locations="host_iso3",
        color="value_observed",
        hover_name="host_country_std",
        color_continuous_scale="Blues",
        range_color=(0, float(m["value_observed"].max())),
    )

    fig.update_traces(
        marker_line_width=0.55,
        marker_line_color="rgba(17,24,39,.36)",
    )

    fig.update_geos(
        **(_focus_geo(points) if focus else _base_geo()),
        showframe=False,
        domain={"x": [0.00, 0.88], "y": [0.00, 1.00]},
    )

    fig.update_layout(
        height=height,
        autosize=True,
        margin={"l": 0, "r": 4, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar={
            "title": {"text": "People", "side": "top"},
            "tickformat": "~s",
            "thickness": 10,
            "len": 0.52,
            "x": 0.91,
            "xanchor": "left",
            "y": 0.50,
            "yanchor": "middle",
            "outlinewidth": 0,
        },
        uirevision="host-choropleth-focus",
    )

    return safe_fig(fig)


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def host_map_large():
        return host_map_impl(state.selected_stock(), height=620, focus=True)

    @output
    @render_widget
    def role_matrix():
        d = data.role_scatter.copy()

        if d.empty:
            return empty_fig("Role matrix not available", 620)

        if "year" in d.columns:
            d = d[d["year"].eq(state.year())]

        if d.empty:
            return empty_fig("Role matrix not available for selected year", 620)

        fig = px.scatter(
            d,
            x="origin_stock_observed",
            y="host_stock_observed",
            size="host_stock_observed",
            color="role_class",
            hover_name="country",
            log_x=True,
            log_y=True,
            color_discrete_sequence=[BLUE, ORANGE, GREEN, PURPLE],
        )

        fig.update_layout(
            height=620,
            margin={"l": 54, "r": 20, "t": 24, "b": 50},
            legend_title_text="Role",
        )
        fig.update_xaxes(title="Origin stock (log)", tickformat="~s")
        fig.update_yaxes(title="Host stock (log)", tickformat="~s")

        return safe_fig(fig)

    @output
    @render_widget
    def host_pressure_plot():
        hp = data.host_pressure.copy()

        if hp.empty:
            d = state.selected_stock()
            d = (
                d.groupby("host_country_std", as_index=False)
                .agg(host_stock_observed=("value_observed", "sum"))
                .sort_values("host_stock_observed", ascending=False)
                .head(12)
            )
            xcol, ycol = "host_stock_observed", "host_country_std"
        else:
            hp = hp[hp["year"].eq(state.year())] if "year" in hp.columns else hp

            metric_candidates = [
                "host_stock_per_100k_population",
                "refugees_per_100k",
                "Refugees_per_100k",
                "host_stock_observed",
            ]
            metric = next((c for c in metric_candidates if c in hp.columns and hp[c].notna().any()), None)

            if metric is None:
                return empty_fig("No host pressure metric", 620)

            ycol = (
                "country"
                if "country" in hp.columns
                else ("host_country_std" if "host_country_std" in hp.columns else hp.columns[0])
            )
            d = hp.sort_values(metric, ascending=False).head(12)
            xcol = metric

        if d.empty:
            return empty_fig("No host pressure data", 620)

        d = d.sort_values(xcol, ascending=True)

        fig = px.bar(
            d,
            x=xcol,
            y=ycol,
            orientation="h",
            color_discrete_sequence=[BLUE],
        )

        fig.update_layout(height=620, margin={"l": 150, "r": 28, "t": 24, "b": 52})
        fig.update_xaxes(title="Host pressure / stock", tickformat="~s")
        fig.update_yaxes(title="")

        return safe_fig(fig)

    @output
    @render_widget
    def flow_map():
        corridors = build_corridors(state.selected_stock(), state.top_n())
        return make_route_map_figure(
            corridors,
            height=600,
            max_routes=state.top_n(),
            route_color=BLUE,
            moving=True,
        )

    @output
    @render_widget
    def network_plot():
        corridors = build_corridors(state.selected_stock(), state.top_n())

        if corridors.empty:
            return empty_fig("No network data for this selection", 315)

        origins = corridors["origin_country_std"].drop_duplicates().tolist()
        hosts = corridors["host_country_std"].drop_duplicates().tolist()

        y_origin = {o: i for i, o in enumerate(origins)}
        y_host = {h: i for i, h in enumerate(hosts)}

        fig = go.Figure()
        maxv = corridors["value_observed"].max()

        for _, r in corridors.iterrows():
            width = 0.5 + 5 * float(r["value_observed"]) / maxv if maxv else 1.0

            fig.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[y_origin[r["origin_country_std"]], y_host[r["host_country_std"]]],
                    mode="lines",
                    line={"width": width, "color": "rgba(47,102,197,.32)"},
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=[0] * len(origins),
                y=list(y_origin.values()),
                mode="markers+text",
                text=origins,
                textposition="middle left",
                marker={"size": 9, "color": ORANGE},
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[1] * len(hosts),
                y=list(y_host.values()),
                mode="markers+text",
                text=hosts,
                textposition="middle right",
                marker={"size": 9, "color": GREEN},
                showlegend=False,
            )
        )

        fig.update_xaxes(visible=False, range=[-0.3, 1.3])
        fig.update_yaxes(visible=False)
        fig.update_layout(height=315, margin={"l": 20, "r": 20, "t": 4, "b": 4})

        return safe_fig(fig)
