"""Generate sample artifacts so the dashboard can be previewed immediately.

Run once:

    python bootstrap_demo.py

This writes the same file layout the Colab notebook produces, using synthetic
prices and simple statistical forecasts. Replace `data/` and `artifacts/` with
the real output from the notebook when it is ready — nothing else changes.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
COMMODITIES = ["Onion", "Potato", "Soybean_Oil"]
MODELS = ["SARIMA", "XGBoost", "LSTM"]
HORIZONS = [30, 60]
MAX_H = max(HORIZONS)
N_DAYS = 1900
TEST_DAYS = 180
SEED = 42

DIRS = {
    "processed": ROOT / "data" / "processed",
    "predictions": ROOT / "data" / "predictions",
    "metrics": ROOT / "artifacts" / "metrics",
    "artifacts": ROOT / "artifacts",
}
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)
PARAMS = {
    "Onion":       dict(base=45,  drift=0.020, annual=14, noise=0.020,
                        shocks=[(430, 60, 2.4), (980, 50, 1.8), (1560, 70, 2.0)]),
    "Potato":      dict(base=25,  drift=0.008, annual=6,  noise=0.014,
                        shocks=[(700, 45, 1.5), (1400, 40, 1.4)]),
    "Soybean_Oil": dict(base=130, drift=0.038, annual=9,  noise=0.012,
                        shocks=[(820, 120, 1.6)]),
}


def synth(name: str, seed: int) -> pd.Series:
    r = np.random.default_rng(seed)
    p = PARAMS[name]
    end = pd.Timestamp.today().normalize()
    dates = pd.date_range(end - pd.Timedelta(days=N_DAYS - 1), end, freq="D")
    t = np.arange(N_DAYS)
    price = (p["base"] + p["drift"] * t
             + p["annual"] * np.sin(2 * np.pi * (t - 40) / 365.25)
             + 0.5 * np.sin(2 * np.pi * t / 7)
             + r.normal(0, p["base"] * p["noise"], N_DAYS))
    for start, length, mag in p["shocks"]:
        if start + length < N_DAYS:
            bump = np.concatenate([np.linspace(1, mag, length // 2),
                                   np.linspace(mag, 1, length - length // 2)])
            price[start:start + length] *= bump
    return pd.Series(np.round(np.maximum(price, 1.0), 2), index=dates, name="price")


def drift_forecast(s: pd.Series, steps: int, wobble: float, seed: int) -> pd.DataFrame:
    """A defensible stand-in: local level + damped drift + seasonal echo."""
    r = np.random.default_rng(seed)
    level = float(s.iloc[-7:].mean())
    slope = float(s.iloc[-30:].diff().mean())
    resid = float(s.diff().std())
    dates = pd.date_range(s.index[-1] + pd.Timedelta(days=1), periods=steps, freq="D")
    damp = np.power(0.985, np.arange(1, steps + 1))
    seasonal = float(s.iloc[-365:].std()) * 0.05 * np.sin(
        2 * np.pi * (np.arange(steps) + s.index[-1].dayofyear) / 365.25)
    vals = level + np.cumsum(slope * damp) + seasonal
    vals = vals * (1 + r.normal(0, wobble, steps).cumsum() * 0.002)
    widen = np.sqrt(np.arange(1, steps + 1))
    return pd.DataFrame({"date": dates, "forecast": np.round(vals, 3),
                         "lower": np.round(vals - 1.96 * resid * widen, 3),
                         "upper": np.round(vals + 1.96 * resid * widen, 3),
                         "horizon_day": np.arange(1, steps + 1)})


def main() -> None:
    print("Generating demo artifacts...")
    prices, forecasts, comparison, test_preds = {}, [], [], []

    for i, c in enumerate(COMMODITIES):
        prices[c] = synth(c, SEED + i)
        prices[c].reset_index().rename(columns={"index": "date"}).to_csv(
            DIRS["processed"] / f"{c}_clean.csv", index=False)

    long = pd.concat([s.to_frame().assign(commodity=c) for c, s in prices.items()])
    long = long.reset_index().rename(columns={"index": "date"})
    long.to_csv(DIRS["processed"] / "all_prices_long.csv", index=False)

    best_model = {}
    for i, c in enumerate(COMMODITIES):
        s = prices[c]
        scale = float(s.iloc[-TEST_DAYS:].std())
        actual = s.iloc[-TEST_DAYS:]

        # plausible, ordered accuracy so one model genuinely wins per commodity
        skill = {"SARIMA": [0.42, 0.30, 0.36][i],
                 "XGBoost": [0.30, 0.38, 0.28][i],
                 "LSTM": [0.36, 0.34, 0.33][i]}
        for m in MODELS:
            r = np.random.default_rng(SEED + i * 10 + MODELS.index(m))
            noise = r.normal(0, scale * skill[m], TEST_DAYS)
            pred = actual.values + noise
            err = actual.values - pred
            mae = float(np.mean(np.abs(err)))
            rmse = float(np.sqrt(np.mean(err ** 2)))
            mape = float(np.mean(np.abs(err / actual.values)) * 100)
            smape = float(np.mean(2 * np.abs(err) /
                                  (np.abs(actual.values) + np.abs(pred))) * 100)
            ss_res = float(np.sum(err ** 2))
            ss_tot = float(np.sum((actual.values - actual.values.mean()) ** 2))
            comparison.append({"commodity": c, "model": m, "MAE": mae, "RMSE": rmse,
                               "MAPE_%": mape, "sMAPE_%": smape,
                               "R2": 1 - ss_res / ss_tot})
            test_preds.append(pd.DataFrame({"date": actual.index, "actual": actual.values,
                                            "pred": pred, "lower": pred - 1.96 * scale * 0.4,
                                            "upper": pred + 1.96 * scale * 0.4,
                                            "commodity": c, "model": m}))

        naive = s.shift(7).iloc[-TEST_DAYS:]
        err = actual.values - naive.values
        comparison.append({"commodity": c, "model": "Seasonal Naive",
                           "MAE": float(np.mean(np.abs(err))),
                           "RMSE": float(np.sqrt(np.mean(err ** 2))),
                           "MAPE_%": float(np.mean(np.abs(err / actual.values)) * 100),
                           "sMAPE_%": float(np.mean(2 * np.abs(err) /
                                                    (np.abs(actual.values) + np.abs(naive.values))) * 100),
                           "R2": 1 - float(np.sum(err ** 2)) /
                                 float(np.sum((actual.values - actual.values.mean()) ** 2))})
        test_preds.append(pd.DataFrame({"date": actual.index, "actual": actual.values,
                                        "pred": naive.values, "commodity": c,
                                        "model": "Seasonal Naive"}))

    comp = pd.DataFrame(comparison)
    skill_col = []
    for _, r in comp.iterrows():
        base = comp[(comp.commodity == r["commodity"]) &
                    (comp.model == "Seasonal Naive")]["MAE"].iloc[0]
        skill_col.append((1 - r["MAE"] / base) * 100)
    comp["skill_vs_naive_%"] = skill_col
    comp.to_csv(DIRS["metrics"] / "model_comparison.csv", index=False)

    for c in COMMODITIES:
        sub = comp[(comp.commodity == c) & (comp.model != "Seasonal Naive")]
        best_model[c] = sub.sort_values("MAE").iloc[0]["model"]

    pd.concat(test_preds).to_csv(DIRS["predictions"] / "test_predictions.csv", index=False)

    # ---- forecasts ------------------------------------------------------
    for i, c in enumerate(COMMODITIES):
        for j, m in enumerate(MODELS):
            f = drift_forecast(prices[c], MAX_H, wobble=0.4 + 0.3 * j, seed=SEED + i * 7 + j)
            f["commodity"] = c
            f["model"] = m
            f["is_best_model"] = (m == best_model[c])
            forecasts.append(f)
    fc = pd.concat(forecasts)[["commodity", "model", "horizon_day", "date",
                               "forecast", "lower", "upper", "is_best_model"]]
    fc.to_csv(DIRS["predictions"] / "future_forecasts.csv", index=False)

    # ---- inflation ------------------------------------------------------
    rows = []
    for c in COMMODITIES:
        last = float(prices[c].iloc[-1])
        last30 = float(prices[c].iloc[-30:].mean())
        for m in MODELS:
            sub = fc[(fc.commodity == c) & (fc.model == m)]
            for H in HORIZONS:
                w = sub[sub.horizon_day <= H]
                pe, pm = float(w["forecast"].iloc[-1]), float(w["forecast"].mean())
                rows.append({
                    "commodity": c, "model": m, "horizon_days": H,
                    "last_actual_price": last, "forecast_price_end": pe,
                    "forecast_price_mean": pm,
                    "inflation_%": (pe - last) / last * 100,
                    "inflation_lower_%": (float(w["lower"].iloc[-1]) - last) / last * 100,
                    "inflation_upper_%": (float(w["upper"].iloc[-1]) - last) / last * 100,
                    "avg_basis_inflation_%": (pm - last30) / last30 * 100,
                    "annualised_inflation_%": ((pe / last) ** (365 / H) - 1) * 100,
                    "is_best_model": m == best_model[c]})
    infl = pd.DataFrame(rows)
    infl.to_csv(DIRS["predictions"] / "future_inflation.csv", index=False)
    infl.to_csv(DIRS["metrics"] / "inflation_summary.csv", index=False)

    # ---- composite ------------------------------------------------------
    weights = {c: 1 / len(COMMODITIES) for c in COMMODITIES}
    comp_rows = []
    for H in HORIZONS:
        now = fut = 0.0
        contrib = {}
        for c in COMMODITIES:
            last = float(prices[c].iloc[-1])
            v = float(fc[(fc.commodity == c) & (fc.model == best_model[c])
                         & (fc.horizon_day == H)]["forecast"].iloc[0])
            now += weights[c] * 100
            fut += weights[c] * (v / last * 100)
            contrib[f"{c}_contrib_%"] = weights[c] * (v / last - 1) * 100
        comp_rows.append({"horizon_days": H, "index_now": now, "index_forecast": fut,
                          "composite_inflation_%": (fut - now) / now * 100, **contrib})
    pd.DataFrame(comp_rows).to_csv(DIRS["predictions"] / "composite_inflation.csv", index=False)

    # ---- forecast table + registry --------------------------------------
    table = []
    for c in COMMODITIES:
        last = float(prices[c].iloc[-1])
        sub = fc[(fc.commodity == c) & (fc.model == best_model[c])]
        for _, r in sub.iterrows():
            table.append({"Commodity": c, "Model": best_model[c], "Day": int(r["horizon_day"]),
                          "Date": pd.to_datetime(r["date"]).date(),
                          "Forecast_BDT": round(float(r["forecast"]), 2),
                          "Lower_95_BDT": round(float(r["lower"]), 2),
                          "Upper_95_BDT": round(float(r["upper"]), 2),
                          "Change_vs_today_%": round((r["forecast"] - last) / last * 100, 3)})
    pd.DataFrame(table).to_csv(DIRS["predictions"] / "forecast_table_best_model.csv", index=False)

    from app.features import build_features
    feature_cols = [c for c in build_features(prices["Onion"]).columns if c != "price"]

    registry = {
        "project": "BD Essential Commodity Price & Inflation Forecasting (DEMO DATA)",
        "generated_at": datetime.now().isoformat(), "seed": SEED, "lookback": 30,
        "feature_columns": feature_cols, "horizons": HORIZONS, "test_days": TEST_DAYS,
        "demo": True, "commodities": {},
    }
    for i, c in enumerate(COMMODITIES):
        metrics = comp[comp.commodity == c].set_index("model")[
            ["MAE", "RMSE", "MAPE_%", "sMAPE_%", "R2", "skill_vs_naive_%"]].to_dict("index")
        registry["commodities"][c] = {
            "best_model": best_model[c],
            "data_start": str(prices[c].index.min().date()),
            "data_end": str(prices[c].index.max().date()),
            "n_observations": int(len(prices[c])),
            "last_price": float(prices[c].iloc[-1]),
            "sarima": {"path": f"artifacts/models/sarima/{c}_sarima.pkl",
                       "order": [1, 1, 1], "seasonal_order": [1, 0, 1, 7],
                       "aic": 4200.0 + i * 130},
            "xgboost": {"path": f"artifacts/models/xgboost/{c}_xgboost.json", "params": {}},
            "lstm": {"path": f"artifacts/models/lstm/{c}_lstm.keras",
                     "scaler": f"artifacts/scalers/{c}_minmax_scaler.pkl",
                     "lookback": 30, "best_epoch": 40 + i * 6},
            "residual_std": f"artifacts/metrics/{c}_residual_std.json",
            "metrics": metrics,
        }
        with open(DIRS["metrics"] / f"{c}_residual_std.json", "w") as f:
            json.dump({"xgb_resid_std": float(prices[c].diff().std()),
                       "lstm_resid_std": float(prices[c].diff().std() * 1.1)}, f, indent=2)

    with open(DIRS["artifacts"] / "registry.json", "w") as f:
        json.dump(registry, f, indent=2, default=str)
    with open(DIRS["metrics"] / "best_model.json", "w") as f:
        json.dump(best_model, f, indent=2)

    print(f"  {N_DAYS} daily observations per commodity")
    print(f"  best models: {best_model}")
    print(f"  written under {ROOT}/data and {ROOT}/artifacts")
    print("\nDemo artifacts ready. Start the dashboard with:  streamlit run Home.py")
    print("Replace data/ and artifacts/ with the notebook's output to use real forecasts.")


if __name__ == "__main__":
    main()
