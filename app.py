#!/usr/bin/env python3
"""Repository-root Shiny entry point for the dashboard app.

The actual modular app package lives in dashboard/refugee_app. This wrapper lets
the dashboard run from the repository root with:

    py -m shiny run --launch-browser --port 8001 app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from shiny import App, Inputs, Outputs, Session

APP_DIR = Path(__file__).resolve().parent / "dashboard"
sys.path.insert(0, str(APP_DIR))

from refugee_app.modules import register_modules
from refugee_app.services.data_loader import load_data
from refugee_app.ui.layout import build_ui

DATA = load_data(APP_DIR)
app_ui = build_ui(DATA)


def server(input: Inputs, output: Outputs, session: Session):
    register_modules(input, output, session, DATA)


app = App(app_ui, server)
