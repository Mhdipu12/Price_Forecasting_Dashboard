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
# dark canvas, so one categorical palette serves both modes.
# --------------------------------------------------------------------------
PALETTE = {
    "ink":     "#0F172A",   # deep slate — headings, dark surfaces
    "paper":   "#FFFFFF",   # page canvas
    "rule":    "#E4E8EE",   # hairline dividers
    "muted":   "#64748B",   # secondary text
    "onion":   "#C2408A",   # onion skin
    "potato":  "#B0723C",   # earth ochre
    "oil":     "#D9A404",   # golden amber
    "sage":    "#0E9F6E",   # prices falling / good news
    "alert":   "#DC2626",   # prices rising / warning
    "slate":   "#3B82F6",   # neutral series (baseline, SARIMA)
}

# Surface tokens per appearance mode. `theme.py` turns these into CSS custom
# properties and `charts.py` reads them for gridlines and axis text, so the
# figures and the page furniture never drift apart.
SURFACE = {
    "light": {
        "canvas":       "#FFFFFF",
        "surface":      "#FFFFFF",
        "surface_alt":  "#F8FAFC",
        "border":       "#E4E8EE",
        "border_bold":  "#CBD5E1",
        "grid":         "#EDF1F6",
        "axis":         "#CBD5E1",
        "text":         "#0F172A",
        "text_soft":    "#475569",
        "muted":        "#64748B",
        "accent":       "#2563EB",
        "positive":     "#047857",
        "negative":     "#C2261E",
        "hover_bg":     "#FFFFFF",
    },
    "dark": {
        "canvas":       "#0B1220",
        "surface":      "#141D2E",
        "surface_alt":  "#0F1828",
        "border":       "#25314A",
        "border_bold":  "#35435F",
        "grid":         "#1E2A40",
        "axis":         "#35435F",
        "text":         "#E6EDF6",
        "text_soft":    "#B6C2D4",
        "muted":        "#8A99AE",
        "accent":       "#60A5FA",
        "positive":     "#34D399",
        "negative":     "#F87171",
        "hover_bg":     "#141D2E",
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
    "SARIMA":         {"color": "#3B82F6"},
    "XGBoost":        {"color": "#10B981"},
    "LSTM":           {"color": "#8B5CF6"},
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
