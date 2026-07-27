"""Model service — the only place the dashboard touches a trained model.

Two modes, matching the project architecture:

  * Precomputed (default)  — read `future_forecasts.csv`. Milliseconds, cannot
    fail during a live demonstration.
  * Live inference         — load the serialized model and forecast on demand
    for a custom horizon. Slower, and degrades gracefully when a dependency or
    artifact is absent.

Models are cached with `@st.cache_resource` (shared, not copied); data with
`@st.cache_data`. Getting that distinction wrong is the usual cause of a slow
Streamlit app.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from . import data as D
from .config import PATHS
from .features import build_features


@dataclass
class LoadResult:
    ok: bool
    obj: object = None
    reason: str = ""


# --------------------------------------------------------------------------
# Capability probing — never let a missing optional dependency break a page
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def capabilities() -> dict:
    caps = {}
    for name, mod in [("joblib", "joblib"), ("xgboost", "xgboost"),
                      ("tensorflow", "tensorflow"), ("statsmodels", "statsmodels")]:
        try:
            __import__(mod)
            caps[name] = True
        except Exception:
            caps[name] = False
    return caps


def live_inference_available(model: str) -> tuple[bool, str]:
    caps = capabilities()
    needs = {"SARIMA": ["joblib", "statsmodels"],
             "XGBoost": ["joblib", "xgboost"],
             "LSTM": ["joblib", "tensorflow"]}.get(model, [])
    missing = [n for n in needs if not caps.get(n)]
    if missing:
        return False, f"{model} needs {', '.join(missing)}, which is not installed."
    reg = D.load_registry()
    for c, meta in reg.get("commodities", {}).items():
        key = model.lower()
        path = meta.get(key, {}).get("path")
        if path and not (PATHS["registry"].parent.parent / path).exists():
            return False, f"Model file missing for {c}: {path}"
    return True, ""


def _abs(rel_path: str):
    return PATHS["registry"].parent.parent / rel_path


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_sarima(commodity: str) -> LoadResult:
    try:
        import joblib
        meta = D.load_registry()["commodities"][commodity]["sarima"]
        return LoadResult(True, joblib.load(_abs(meta["path"])))
    except Exception as e:
        return LoadResult(False, reason=str(e))


@st.cache_resource(show_spinner=False)
def load_xgboost(commodity: str) -> LoadResult:
    try:
        import xgboost as xgb
        meta = D.load_registry()["commodities"][commodity]["xgboost"]
        m = xgb.XGBRegressor()
        m.load_model(str(_abs(meta["path"])))
        return LoadResult(True, m)
    except Exception as e:
        return LoadResult(False, reason=str(e))


@st.cache_resource(show_spinner=False)
def load_lstm(commodity: str) -> LoadResult:
    try:
        import joblib
        from tensorflow.keras.models import load_model
        meta = D.load_registry()["commodities"][commodity]["lstm"]
        model = load_model(_abs(meta["path"]))
        scaler = joblib.load(_abs(meta["scaler"]))
        return LoadResult(True, {"model": model, "scaler": scaler,
                                 "lookback": meta.get("lookback", 30)})
    except Exception as e:
        return LoadResult(False, reason=str(e))


@st.cache_data(show_spinner=False)
def residual_std(commodity: str) -> dict:
    path = PATHS["metrics_dir"] / f"{commodity}_residual_std.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Recursive forecasters (identical logic to notebook Phase 9)
# --------------------------------------------------------------------------
def _widen(steps: int) -> np.ndarray:
    return np.sqrt(np.arange(1, steps + 1))


def forecast_sarima(commodity: str, steps: int) -> pd.DataFrame:
    res = load_sarima(commodity)
    if not res.ok:
        raise RuntimeError(res.reason)
    fc = res.obj.get_forecast(steps=steps)
    ci = fc.conf_int(alpha=0.05)
    return pd.DataFrame({
        "date": pd.DatetimeIndex(fc.predicted_mean.index),
        "forecast": fc.predicted_mean.values,
        "lower": ci.iloc[:, 0].values,
        "upper": ci.iloc[:, 1].values,
        "horizon_day": np.arange(1, steps + 1),
    })


def forecast_xgboost(commodity: str, steps: int, delta_target: bool = True) -> pd.DataFrame:
    res = load_xgboost(commodity)
    if not res.ok:
        raise RuntimeError(res.reason)
    model = res.obj
    reg = D.load_registry()
    feature_cols = reg.get("feature_columns", [])
    s = D.price_series(commodity).copy()
    sd = residual_std(commodity).get("xgb_resid_std", float(s.diff().std()))

    preds, dates = [], []
    for _ in range(steps):
        next_date = s.index[-1] + pd.Timedelta(days=1)
        s_ext = pd.concat([s, pd.Series([np.nan], index=[next_date])])
        feats = build_features(s_ext)
        row = feats.iloc[[-1]][feature_cols] if feature_cols else feats.iloc[[-1]].drop(columns="price")
        if row.isna().to_numpy().any():
            row = row.fillna(feats[row.columns].ffill().iloc[-1]).fillna(0.0)
        raw = float(model.predict(row)[0])
        yhat = float(row["lag_1"].iloc[0]) + raw if delta_target else raw
        preds.append(yhat)
        dates.append(next_date)
        s = pd.concat([s, pd.Series([yhat], index=[next_date])])

    vals = np.array(preds)
    w = _widen(steps)
    return pd.DataFrame({"date": pd.DatetimeIndex(dates), "forecast": vals,
                         "lower": vals - 1.96 * sd * w, "upper": vals + 1.96 * sd * w,
                         "horizon_day": np.arange(1, steps + 1)})


def forecast_lstm(commodity: str, steps: int) -> pd.DataFrame:
    res = load_lstm(commodity)
    if not res.ok:
        raise RuntimeError(res.reason)
    model, scaler, lookback = res.obj["model"], res.obj["scaler"], res.obj["lookback"]
    s = D.price_series(commodity)
    sd = residual_std(commodity).get("lstm_resid_std", float(s.diff().std()))

    scaled = scaler.transform(s.values.reshape(-1, 1)).flatten()
    window = list(scaled[-lookback:])
    out = []
    for _ in range(steps):
        x = np.array(window[-lookback:]).reshape(1, lookback, 1)
        out.append(float(model.predict(x, verbose=0)[0, 0]))
        window.append(out[-1])
    vals = scaler.inverse_transform(np.array(out).reshape(-1, 1)).flatten()
    dates = pd.date_range(s.index[-1] + pd.Timedelta(days=1), periods=steps, freq="D")
    w = _widen(steps)
    return pd.DataFrame({"date": dates, "forecast": vals,
                         "lower": vals - 1.96 * sd * w, "upper": vals + 1.96 * sd * w,
                         "horizon_day": np.arange(1, steps + 1)})


FORECASTERS = {"SARIMA": forecast_sarima, "XGBoost": forecast_xgboost, "LSTM": forecast_lstm}


def get_forecast(commodity: str, model: str, horizon: int, live: bool = False) -> pd.DataFrame:
    """Single entry point. Falls back to precomputed if live inference fails."""
    if live and model in FORECASTERS:
        try:
            with st.spinner(f"Running {model} inference for {horizon} days..."):
                return FORECASTERS[model](commodity, horizon)
        except Exception as e:
            st.warning(f"Live {model} inference unavailable ({e}). Showing precomputed forecast.")
    return D.forecast_for(commodity, model, horizon)
