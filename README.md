# Essential Commodity Price Monitor — Streamlit dashboard

Forecasting price and inflation of daily essential commodities in Bangladesh, using SARIMA,
XGBoost and LSTM. This dashboard is the presentation layer of the project: it **reads** the
artifacts produced by the Colab notebook and never trains anything.

---

## Quick start

```bash
pip install -r requirements.txt

# preview immediately with sample data
python bootstrap_demo.py
streamlit run Home.py
```

Then open http://localhost:8501.

## Using your real forecasts

Run the Colab notebook through Phase 10, download `bd_forecasting_artifacts.zip`, and unzip it so
`data/` and `artifacts/` sit beside `Home.py`, replacing the demo folders:

```
streamlit_dashboard/
├── Home.py
├── data/            <- from the notebook zip
│   ├── processed/
│   └── predictions/
└── artifacts/       <- from the notebook zip
    ├── models/
    ├── scalers/
    ├── metrics/
    └── registry.json
```

Nothing else changes. If you prefer to keep the artifacts elsewhere, point the app at them:

```bash
export BD_DATA_ROOT=/path/to/bd_price_forecasting
streamlit run Home.py
```

The app reads `artifacts/registry.json` first — that manifest is the contract between the
notebook and the dashboard.

---

## Pages

| Page | Contents |
|---|---|
| **Home** | Project overview, objectives, current price snapshot, method summary |
| **Historical Analysis** | Price history, trend, seasonality, realised inflation, descriptive statistics |
| **Forecast** | Product, model and horizon selection; forecast with 95% intervals; export |
| **Inflation** | Daily, weekly, monthly and annual inflation; forward projections; composite basket |
| **Model Comparison** | Metrics table, diagnostic charts, written performance verdict |
| **Insights** | Automatically generated trend, volatility, consumer and policy readings |
| **Downloads** | Every table as CSV/JSON, charts as HTML/PNG, a summary report, and a full bundle |

---

## Architecture

```
Home.py                 landing page
pages/                  one file per page, layout and interaction only
app/
  config.py             paths, palette, commodity metadata
  theme.py              CSS, page headers, KPI cards
  ui.py                 shared sidebar controls and filters
  data.py               cached loaders and derived series
  charts.py             every Plotly figure
  models.py             artifact loading and live inference
  features.py           feature builder mirroring the notebook
  insights.py           automatic insight generation
  report.py             CSV/chart/HTML exports
  compat.py             Streamlit version shims
bootstrap_demo.py       generates sample artifacts
run_tests.py            headless smoke test of every page
run_interaction_tests.py exercises every control
```

Three rules keep it fast and maintainable:

1. **Pages contain no business logic.** They read the user's choices, call a service, and hand
   the result to a chart. If a page exceeds roughly 150 lines, something belongs in `app/`.
2. **Data is cached with `@st.cache_data`, models with `@st.cache_resource`.** Data is copied
   per call; models are shared. Getting this backwards is the usual cause of a slow Streamlit
   app.
3. **Precomputed forecasts are the default.** Live inference is an opt-in toggle on the Forecast
   page and degrades gracefully when a model file or library is missing — so a demonstration
   cannot fail because TensorFlow is not installed.

---

## Optional dependencies

The dashboard runs on `streamlit`, `pandas`, `numpy` and `plotly` alone. The rest unlock extras:

| Package | Enables |
|---|---|
| `statsmodels`, `joblib` | live SARIMA inference |
| `xgboost` | live XGBoost inference |
| `tensorflow` | live LSTM inference |
| `kaleido` | PNG chart export (HTML export always works) |

Missing packages disable the relevant control with an explanation rather than raising.

---

## Testing

```bash
python run_tests.py              # every page renders without error
python run_interaction_tests.py  # every selector, radio, slider and toggle
```

Both run headlessly through Streamlit's `AppTest` harness — no browser needed.

---

## Deploying

**Streamlit Community Cloud.** Push the folder to GitHub, point the app at `Home.py`. Model
files can exceed the repository size limit; either commit only `data/` and `artifacts/metrics/`
plus `registry.json` (precomputed mode works fully without the model binaries) or use Git LFS.

**Locally for a viva.** `streamlit run Home.py` and present from `localhost`. Precomputed mode
needs no network and cannot fail mid-demonstration.

---

## Notes on interpretation

Figures shown are model output, not official statistics. Metrics on the Model Comparison page
come from one-step-ahead prediction on a held-out test period; multi-step forecasts on the
Forecast page are materially less accurate, which is why their intervals widen with the horizon.
Composite basket weights are currently equal — replacing them with household consumption shares
would make the composite figure directly comparable with published BBS inflation.
