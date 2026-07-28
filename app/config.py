"""Central configuration: paths, palette, and commodity metadata.

Every tunable value in the dashboard lives here. Nothing else hardcodes a path
or a colour.
"""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent


# --------------------------------------------------------------------------
# Where the notebook's artifacts live
# --------------------------------------------------------------------------
def resolve_data_root() -> Path:
    """Find the folder that contains `data/` and `artifacts/`.

    Search order:
      1. the BD_DATA_ROOT environment variable
      2. the dashboard folder itself
      3. a `bd_price_forecasting/` subfolder (the notebook's zip layout)
      4. the parent folder
    """
    env = os.environ.get("BD_DATA_ROOT")
    candidates = [Path(env)] if env else []
    candidates += [ROOT, ROOT / "bd_price_forecasting", ROOT.parent]
    for c in candidates:
        if (c / "artifacts" / "registry.json").exists():
            return c
    return ROOT


DATA_ROOT = resolve_data_root()

PATHS = {
    "registry":       DATA_ROOT / "artifacts" / "registry.json",
    "best_model":     DATA_ROOT / "artifacts" / "metrics" / "best_model.json",
    "comparison":     DATA_ROOT / "artifacts" / "metrics" / "model_comparison.csv",
    "prices":         DATA_ROOT / "data" / "processed" / "all_prices_long.csv",
    "forecasts":      DATA_ROOT / "data" / "predictions" / "future_forecasts.csv",
    "inflation":      DATA_ROOT / "data" / "predictions" / "future_inflation.csv",
    "composite":      DATA_ROOT / "data" / "predictions" / "composite_inflation.csv",
    "test_preds":     DATA_ROOT / "data" / "predictions" / "test_predictions.csv",
    "models_dir":     DATA_ROOT / "artifacts" / "models",
    "scalers_dir":    DATA_ROOT / "artifacts" / "scalers",
    "metrics_dir":    DATA_ROOT / "artifacts" / "metrics",
}


# --------------------------------------------------------------------------
# Palette — each commodity wears its own colour, taken from the thing itself.
#
# Every value is a mid-tone chosen to stay legible on both the light and the
# dark canvas, so one categorical palette serves both modes. The three aurora
# hues (violet, cyan, magenta) are the signature of the interface: they light
# the page background, the brand mark and every gradient in the chrome.
# --------------------------------------------------------------------------
PALETTE = {
    "ink":     "#0B1020",   # deep space — headings, dark surfaces
    "paper":   "#FFFFFF",   # page canvas
    "rule":    "#E3E7F7",   # hairline dividers
    "muted":   "#6B7699",   # secondary text
    "onion":   "#E0459B",   # onion skin
    "potato":  "#C98A3E",   # earth ochre
    "oil":     "#E5B00A",   # golden amber
    "sage":    "#10B981",   # prices falling / good news
    "alert":   "#F43F5E",   # prices rising / warning
    "slate":   "#6366F1",   # neutral series (baseline, SARIMA)
    "violet":  "#8B5CF6",   # aurora — primary light
    "cyan":    "#22D3EE",   # aurora — cool light
    "magenta": "#EC4899",   # aurora — warm light
}

# Surface tokens per appearance mode. `theme.py` turns these into CSS custom
# properties and `charts.py` reads them for gridlines and axis text, so the
# figures and the page furniture never drift apart.
#
# `aurora_*` are the three light sources painted behind the whole page, and
# `glass*` describe the frosted panes that float on top of them.
SURFACE = {
    "light": {
        "canvas":       "#F5F7FF",
        "surface":      "#FFFFFF",
        "surface_alt":  "#F0F3FE",
        "border":       "#E3E7F7",
        "border_bold":  "#C6CCEA",
        "grid":         "#EAEDFB",
        "axis":         "#C6CCEA",
        "text":         "#101736",
        "text_soft":    "#454E72",
        "muted":        "#6B7699",
        "accent":       "#6D4AFF",
        "positive":     "#059669",
        "negative":     "#E11D48",
        "hover_bg":     "#FFFFFF",
        "aurora_1":     "rgba(139,92,246,0.22)",
        "aurora_2":     "rgba(34,211,238,0.17)",
        "aurora_3":     "rgba(236,72,153,0.15)",
        "glass":        "rgba(255,255,255,0.68)",
        "glass_strong": "rgba(255,255,255,0.82)",
        "glass_border": "rgba(16,23,54,0.09)",
        "hairline":     "rgba(255,255,255,0.85)",
        "grain":        "0.030",
    },
    "dark": {
        "canvas":       "#060912",
        "surface":      "#101A2E",
        "surface_alt":  "#0C1424",
        "border":       "#26314D",
        "border_bold":  "#3A4870",
        "grid":         "#1A2437",
        "axis":         "#35446B",
        "text":         "#E9EEFC",
        "text_soft":    "#B4C0DA",
        "muted":        "#8593B4",
        "accent":       "#A78BFA",
        "positive":     "#34D399",
        "negative":     "#FB7185",
        "hover_bg":     "#0F1930",
        "aurora_1":     "rgba(124,58,237,0.42)",
        "aurora_2":     "rgba(34,211,238,0.26)",
        "aurora_3":     "rgba(236,72,153,0.24)",
        "glass":        "rgba(255,255,255,0.045)",
        "glass_strong": "rgba(255,255,255,0.075)",
        "glass_border": "rgba(255,255,255,0.10)",
        "hairline":     "rgba(255,255,255,0.14)",
        "grain":        "0.055",
    },
}


def surface(dark: bool = False) -> dict:
    """Surface tokens for the requested appearance."""
    return SURFACE["dark" if dark else "light"]


COMMODITY_STYLE = {
    "Onion":       {"color": PALETTE["onion"],  "unit": "BDT/kg",    "label": "Onion"},
    "Potato":      {"color": PALETTE["potato"], "unit": "BDT/kg",    "label": "Potato"},
    "Soybean_Oil": {"color": PALETTE["oil"],    "unit": "BDT/litre", "label": "Soybean oil"},
}

MODEL_STYLE = {
    "SARIMA":         {"color": "#6366F1"},
    "XGBoost":        {"color": "#10B981"},
    "LSTM":           {"color": "#A855F7"},
    "Seasonal Naive": {"color": "#94A3B8"},
}

DEFAULT_STYLE = {"color": PALETTE["slate"], "unit": "BDT", "label": "Commodity"}


def style_for(commodity: str) -> dict:
    return COMMODITY_STYLE.get(commodity, {**DEFAULT_STYLE, "label": pretty_name(commodity)})


def model_color(model: str) -> str:
    return MODEL_STYLE.get(model, {"color": PALETTE["muted"]})["color"]


def pretty_name(commodity: str) -> str:
    return COMMODITY_STYLE.get(commodity, {}).get("label", commodity.replace("_", " "))


def unit_for(commodity: str) -> str:
    return COMMODITY_STYLE.get(commodity, DEFAULT_STYLE)["unit"]


PAGE_ICON = ":material/query_stats:"
APP_TITLE = "Bangladesh Essential Commodity Price Monitor"
APP_SUBTITLE = "Forecasting price and inflation with SARIMA, XGBoost and LSTM"
