"""Shared sidebar controls, so every page offers the same vocabulary."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import data as D
from .config import pretty_name
from .theme import sidebar_brand, sidebar_label
from .compat import STRETCH


def sidebar_controls(show_horizon: bool = False) -> dict:
    sidebar_brand()
    state: dict = {}

    sidebar_label("Display")
    dark = st.sidebar.toggle(
        "Dark charts", value=st.session_state.get("dark_charts", False),
        help="Switches chart styling. To change the whole app, use Settings in the top-right menu.")
    st.session_state["dark_charts"] = dark
    state["dark"] = dark

    if show_horizon:
        sidebar_label("Forecast")
        max_h = D.max_horizon()
        default = min(30, max_h)
        state["horizon"] = st.sidebar.slider(
            "Forecast horizon (days)", min_value=1, max_value=int(max_h),
            value=int(st.session_state.get("horizon", default)), step=1)
        st.session_state["horizon"] = state["horizon"]

    reg = D.load_registry()
    gen = reg.get("generated_at", "")
    if gen:
        st.sidebar.markdown(
            f'<div class="bd-side-meta"><span class="bd-dot"></span>'
            f"<span>Artifacts generated<br>"
            f"{pd.to_datetime(gen).strftime('%d %b %Y, %H:%M')}</span></div>",
            unsafe_allow_html=True)
    return state


def commodity_picker(label="Commodity", key="commodity", multi=False, default_all=True):
    options = D.commodities()
    if multi:
        return st.multiselect(label, options, default=options if default_all else options[:1],
                              format_func=pretty_name, key=key)
    stored = st.session_state.get("sel_commodity")
    index = options.index(stored) if stored in options else 0
    choice = st.selectbox(label, options, index=index, format_func=pretty_name, key=key)
    st.session_state["sel_commodity"] = choice
    return choice


def date_range_picker(series_index, key="dates"):
    lo, hi = series_index.min().date(), series_index.max().date()
    preset = st.selectbox("Period", ["Full history", "Last 5 years", "Last 3 years",
                                     "Last 12 months", "Last 6 months", "Custom"],
                          index=0, key=f"{key}_preset")
    offsets = {"Last 5 years": 365 * 5, "Last 3 years": 365 * 3,
               "Last 12 months": 365, "Last 6 months": 182}
    if preset == "Custom":
        picked = st.date_input("Date range", value=(lo, hi), min_value=lo, max_value=hi,
                               key=f"{key}_custom")
        if isinstance(picked, tuple) and len(picked) == 2:
            return picked[0], picked[1]
        return lo, hi
    if preset in offsets:
        start = max(lo, (pd.Timestamp(hi) - pd.Timedelta(days=offsets[preset])).date())
        return start, hi
    return lo, hi


def download_row(items: list[tuple[str, bytes, str, str]]) -> None:
    """items: (label, payload, filename, mime)"""
    cols = st.columns(len(items), gap="small")
    for col, (label, payload, fname, mime) in zip(cols, items):
        col.download_button(label, data=payload, file_name=fname, mime=mime,
                            **STRETCH)


def metric_help() -> None:
    st.caption(
        "MAE and RMSE are in BDT — lower is better. MAPE is a percentage error — lower is "
        "better. R² is the share of variance explained — higher is better, and a negative "
        "value means the model is worse than predicting the average. Skill compares against "
        "a seasonal naive baseline — positive means the model beats doing nothing.")
