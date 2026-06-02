"""Sankey output module."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from shiny import Inputs, Outputs, render
from shinywidgets import render_widget

from refugee_app.constants import BLUE, GREEN, ORANGE
from refugee_app.modules.hero import empty_fig
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import DashboardState, build_corridors
from refugee_app.services.serializers import safe_fig


def register(input: Inputs, output: Outputs, data: DataStore, state: DashboardState) -> None:
    @output
    @render_widget
    def sankey_plot():
        corridors = build_corridors(state.selected_stock(), int(input.top_n()))
        if corridors.empty:
            return empty_fig("No Sankey links for this selection", 315)
        origins = corridors["origin_country_std"].drop_duplicates().tolist()
        hosts = corridors["host_country_std"].drop_duplicates().tolist()
        statuses = corridors["population_type_std"].drop_duplicates().tolist()
        labels = origins + hosts + statuses
        idx = {label: i for i, label in enumerate(labels)}
        src, tgt, val = [], [], []
        for _, r in corridors.iterrows():
            src.append(idx[r["origin_country_std"]]); tgt.append(idx[r["host_country_std"]]); val.append(float(r["value_observed"]))
            src.append(idx[r["host_country_std"]]); tgt.append(idx[r["population_type_std"]]); val.append(float(r["value_observed"]))
        colors = [ORANGE]*len(origins) + [BLUE]*len(hosts) + [GREEN]*len(statuses)
        fig = go.Figure(go.Sankey(node={"label": labels, "pad": 14, "thickness": 14, "color": colors}, link={"source": src, "target": tgt, "value": val, "color": "rgba(17,24,39,.15)"}))
        fig.update_layout(height=315, margin={"l": 8, "r": 8, "t": 4, "b": 4})
        return safe_fig(fig)
