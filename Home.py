"""Home — project overview, objectives, and the current price snapshot."""
import streamlit as st

from app import charts, data as D, insights as I
from app.config import APP_SUBTITLE, pretty_name, style_for, unit_for
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import sidebar_controls
from app.compat import STRETCH

setup_page("Home")
D.require_artifacts()
state = sidebar_controls()
dark = state["dark"]

page_header(
    "Overview",
    "Essential Commodity Price Monitor",
    APP_SUBTITLE + ". Daily retail prices for onion, potato and soybean oil in Bangladesh, "
    "with forward projections and the evidence behind them.",
)

# --------------------------------------------------------------------------
# Current snapshot
# --------------------------------------------------------------------------
section("Where prices stand today")
st.caption("The marker on each ribbon shows where today's price sits inside its own "
           "52-week range — left is cheap, right is dear.")

cards = []
for c in D.commodities():
    snap = D.latest_snapshot(c)
    if not snap:
        continue
    cards.append(kpi_card(
        label=pretty_name(c),
        value=f"{snap['price']:,.2f}",
        unit=unit_for(c),
        delta=snap["change_30d"],
        delta_caption="over 30 days",
        accent=style_for(c)["color"],
        ribbon=(snap["low_52w"], snap["high_52w"], snap["price"]),
    ))
render_kpis(cards, per_row=3)

overview = I.market_overview(30)
note(f"<strong>Market summary.</strong> {overview}")

# --------------------------------------------------------------------------
# Price history at a glance
# --------------------------------------------------------------------------
section("Twelve months of prices")
col_a, col_b = st.columns([3, 1], gap="large")
with col_b.container(border=True):
    normalise = st.radio(
        "Scale", ["Actual prices", "Rebased to 100"], index=0,
        help="Rebasing removes the difference in price levels so the three series can be "
             "compared on how much they moved, not what they cost.")
    st.caption("Onion and potato are priced per kilogram; soybean oil per litre, which is "
               "why the actual-price view separates them so widely.")
with col_a:
    series = {c: D.price_series(c).iloc[-365:] for c in D.commodities()}
    st.plotly_chart(
        charts.price_history(series, dark=dark, height=380,
                             normalise=(normalise == "Rebased to 100")),
        **STRETCH)

# --------------------------------------------------------------------------
# Objectives
# --------------------------------------------------------------------------
section("Objectives")
o1, o2 = st.columns(2, gap="large")
with o1.container(border=True):
    st.markdown("""
**1 · Forecast prices accurately.**
Project daily retail prices for onion, potato and soybean oil over horizons of 30 and 60 days,
using three methodologically distinct approaches.

**2 · Convert prices into inflation.**
Translate forecast price paths into daily, weekly, monthly and annualised inflation, plus a
weighted composite index for the essential-goods basket.

**3 · Compare statistical and machine learning methods.**
Evaluate SARIMA, XGBoost and LSTM on identical held-out data under an identical protocol, and
establish which approach suits which commodity, and why.
""")
with o2.container(border=True):
    st.markdown("""
**4 · Quantify uncertainty honestly.**
Report 95% intervals that widen with the horizon, and measure every model against a seasonal
naive baseline so that "accurate" means "better than doing nothing".

**5 · Deliver decisions, not just numbers.**
Generate plain-language guidance for households and for policy, derived from documented
thresholds rather than intuition.

**6 · Make the work reproducible.**
Ship the full pipeline — cleaning, features, training, evaluation, artifacts — so any result
in this dashboard can be traced back to the code that produced it.
""")

# --------------------------------------------------------------------------
# Method and coverage
# --------------------------------------------------------------------------
section("How the forecasts are produced")
m1, m2, m3 = st.columns(3, gap="medium")
with m1.container(border=True):
    st.markdown("""
##### SARIMA
A seasonal ARIMA fitted by the full Box–Jenkins procedure: stationarity testing, differencing,
order selection by AIC, and residual diagnostics. It is the only model here that derives its
confidence intervals analytically.
""")
with m2.container(border=True):
    st.markdown("""
##### XGBoost
Gradient-boosted trees over engineered lag, rolling, calendar and volatility features. It
predicts the daily *change* rather than the price level, which removes the extrapolation
ceiling that otherwise cripples tree models on trending series.
""")
with m3.container(border=True):
    st.markdown("""
##### LSTM
A stacked recurrent network reading the last 30 days of price directly, with dropout and early
stopping. It tests whether a sequence model extracts more from raw history than hand-built
features do.
""")

reg = D.load_registry()
rows = []
for c, meta in reg.get("commodities", {}).items():
    rows.append({
        "Commodity": pretty_name(c),
        "Observations": meta.get("n_observations", "-"),
        "From": meta.get("data_start", "-"),
        "To": meta.get("data_end", "-"),
        "Best model": meta.get("best_model", "-"),
        "Test MAE (BDT)": round(
            meta.get("metrics", {}).get(meta.get("best_model", ""), {}).get("MAE", float("nan")), 3),
    })
if rows:
    section("Data coverage and selected models")
    st.dataframe(rows, **STRETCH, hide_index=True)
    st.caption("The best model is chosen by lowest mean absolute error on the held-out test "
               "period. Full metrics are on the Model Comparison page.")

st.divider()
st.caption("Figures on this dashboard are model output, not official statistics. "
           "Use the Downloads page to export the underlying tables and a summary report.")
