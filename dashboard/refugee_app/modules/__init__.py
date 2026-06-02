"""Register Shiny server modules for the final core dashboard.

The final UI intentionally excludes weak bonus views (Sankey, network, raw
appendix, and scenario ML) so the demo remains focused and visually strong.
"""
from __future__ import annotations

from shiny import Inputs, Outputs, Session

from refugee_app.modules import hero, map_flows, method, rankings, storytelling
from refugee_app.services.data_loader import DataStore
from refugee_app.services.filters_state import make_state


def register_modules(input: Inputs, output: Outputs, session: Session, data: DataStore) -> None:
    state = make_state(input, session, data)
    hero.register(input, output, data, state)
    map_flows.register(input, output, data, state)
    rankings.register(input, output, data, state)
    storytelling.register(input, output, data, state)
    method.register(input, output, data, state)
