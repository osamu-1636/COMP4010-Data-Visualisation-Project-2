"""Filter module facade.

The reactive filter implementation lives in services/filters_state.py because it is shared
by every visual module. This file exists to keep the codebase architecture explicit and
matching the dashboard design contract.
"""
from refugee_app.services.filters_state import apply_filters, selected_types, make_state

__all__ = ["apply_filters", "selected_types", "make_state"]
