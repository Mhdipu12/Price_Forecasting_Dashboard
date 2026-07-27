"""Forecast — pick a commodity, a model and a horizon, and see what happens next."""
import pandas as pd
import streamlit as st

from app import charts, data as D, models as M
from app.config import pretty_name, style_for, unit_for
from app.report import df_to_csv_bytes, fig_to_html_bytes, fig_to_png_bytes
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import commodity_picker, sidebar_controls
from app.compat import STRETCH

setup_page("Forecast")
D.require_artifacts()
state = sidebar_controls(show_horizon=True)
dark = state["dark"]
horizon = state["horizon"]

page_header(
    "Forecast",
    "What happens next",
    "Every forecast is produced recursively, so uncertainty widens with distance. "
    "The shaded band is a 95% interval, not a guarantee.",
)

# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------
filters = st.container(border=True)
c1, c2, c3 = filters.columns([2, 2, 2], gap="large", vertical_alignment="bottom")
with c1:
    commodity = commodity_picker("Product", key="fc_commodity")
with c2:
    all_models = D.available_models(commodity)
    best = D.best_model(commodity)
    options = [f"Best model ({best})"] + all_models + ["Compare all models"]
    choice = st.selectbox("Model", options, index=0, key="fc_model")
with c3:
    show_ci = st.checkbox("Show 95% confidence interval", value=True)

if choice.startswith("Best model"):
    selected, highlight = [best], best
elif choice == "Compare all models":
    selected, highlight = all_models, best
else:
    selected, highlight = [choice], choice

live = False
with st.expander("Advanced: run the models live instead of using precomputed forecasts",
                 icon=":material/tune:"):
    st.markdown(
        "Precomputed forecasts load instantly and are what the project reports. Live inference "
        "re-runs the saved model for the exact horizon you chose, which is slower and requires "
        "the model files and their libraries to be present.")
    ready, reason = M.live_inference_available(highlight)
    live = st.toggle("Run live inference", value=False, disabled=not ready,
                     help=reason or "Loads the serialized model and forecasts on demand.")
    if not ready:
        st.caption(reason)

# --------------------------------------------------------------------------
# Build forecasts
# --------------------------------------------------------------------------
history = D.price_series(commodity)
unit = unit_for(commodity)
forecasts = {m: M.get_forecast(commodity, m, horizon, live=live and m == highlight)
             for m in selected}
forecasts = {m: df for m, df in forecasts.items() if not df.empty}

if not forecasts:
    st.warning("No forecast is available for this combination. Re-run Phase 9 of the notebook.")
    st.stop()

main = forecasts[highlight] if highlight in forecasts else next(iter(forecasts.values()))
last_price = float(history.iloc[-1])
end_price = float(main["forecast"].iloc[-1])
change = (end_price - last_price) / last_price * 100
accent = style_for(commodity)["color"]
band = (float(main["upper"].iloc[-1]) - float(main["lower"].iloc[-1])) / 2

render_kpis([
    kpi_card("Latest observed", f"{last_price:,.2f}", unit, accent=accent,
             delta_caption=str(history.index[-1].date())),
    kpi_card(f"Forecast in {horizon} days", f"{end_price:,.2f}", unit, delta=change,
             delta_caption="vs today", accent=accent),
    kpi_card("Forecast range", f"±{band:,.2f}", unit, accent=accent,
             delta_caption="95% interval at final day"),
    kpi_card("Period average", f"{main['forecast'].mean():,.2f}", unit, accent=accent,
             delta_caption=f"mean of {horizon} days"),
], per_row=4)

# --------------------------------------------------------------------------
# Chart
# --------------------------------------------------------------------------
section("Future forecast")
lookback = st.select_slider("History shown", options=[60, 90, 180, 365, 730], value=180,
                            format_func=lambda v: f"{v} days")
fig = charts.forecast_chart(history, forecasts, commodity, show_ci=show_ci,
                            highlight=highlight, lookback=lookback, dark=dark)
st.plotly_chart(fig, **STRETCH)

if len(forecasts) > 1:
    st.caption(f"The solid line is {highlight}, selected as the best model for "
               f"{pretty_name(commodity)}. Dotted lines are the alternatives. Where they "
               f"diverge sharply, treat the forecast as genuinely uncertain rather than "
               f"picking whichever number you prefer.")

# --------------------------------------------------------------------------
# Uncertainty and table
# --------------------------------------------------------------------------
left, right = st.columns([1, 1], gap="large")
with left:
    section("How uncertainty grows")
    st.plotly_chart(charts.horizon_uncertainty(main, commodity, dark=dark),
                    **STRETCH)
    note("Each day's forecast is built on the previous day's forecast, so errors accumulate. "
         "The band widens roughly with the square root of the horizon. A 60-day number is a "
         "direction of travel, not a price you should plan a budget around.")
with right:
    section("Milestones")
    marks = [d for d in (7, 14, 30, 45, 60) if d <= horizon]
    rows = []
    for d in marks:
        r = main[main["horizon_day"] == d]
        if r.empty:
            continue
        r = r.iloc[0]
        rows.append({
            "Days ahead": d,
            "Date": pd.to_datetime(r["date"]).date(),
            f"Forecast ({unit})": round(float(r["forecast"]), 2),
            "Change %": round((float(r["forecast"]) - last_price) / last_price * 100, 2),
            "Low": round(float(r["lower"]), 2),
            "High": round(float(r["upper"]), 2),
        })
    if rows:
        st.dataframe(rows, **STRETCH, hide_index=True)

section("Forecast table")
table = main.copy()
table["date"] = pd.to_datetime(table["date"]).dt.date
table["change_%"] = (table["forecast"] - last_price) / last_price * 100
table = table[["horizon_day", "date", "forecast", "lower", "upper", "change_%"]].round(3)
table.columns = ["Day", "Date", f"Forecast ({unit})", "Lower 95%", "Upper 95%", "Change %"]
st.dataframe(table, **STRETCH, hide_index=True, height=300)

# --------------------------------------------------------------------------
# Downloads
# --------------------------------------------------------------------------
section("Export")
d1, d2, d3 = st.columns(3, gap="small")
d1.download_button("Forecast (CSV)", df_to_csv_bytes(table),
                   file_name=f"{commodity}_{highlight}_{horizon}d_forecast.csv",
                   mime="text/csv", icon=":material/table_view:", **STRETCH)
d2.download_button("Chart (interactive HTML)", fig_to_html_bytes(fig),
                   file_name=f"{commodity}_forecast_chart.html",
                   mime="text/html", icon=":material/code:", **STRETCH)
png = fig_to_png_bytes(fig)
if png:
    d3.download_button("Chart (PNG)", png, file_name=f"{commodity}_forecast_chart.png",
                       mime="image/png", icon=":material/image:", **STRETCH)
else:
    d3.button("Chart (PNG)", disabled=True, icon=":material/image:", **STRETCH,
              help="PNG export needs the kaleido package: pip install kaleido")

# --------------------------------------------------------------------------
# Model context
# --------------------------------------------------------------------------
comp = D.load_comparison()
if not comp.empty:
    sub = comp[(comp["commodity"] == commodity) & (comp["model"] == highlight)]
    if not sub.empty:
        r = sub.iloc[0]
        st.caption(
            f"On the held-out test period, {highlight} achieved MAE {r['MAE']:.3f} BDT, "
            f"RMSE {r['RMSE']:.3f}, MAPE {r['MAPE_%']:.2f}% and R² {r['R2']:.3f}, "
            f"beating the seasonal naive baseline by {r['skill_vs_naive_%']:.1f}%. "
            f"Those figures come from one-step-ahead prediction; multi-step accuracy is lower.")
