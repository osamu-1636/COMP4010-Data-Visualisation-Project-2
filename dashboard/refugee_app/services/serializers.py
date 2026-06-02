"""JSON-safe serializers for Shiny + Plotly widgets."""
from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def json_sanitize(obj: Any) -> Any:
    """Convert pandas/numpy NaN-like values into JSON-safe nulls.

    Shiny sends widget state over WebSockets using strict JSON. Python NaN and inf
    are valid floats but invalid JSON under allow_nan=False, so every Plotly figure
    is scrubbed before being returned.
    """
    if isinstance(obj, dict):
        return {str(k): json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [json_sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [json_sanitize(v) for v in obj.tolist()]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        obj = float(obj)
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if obj is pd.NA:
        return None
    try:
        if not isinstance(obj, (str, bytes)) and pd.isna(obj):
            return None
    except Exception:
        pass
    return obj


def assert_json_safe(obj: Any) -> None:
    json.dumps(json_sanitize(obj), allow_nan=False)


def safe_fig(fig: go.Figure, *, height: int | None = None) -> go.Figure:
    """Apply consistent theme and scrub the figure for strict JSON."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": "#111827", "size": 12},
        hoverlabel={"bgcolor": "white", "bordercolor": "#111827", "font_size": 12},
        modebar_remove=["select2d", "lasso2d"],
    )
    if height is not None:
        fig.update_layout(height=height)
    return go.Figure(json_sanitize(fig.to_plotly_json()))
