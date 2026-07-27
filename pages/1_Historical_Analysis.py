"""Historical Analysis — price, trend, inflation and descriptive statistics."""
import pandas as pd
import streamlit as st

from app import charts, data as D
from app.config import pretty_name, style_for, unit_for
from app.report import df_to_csv_bytes
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import commodity_picker, date_range_picker, sidebar_controls
from app.compat import STRETCH

setup_page("Historical Analysis")
D.require_artifacts()
state = sidebar_controls()
dark = state["dark"]

page_header(
    "Historical analysis",
    "What prices have done",
    "Filter by commodity and period, then read the level, the trend, the realised inflation "
    "and the summary statistics behind them.",
)

# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------
filters = st.container(border=True)
f1, f2, f3 = filters.columns([2, 2, 2], gap="large")
with f1:
    commodity = commodity_picker(key="hist_commodity")
with f2:
    full = D.price_series(commodity)
    start, end = date_range_picker(full.index, key="hist")
with f3:
    compare = st.multiselect("Compare with", [c for c in D.commodities() if c != commodity],
                             format_func=pretty_name, key="hist_compare")

s = full[(full.index >= pd.Timestamp(start)) & (full.index <= pd.Timestamp(end))]
if s.empty:
    st.warning("No observations in the selected period. Widen the date range.")
    st.stop()

unit = unit_for(commodity)
accent = style_for(commodity)["color"]

# --------------------------------------------------------------------------
# Period KPIs
# --------------------------------------------------------------------------
chg = (s.iloc[-1] - s.iloc[0]) / s.iloc[0] * 100 if s.iloc[0] else float("nan")
render_kpis([
    kpi_card("Period average", f"{s.mean():,.2f}", unit, accent=accent),
    kpi_card("Period low", f"{s.min():,.2f}", unit, accent=accent,
             delta_caption=str(s.idxmin().date())),
    kpi_card("Period high", f"{s.max():,.2f}", unit, accent=accent,
             delta_caption=str(s.idxmax().date())),
    kpi_card("Change over period", f"{s.iloc[-1]:,.2f}", unit, delta=chg,
             delta_caption="start to end", accent=accent,
             ribbon=(float(s.min()), float(s.max()), float(s.iloc[-1]))),
], per_row=4)

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab_price, tab_trend, tab_infl, tab_stats = st.tabs([
    ":material/show_chart: Historical price",
    ":material/trending_up: Trend and seasonality",
    ":material/percent: Realised inflation",
    ":material/functions: Statistics",
])

with tab_price:
    series = {commodity: s}
    for c in compare:
        other = D.price_series(c)
        series[c] = other[(other.index >= pd.Timestamp(start)) & (other.index <= pd.Timestamp(end))]
    norm = st.checkbox("Rebase all series to 100 at period start", value=bool(compare),
                       help="Compares how much each price moved rather than what it costs.")
    st.plotly_chart(charts.price_history(series, dark=dark, height=440, normalise=norm),
                    **STRETCH)
    st.caption("Drag inside the chart to zoom; use the slider beneath it to scrub through time.")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        section("Distribution")
        st.plotly_chart(charts.distribution_chart(s, commodity, dark=dark),
                        **STRETCH)
    with c2:
        section("Average price by year and month")
        st.plotly_chart(charts.monthly_heatmap(s, dark=dark), **STRETCH)
        st.caption("Read down a column: if the same month is consistently hot across years, "
                   "seasonality is stable and a seasonal model will generalise.")

with tab_trend:
    section("Price against its moving averages")
    st.plotly_chart(charts.trend_chart(s, commodity, dark=dark), **STRETCH)
    note("The 30-day average tracks short swings, the 90-day shows the medium-term direction, "
         "and the 365-day average is the underlying trend with seasonality removed. When the "
         "short average crosses above the long one and stays there, the market has changed "
         "level rather than merely fluctuated.")

    section("Seasonal pattern")
    if len(full) > 400:
        st.plotly_chart(charts.seasonality_chart(full, commodity, dark=dark),
                        **STRETCH)
        st.caption("Computed on the full history and de-trended, so each bar shows how much "
                   "that month typically deviates from the year's own trend.")
    else:
        st.info("At least 400 observations are needed to separate seasonality from trend.")

with tab_infl:
    infl = D.inflation_series(commodity)
    infl = infl[(infl.index >= pd.Timestamp(start)) & (infl.index <= pd.Timestamp(end))]
    freq = st.radio("Frequency", ["Weekly", "Monthly", "Annual", "Daily"],
                    horizontal=True, key="hist_infl_freq")
    col = {"Daily": "daily_%", "Weekly": "weekly_%",
           "Monthly": "monthly_%", "Annual": "annual_%"}[freq]
    st.plotly_chart(
        charts.inflation_chart(infl, col, commodity, dark=dark, height=380,
                               title=f"{freq} price inflation — {pretty_name(commodity)}"),
        **STRETCH)

    d = infl[col].dropna()
    if len(d):
        render_kpis([
            kpi_card(f"Average {freq.lower()} inflation", f"{d.mean():+,.2f}", "%", accent=accent),
            kpi_card("Most recent", f"{d.iloc[-1]:+,.2f}", "%", accent=accent),
            kpi_card("Highest", f"{d.max():+,.2f}", "%", accent=accent,
                     delta_caption=str(d.idxmax().date())),
            kpi_card("Lowest", f"{d.min():+,.2f}", "%", accent=accent,
                     delta_caption=str(d.idxmin().date())),
        ], per_row=4)
    note("Red areas are periods when the price rose against the comparison window; green areas "
         "are periods when it fell. Annual inflation compares each day with the same day one "
         "year earlier, which removes seasonality entirely — it is the measure most comparable "
         "to official statistics.")

with tab_stats:
    section("Descriptive statistics")
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        stats = D.descriptive_stats(commodity, start, end)
        st.dataframe(stats, **STRETCH, hide_index=True, height=430)
        st.download_button("Download statistics (CSV)", df_to_csv_bytes(stats),
                           file_name=f"{commodity}_statistics.csv", mime="text/csv",
                           icon=":material/download:")
    with right.container(border=True):
        st.markdown("""
##### Reading these numbers

**Coefficient of variation** normalises dispersion by the price level, so commodities with very
different prices can be compared directly. Above roughly 25% the series is volatile, and
volatility is what makes forecasting hard.

**Skewness** above zero means occasional violent spikes above a normal floor — the signature of
a supply-constrained agricultural commodity.

**Kurtosis** well above 3 means fat tails: extreme days occur far more often than a normal
distribution allows, which is why the confidence intervals on the Forecast page should be
treated as optimistic during a shock.

**Annualised volatility** scales daily variation to a yearly figure, making it comparable with
financial risk measures.
""")

    section("Full price history")
    table = s.reset_index()
    table.columns = ["Date", f"Price ({unit})"]
    st.dataframe(table.iloc[::-1], **STRETCH, hide_index=True, height=320)
    st.download_button("Download price history (CSV)", df_to_csv_bytes(table),
                       file_name=f"{commodity}_prices_{start}_{end}.csv", mime="text/csv",
                       icon=":material/download:")
