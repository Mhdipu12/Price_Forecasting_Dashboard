"""Feature builder for live inference.

This is a verbatim copy of `build_features` from the Colab notebook. It must
stay identical — if the two ever diverge, the model receives inputs that differ
from its training distribution and quietly degrades. `verify_against_registry`
checks the column list against `registry.json` on load so drift is caught at
startup rather than in a forecast.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = [1, 2, 3, 7, 14, 30]
ROLLING_WINDOWS = [7, 14, 30]
EMA_SPANS = [7, 30]


def build_features(price: pd.Series) -> pd.DataFrame:
    s = price.astype(float).copy()
    s.name = "price"
    X = pd.DataFrame(index=s.index)
    X["price"] = s

    idx = s.index
    X["year"] = idx.year
    X["month"] = idx.month
    X["week"] = idx.isocalendar().week.astype(int)
    X["day"] = idx.day
    X["dayofweek"] = idx.dayofweek
    X["dayofyear"] = idx.dayofyear
    X["quarter"] = idx.quarter
    X["is_weekend"] = idx.dayofweek.isin([4, 5]).astype(int)
    X["is_month_start"] = idx.is_month_start.astype(int)
    X["is_month_end"] = idx.is_month_end.astype(int)
    X["month_sin"] = np.sin(2 * np.pi * X["month"] / 12)
    X["month_cos"] = np.cos(2 * np.pi * X["month"] / 12)
    X["doy_sin"] = np.sin(2 * np.pi * X["dayofyear"] / 365.25)
    X["doy_cos"] = np.cos(2 * np.pi * X["dayofyear"] / 365.25)
    X["dow_sin"] = np.sin(2 * np.pi * X["dayofweek"] / 7)
    X["dow_cos"] = np.cos(2 * np.pi * X["dayofweek"] / 7)

    for L in LAGS:
        X[f"lag_{L}"] = s.shift(L)

    past = s.shift(1)
    for w in ROLLING_WINDOWS:
        X[f"roll_mean_{w}"] = past.rolling(w).mean()
        X[f"roll_median_{w}"] = past.rolling(w).median()
        X[f"roll_max_{w}"] = past.rolling(w).max()
        X[f"roll_min_{w}"] = past.rolling(w).min()
        X[f"roll_std_{w}"] = past.rolling(w).std()
        X[f"roll_range_{w}"] = X[f"roll_max_{w}"] - X[f"roll_min_{w}"]

    for span in EMA_SPANS:
        ema = past.ewm(span=span, adjust=False).mean()
        X[f"ema_{span}"] = ema
        X[f"lag1_over_ema_{span}"] = past / ema

    X["pct_change_1"] = past.pct_change(1) * 100
    X["pct_change_7"] = past.pct_change(7) * 100
    X["pct_change_30"] = past.pct_change(30) * 100
    X["log_return_1"] = np.log(past / past.shift(1))
    X["diff_1"] = past.diff(1)
    X["diff_7"] = past.diff(7)

    X["inflation_daily"] = past.pct_change(1) * 100
    X["inflation_weekly"] = past.pct_change(7) * 100
    X["inflation_monthly"] = past.pct_change(30) * 100
    X["inflation_annual"] = past.pct_change(365) * 100

    X["volatility_7"] = past.pct_change().rolling(7).std() * 100
    X["volatility_30"] = past.pct_change().rolling(30).std() * 100
    return X


def verify_against_registry(registry: dict) -> tuple[bool, list[str]]:
    """Confirm this builder still produces the columns the models were trained on."""
    expected = registry.get("feature_columns")
    if not expected:
        return True, []
    dates = pd.date_range("2020-01-01", periods=500, freq="D")
    probe = pd.Series(np.linspace(40, 60, 500), index=dates)
    produced = [c for c in build_features(probe).columns if c != "price"]
    missing = [c for c in expected if c not in produced]
    return (len(missing) == 0), missing
