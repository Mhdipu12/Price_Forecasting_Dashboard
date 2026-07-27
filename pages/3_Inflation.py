"""Inflation — realised inflation at three frequencies, and the forward projection."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import charts, data as D
from app.config import PALETTE, pretty_name, style_for
from app.report import df_to_csv_bytes
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import commodity_picker, sidebar_controls
from app.compat import STRETCH

setup_page("Inflation")
D.require_artifacts()
state = sidebar_controls(show_horizon=True)
dark = state["dark"]
horizon = state["horizon"]

page_header(
    "Inflation",
    "How fast prices are changing",
    "Realised inflation measured over one day, one week and one month, alongside the "
    "projection implied by the forecasts.",
)

tab_hist, tab_future, tab_basket = st.tabs([
    ":material/history: Realised inflation",
    ":material/timeline: Future inflation",
    ":material/shopping_basket: Essential-goods basket",
])

# ==========================================================================
# Realised
# ==========================================================================
with tab_hist:
    filters = st.container(border=True)
    c1, c2 = filters.columns([2, 3], gap="large")
    with c1:
        commodity = commodity_picker("Commodity", key="infl_commodity")
    with c2:
        window = st.select_slider("Window shown", options=[90, 180, 365, 730, 1825],
                                  value=365, format_func=lambda v: f"last {v} days")

    infl = D.inflation_series(commodity).iloc[-window:]
    accent = style_for(commodity)["color"]

    latest = {k: infl[k].dropna().iloc[-1] if infl[k].notna().any() else float("nan")
              for k in ["daily_%", "weekly_%", "monthly_%", "annual_%"]}
    render_kpis([
        kpi_card("Daily", f"{latest['daily_%']:+,.2f}", "%", accent=accent,
                 delta_caption="vs yesterday"),
        kpi_card("Weekly", f"{latest['weekly_%']:+,.2f}", "%", accent=accent,
                 delta_caption="vs 7 days ago"),
        kpi_card("Monthly", f"{latest['monthly_%']:+,.2f}", "%", accent=accent,
                 delta_caption="vs 30 days ago"),
        kpi_card("Annual", f"{latest['annual_%']:+,.2f}", "%", accent=accent,
                 delta_caption="vs 12 months ago"),
    ], per_row=4)

    for label, col in [("Daily", "daily_%"), ("Weekly", "weekly_%"), ("Monthly", "monthly_%")]:
        section(f"{label} inflation")
        st.plotly_chart(
            charts.inflation_chart(infl, col, commodity, dark=dark, height=250),
            **STRETCH)

    note("Daily inflation is noisy by nature — a single market day can swing it several "
         "percent. Weekly inflation smooths that out and is the most useful frequency for "
         "spotting a turn. Monthly inflation is the one to quote: it is stable enough to be "
         "meaningful and short enough to be timely.")

    section("Volatility")
    vol = infl["volatility_30"].dropna()
    if len(vol):
        fig = go.Figure(go.Scatter(x=vol.index, y=vol, mode="lines", fill="tozeroy",
                                   line=dict(color=accent, width=1.8),
                                   fillcolor="rgba(142,59,107,0.14)"))
        fig.add_hline(y=1.0, line_dash="dot", line_color=PALETTE["sage"],
                      annotation_text="calm")
        fig.add_hline(y=3.0, line_dash="dot", line_color=PALETTE["alert"],
                      annotation_text="disrupted")
        st.plotly_chart(charts.base_layout(fig, dark, 260, ylab="30-day volatility (%)",
                                           legend=False), **STRETCH)
        st.caption("Rolling standard deviation of daily returns. Sustained readings above 3% "
                   "usually mean supply disruption or speculative holding rather than normal "
                   "seasonal movement.")

    st.download_button("Download inflation series (CSV)",
                       df_to_csv_bytes(infl.reset_index()),
                       file_name=f"{commodity}_inflation.csv", mime="text/csv",
                       icon=":material/download:")

# ==========================================================================
# Future
# ==========================================================================
with tab_future:
    fut = D.load_inflation()
    if fut.empty:
        st.info("No inflation projections found. Run Phase 9 of the notebook.")
    else:
        available_h = sorted(fut["horizon_days"].unique())
        h = st.radio("Horizon", available_h, index=len(available_h) - 1,
                     horizontal=True, format_func=lambda v: f"{v} days", key="infl_h")

        best_only = st.toggle("Best model only", value=True,
                              help="Turn off to compare what each model implies.")
        sub = fut[fut["horizon_days"] == h]
        if best_only and "is_best_model" in sub:
            sub = sub[sub["is_best_model"]]

        section(f"Projected inflation over {h} days")
        plot_df = (sub.drop_duplicates(subset=["commodity"])
                   if best_only else sub.sort_values(["commodity", "model"]))
        st.plotly_chart(
            charts.inflation_bars(plot_df, dark=dark, height=380,
                                  lower_col="inflation_lower_%",
                                  upper_col="inflation_upper_%"),
            **STRETCH)
        st.caption("Whiskers show the 95% interval. Where a whisker crosses zero, the model "
                   "cannot tell you the direction with confidence.")

        cards = []
        for _, r in plot_df.iterrows():
            v = float(r["inflation_%"])
            cards.append(kpi_card(
                pretty_name(r["commodity"]),
                f"{v:+,.2f}", "%",
                delta=float(r["annualised_inflation_%"]),
                delta_suffix="%", delta_caption="annualised",
                accent=style_for(r["commodity"])["color"]))
        render_kpis(cards, per_row=3)

        section("Detail")
        show = sub[["commodity", "model", "horizon_days", "last_actual_price",
                    "forecast_price_end", "inflation_%", "inflation_lower_%",
                    "inflation_upper_%", "annualised_inflation_%"]].copy()
        show["commodity"] = show["commodity"].map(pretty_name)
        show.columns = ["Commodity", "Model", "Days", "Price now", "Price forecast",
                        "Inflation %", "Low 95%", "High 95%", "Annualised %"]
        st.dataframe(show.round(3), **STRETCH, hide_index=True)
        st.download_button("Download projections (CSV)", df_to_csv_bytes(show.round(4)),
                           file_name=f"future_inflation_{h}d.csv", mime="text/csv",
                           icon=":material/download:")

        note("Annualised inflation extrapolates the projected change to a full year. It is a "
             "comparison device, not a prediction — a 30-day move rarely repeats twelve times.")

# ==========================================================================
# Basket
# ==========================================================================
with tab_basket:
    comp = D.load_composite()
    if comp.empty:
        st.info("No composite index found. Run Phase 9.5 of the notebook.")
    else:
        section("Composite essential-goods index")
        st.markdown(
            "A weighted index across all tracked commodities, rebased so that today equals "
            "100. It answers a different question from any single commodity: what happens to "
            "the cost of the basket as a whole.")

        cards = []
        for _, r in comp.iterrows():
            v = float(r["composite_inflation_%"])
            cards.append(kpi_card(
                f"{int(r['horizon_days'])}-day outlook",
                f"{v:+,.2f}", "%",
                delta_caption=f"index {r['index_now']:.0f} → {r['index_forecast']:.1f}",
                accent=PALETTE["alert"] if v > 0 else PALETTE["sage"]))
        render_kpis(cards, per_row=len(cards) or 1)

        contrib_cols = [c for c in comp.columns if c.endswith("_contrib_%")]
        if contrib_cols:
            section("Which commodity drives the basket")
            h_sel = st.radio("Horizon", sorted(comp["horizon_days"].unique()),
                             horizontal=True, format_func=lambda v: f"{v} days",
                             key="basket_h")
            row = comp[comp["horizon_days"] == h_sel].iloc[0]
            names = [c.replace("_contrib_%", "") for c in contrib_cols]
            vals = [float(row[c]) for c in contrib_cols]
            fig = go.Figure(go.Bar(
                x=[pretty_name(n) for n in names], y=vals,
                marker_color=[style_for(n)["color"] for n in names],
                text=[f"{v:+.2f} pp" for v in vals], textposition="outside",
                hovertemplate="%{x}: %{y:+.2f} percentage points<extra></extra>"))
            fig.add_hline(y=0, line_width=1.2, line_color=PALETTE["muted"])
            st.plotly_chart(
                charts.base_layout(fig, dark, 340,
                                   ylab="Contribution (percentage points)", legend=False),
                **STRETCH)
            st.caption("Contributions are weighted, so they sum to the composite figure above. "
                       "A commodity with a large price move but a small basket weight "
                       "contributes less than its headline number suggests.")

        st.dataframe(comp.round(3), **STRETCH, hide_index=True)
        st.download_button("Download composite index (CSV)", df_to_csv_bytes(comp),
                           file_name="composite_inflation.csv", mime="text/csv",
                           icon=":material/download:")

        note("Weights are currently equal across commodities. Replacing them with household "
             "consumption shares from a HIES survey would make this figure directly comparable "
             "with official BBS inflation.")
