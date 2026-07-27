"""Downloads — take the data, the charts and the report away with you."""
import streamlit as st

from app import charts, data as D, report as R
from app.config import pretty_name
from app.theme import note, page_header, section, setup_page
from app.ui import commodity_picker, sidebar_controls
from app.compat import STRETCH, html_embed

setup_page("Downloads")
D.require_artifacts()
state = sidebar_controls(show_horizon=True)
dark = state["dark"]
horizon = state["horizon"]

page_header(
    "Downloads",
    "Export the evidence",
    "Every table behind this dashboard, the charts as standalone files, and a summary report "
    "you can print or attach.",
)

# ==========================================================================
# 1 · Forecast data
# ==========================================================================
section("Forecast data")
fc = D.load_forecasts()
if fc.empty:
    st.info("No forecasts found.")
else:
    filters = st.container(border=True)
    c1, c2 = filters.columns([2, 3], gap="large")
    with c1:
        scope = st.radio("Scope", ["Best model only", "All models"], index=0, key="dl_scope")
        commodities = st.multiselect("Commodities", D.commodities(), default=D.commodities(),
                                     format_func=pretty_name, key="dl_comm")
    sub = fc[(fc["commodity"].isin(commodities)) & (fc["horizon_day"] <= horizon)]
    if scope == "Best model only" and "is_best_model" in sub:
        sub = sub[sub["is_best_model"]]
    with c2:
        st.metric("Rows selected", f"{len(sub):,}", border=True)
        st.caption(f"Horizon capped at {horizon} days by the sidebar slider.")

    st.dataframe(sub.head(200), **STRETCH, hide_index=True, height=260)
    d1, d2 = st.columns(2, gap="small")
    d1.download_button("Forecast (CSV)", R.df_to_csv_bytes(sub),
                       file_name=f"forecasts_{horizon}d.csv", mime="text/csv",
                       icon=":material/table_view:", **STRETCH)
    d2.download_button("Forecast (JSON)",
                       sub.to_json(orient="records", date_format="iso", indent=2).encode(),
                       file_name=f"forecasts_{horizon}d.json", mime="application/json",
                       icon=":material/data_object:", **STRETCH)

# ==========================================================================
# 2 · Other tables
# ==========================================================================
section("Supporting tables")
TABLES = [
    ("Price history", D.load_prices, "price_history.csv",
     "Cleaned daily prices for every commodity."),
    ("Future inflation", D.load_inflation, "future_inflation.csv",
     "Projected inflation by commodity, model and horizon."),
    ("Composite index", D.load_composite, "composite_inflation.csv",
     "Weighted essential-goods basket."),
    ("Model comparison", D.load_comparison, "model_comparison.csv",
     "Accuracy metrics on the held-out test set."),
    ("Test predictions", D.load_test_predictions, "test_predictions.csv",
     "Actual versus predicted values used to compute those metrics."),
]
for label, loader, fname, desc in TABLES:
    df = loader()
    row = st.container(border=True)
    col_a, col_b, col_c = row.columns([2.4, 1.2, 1.4], gap="medium",
                                      vertical_alignment="center")
    col_a.markdown(f"**{label}**  \n<span class='bd-meta'>{desc}</span>",
                   unsafe_allow_html=True)
    col_b.markdown(f"<span class='bd-meta-num'>{len(df):,} rows</span>" if not df.empty
                   else "<span class='bd-meta-num'>not available</span>",
                   unsafe_allow_html=True)
    if df.empty:
        col_c.button("Download", key=f"dl_{fname}", disabled=True,
                     icon=":material/download:", **STRETCH)
    else:
        col_c.download_button("Download", R.df_to_csv_bytes(df), file_name=fname,
                              mime="text/csv", key=f"dl_{fname}",
                              icon=":material/download:", **STRETCH)

# ==========================================================================
# 3 · Charts
# ==========================================================================
section("Charts")
st.caption("Interactive HTML keeps the zoom, hover and legend controls and opens in any "
           "browser. PNG needs the optional kaleido package.")

ch1, ch2 = st.columns([2, 3], gap="large")
with ch1.container(border=True):
    chart_commodity = commodity_picker("Commodity", key="dl_chart_commodity")
    chart_kind = st.selectbox("Chart", ["Forecast", "Price history", "Trend",
                                        "Seasonal pattern", "Monthly heatmap"],
                              key="dl_chart_kind")

history = D.price_series(chart_commodity)
if chart_kind == "Forecast":
    best = D.best_model(chart_commodity)
    fig = charts.forecast_chart(history,
                                {best: D.forecast_for(chart_commodity, best, horizon)},
                                chart_commodity, dark=dark)
    stem = f"{chart_commodity}_forecast_{horizon}d"
elif chart_kind == "Price history":
    fig = charts.price_history({chart_commodity: history}, dark=dark)
    stem = f"{chart_commodity}_price_history"
elif chart_kind == "Trend":
    fig = charts.trend_chart(history, chart_commodity, dark=dark)
    stem = f"{chart_commodity}_trend"
elif chart_kind == "Seasonal pattern":
    fig = charts.seasonality_chart(history, chart_commodity, dark=dark)
    stem = f"{chart_commodity}_seasonality"
else:
    fig = charts.monthly_heatmap(history, dark=dark)
    stem = f"{chart_commodity}_monthly_heatmap"

with ch2:
    st.plotly_chart(fig, **STRETCH)

g1, g2 = st.columns(2, gap="small")
g1.download_button("Chart (HTML)", R.fig_to_html_bytes(fig), file_name=f"{stem}.html",
                   mime="text/html", icon=":material/code:", **STRETCH)
png = R.fig_to_png_bytes(fig)
if png:
    g2.download_button("Chart (PNG)", png, file_name=f"{stem}.png", mime="image/png",
                       icon=":material/image:", **STRETCH)
else:
    g2.button("Chart (PNG)", disabled=True, icon=":material/image:", **STRETCH,
              help="Install kaleido to enable PNG export: pip install kaleido")

# ==========================================================================
# 4 · Summary report
# ==========================================================================
section("Summary report")
st.markdown(
    "A self-contained HTML document covering the market overview, per-commodity readings, "
    "projected inflation, model accuracy and the method notes. It uses no external files, so "
    "it opens offline and prints to PDF cleanly from any browser.")

r1, r2 = st.columns([1, 1], gap="small")
r1.download_button("Summary report (HTML)", R.build_html_report(horizon).encode("utf-8"),
                   file_name=f"forecast_summary_{horizon}d.html", mime="text/html",
                   icon=":material/description:", **STRETCH)
r2.download_button("Everything (ZIP)", R.build_full_bundle(horizon),
                   file_name=f"bd_price_forecast_bundle_{horizon}d.zip",
                   mime="application/zip", icon=":material/folder_zip:", **STRETCH)

with st.expander("Preview the report", icon=":material/visibility:"):
    html_embed(R.build_html_report(horizon), height=620)

note("To produce a PDF, download the HTML report, open it in a browser and print to PDF. "
     "The stylesheet includes print rules that keep sections and cards from breaking across "
     "pages.")
