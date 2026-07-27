"""Data access layer.

Every read from disk happens here, behind `@st.cache_data`, so pages stay fast
no matter how often Streamlit re-runs them. Pages never touch a file path.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from .config import PATHS


class ArtifactsMissing(Exception):
    """Raised when the notebook's output has not been copied in yet."""


# --------------------------------------------------------------------------
# Availability
# --------------------------------------------------------------------------
def artifacts_present() -> bool:
    return PATHS["registry"].exists() and PATHS["prices"].exists()


def missing_files() -> list[str]:
    return [k for k, p in PATHS.items() if isinstance(p, Path) and p.suffix and not p.exists()]


def require_artifacts() -> None:
    """Show a setup screen and halt the page if artifacts are absent."""
    if artifacts_present():
        return
    st.error("Forecast artifacts not found.")
    st.markdown(
        """
Run the Colab notebook, download `bd_forecasting_artifacts.zip`, and unzip it so that
`data/` and `artifacts/` sit next to `Home.py`:

```
streamlit_dashboard/
├── Home.py
├── data/          <- from the zip
└── artifacts/     <- from the zip
```

To preview the interface with sample data instead, run:

```bash
python bootstrap_demo.py
```
"""
    )
    st.stop()


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_registry() -> dict:
    with open(PATHS["registry"]) as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_prices() -> pd.DataFrame:
    df = pd.read_csv(PATHS["prices"], parse_dates=["date"])
    return df.sort_values(["commodity", "date"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_forecasts() -> pd.DataFrame:
    if not PATHS["forecasts"].exists():
        return pd.DataFrame()
    return pd.read_csv(PATHS["forecasts"], parse_dates=["date"])


@st.cache_data(show_spinner=False)
def load_inflation() -> pd.DataFrame:
    if not PATHS["inflation"].exists():
        return pd.DataFrame()
    return pd.read_csv(PATHS["inflation"])


@st.cache_data(show_spinner=False)
def load_composite() -> pd.DataFrame:
    if not PATHS["composite"].exists():
        return pd.DataFrame()
    return pd.read_csv(PATHS["composite"])


@st.cache_data(show_spinner=False)
def load_comparison() -> pd.DataFrame:
    if not PATHS["comparison"].exists():
        return pd.DataFrame()
    return pd.read_csv(PATHS["comparison"])


@st.cache_data(show_spinner=False)
def load_test_predictions() -> pd.DataFrame:
    if not PATHS["test_preds"].exists():
        return pd.DataFrame()
    return pd.read_csv(PATHS["test_preds"], parse_dates=["date"])


# --------------------------------------------------------------------------
# Convenience accessors
# --------------------------------------------------------------------------
def commodities() -> list[str]:
    reg = load_registry()
    return list(reg.get("commodities", {}).keys()) or sorted(load_prices()["commodity"].unique())


def best_model(commodity: str) -> str:
    reg = load_registry()
    return reg.get("commodities", {}).get(commodity, {}).get("best_model", "SARIMA")


def price_series(commodity: str) -> pd.Series:
    df = load_prices()
    s = df[df["commodity"] == commodity].set_index("date")["price"]
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def available_models(commodity: str | None = None) -> list[str]:
    fc = load_forecasts()
    if fc.empty:
        return []
    sub = fc if commodity is None else fc[fc["commodity"] == commodity]
    order = ["SARIMA", "XGBoost", "LSTM"]
    present = list(sub["model"].unique())
    return [m for m in order if m in present] + [m for m in present if m not in order]


def max_horizon() -> int:
    fc = load_forecasts()
    return int(fc["horizon_day"].max()) if not fc.empty else 30


# --------------------------------------------------------------------------
# Derived series
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def inflation_series(commodity: str) -> pd.DataFrame:
    """Historical inflation at daily, weekly, monthly and annual frequency."""
    s = price_series(commodity)
    out = pd.DataFrame({"price": s})
    out["daily_%"] = s.pct_change(1) * 100
    out["weekly_%"] = s.pct_change(7) * 100
    out["monthly_%"] = s.pct_change(30) * 100
    out["annual_%"] = s.pct_change(365) * 100
    out["volatility_30"] = s.pct_change().rolling(30).std() * 100
    return out


@st.cache_data(show_spinner=False)
def descriptive_stats(commodity: str, start=None, end=None) -> pd.DataFrame:
    s = price_series(commodity)
    if start is not None:
        s = s[s.index >= pd.Timestamp(start)]
    if end is not None:
        s = s[s.index <= pd.Timestamp(end)]
    ret = s.pct_change().dropna()
    rows = {
        "Observations": len(s),
        "Start": s.index.min().date().isoformat() if len(s) else "-",
        "End": s.index.max().date().isoformat() if len(s) else "-",
        "Mean": s.mean(),
        "Median": s.median(),
        "Std deviation": s.std(),
        "Minimum": s.min(),
        "Maximum": s.max(),
        "Range": s.max() - s.min(),
        "Coefficient of variation (%)": s.std() / s.mean() * 100 if s.mean() else np.nan,
        "Skewness": s.skew(),
        "Kurtosis": s.kurtosis(),
        "Daily volatility (%)": ret.std() * 100,
        "Annualised volatility (%)": ret.std() * np.sqrt(365) * 100,
    }
    def fmt(k, v):
        if isinstance(v, str):
            return v
        if k == "Observations":
            return f"{int(v):,}"
        return "-" if pd.isna(v) else f"{v:,.3f}"

    return pd.DataFrame({"Statistic": list(rows.keys()),
                         "Value": [fmt(k, v) for k, v in rows.items()]})


def latest_snapshot(commodity: str) -> dict:
    """Current price plus the context needed for a KPI card."""
    s = price_series(commodity)
    if s.empty:
        return {}
    cur = float(s.iloc[-1])
    win = s.iloc[-365:] if len(s) >= 365 else s

    def chg(days: int) -> float:
        if len(s) <= days:
            return float("nan")
        prev = float(s.iloc[-1 - days])
        return (cur - prev) / prev * 100 if prev else float("nan")

    return {
        "price": cur,
        "date": s.index[-1],
        "change_1d": chg(1),
        "change_7d": chg(7),
        "change_30d": chg(30),
        "change_365d": chg(365),
        "low_52w": float(win.min()),
        "high_52w": float(win.max()),
        "mean_52w": float(win.mean()),
        "volatility_30d": float(s.pct_change().rolling(30).std().iloc[-1] * 100)
        if len(s) > 31 else float("nan"),
    }


def forecast_for(commodity: str, model: str, horizon: int) -> pd.DataFrame:
    fc = load_forecasts()
    if fc.empty:
        return pd.DataFrame()
    sub = fc[(fc["commodity"] == commodity) & (fc["model"] == model)
             & (fc["horizon_day"] <= horizon)]
    return sub.sort_values("horizon_day").reset_index(drop=True)
