"""Small shims so the dashboard runs on both older and newer Streamlit.

Streamlit replaced `use_container_width=True` with `width="stretch"` and
`st.components.v1.html` with `st.iframe`. Detecting the available API once here
keeps every page free of version checks.
"""
from __future__ import annotations

import inspect

import streamlit as st


def _supports_width() -> bool:
    try:
        return "width" in inspect.signature(st.dataframe).parameters
    except (TypeError, ValueError):
        return False


_WIDTH_API = _supports_width()

# Spread into any Streamlit element: st.dataframe(df, **STRETCH)
STRETCH: dict = {"width": "stretch"} if _WIDTH_API else {"use_container_width": True}
CONTENT: dict = {"width": "content"} if _WIDTH_API else {"use_container_width": False}


def html_embed(markup: str, height: int = 600, scrolling: bool = True) -> None:
    """Render a full HTML document in a sandboxed frame.

    `st.components.v1.html` is the only API that isolates a complete document
    (including its own <style>) from the surrounding page. `st.iframe` takes a
    URL rather than markup, so it is not a substitute here. If the components
    API ever disappears, fall back to inline rendering.
    """
    try:
        import streamlit.components.v1 as components
        components.html(markup, height=height, scrolling=scrolling)
    except Exception:
        st.html(markup)
