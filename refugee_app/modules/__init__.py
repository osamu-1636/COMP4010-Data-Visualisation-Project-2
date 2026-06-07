"""Register Shiny server modules for the excellent-rubric final dashboard."""
from __future__ import annotations

from shiny import Inputs, Outputs, Session

from refugee_app.modules import advanced_viz, hero, map_flows, method, rankings, sankey, storytelling
from refugee_app.modules import ml_visualized
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import make_state


def register_modules(input: Inputs, output: Outputs, session: Session, data: DataStore) -> None:
    state = make_state(input, session, data)
    hero.register(input, output, data, state)
    map_flows.register(input, output, data, state)
    rankings.register(input, output, data, state)
    sankey.register(input, output, data, state)
    advanced_viz.register(input, output, data, state)
    ml_visualized.register(input, output, data, state)
    storytelling.register(input, output, data, state)
    method.register(input, output, data, state)
