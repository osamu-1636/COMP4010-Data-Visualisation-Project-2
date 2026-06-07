#!/usr/bin/env python3
"""Thin Shiny entry point for the modular forced migration dashboard."""
from __future__ import annotations
from shiny import App, Inputs, Outputs, Session
from refugee_app.modules import register_modules
from refugee_app.services.data_loader import load_data
from refugee_app.ui.layout import build_ui
DATA = load_data()
app_ui = build_ui(DATA)
def server(input: Inputs, output: Outputs, session: Session):
    register_modules(input, output, session, DATA)
app = App(app_ui, server)
