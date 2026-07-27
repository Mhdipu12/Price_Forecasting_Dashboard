"""Model Comparison — accuracy metrics, diagnostic charts and a written verdict."""
import numpy as np
import pandas as pd
import streamlit as st

from app import charts, data as D
from app.config import model_color, pretty_name
from app.report import df_to_csv_bytes
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import commodity_picker, metric_help, sidebar_controls
from app.compat import STRETCH

setup_page("Model Comparison")
D.require_artifacts()
state = sidebar_controls()
dark = state["dark"]

page_header(
    "Model comparison",
    "Which model to trust, and where",
    "All models were evaluated on the same held-out period under the same one-step-ahead "
    "protocol, against a seasonal naive baseline.",
)

comp = D.load_comparison()
if comp.empty:
    st.info("No comparison metrics found. Run Phase 8 of the notebook.")
    st.stop()

tab_metrics, tab_charts, tab_summary = st.tabs([
    ":material/table_chart: Metrics",
    ":material/insights: Charts",
    ":material/emoji_events: Performance summary",
])

# ==========================================================================
# Metrics
# ==========================================================================
with tab_metrics:
    filters = st.container(border=True)
    f1, f2 = filters.columns([2, 2], gap="large", vertical_alignment="bottom")
    with f1:
        scope = st.multiselect("Commodities", D.commodities(), default=D.commodities(),
                               format_func=pretty_name, key="mc_scope")
    with f2:
        hide_naive = st.toggle("Hide the naive baseline", value=False,
                               help="The baseline is what every model must beat to be useful.")

    view = comp[comp["commodity"].isin(scope)].copy()
    if hide_naive:
        view = view[view["model"] != "Seasonal Naive"]
    view["commodity"] = view["commodity"].map(pretty_name)

    section("Accuracy on the held-out test set")
    st.dataframe(
        view.sort_values(["commodity", "MAE"]).round(4),
        **STRETCH, hide_index=True,
        column_config={
            "MAE": st.column_config.NumberColumn("MAE (BDT)", format="%.3f"),
            "RMSE": st.column_config.NumberColumn("RMSE (BDT)", format="%.3f"),
            "MAPE_%": st.column_config.NumberColumn("MAPE %", format="%.2f"),
            "sMAPE_%": st.column_config.NumberColumn("sMAPE %", format="%.2f"),
            "R2": st.column_config.NumberColumn("R²", format="%.3f"),
            "skill_vs_naive_%": st.column_config.ProgressColumn(
                "Skill vs naive %", format="%.1f%%",
                min_value=float(min(0, view["skill_vs_naive_%"].min())),
                max_value=float(max(1, view["skill_vs_naive_%"].max()))),
        })
    metric_help()

    section("Winner by commodity")
    cards = []
    for c in scope:
        sub = comp[(comp["commodity"] == c) & (comp["model"] != "Seasonal Naive")]
        if sub.empty:
            continue
        w = sub.sort_values("MAE").iloc[0]
        runner = sub.sort_values("MAE").iloc[1] if len(sub) > 1 else None
        margin = ((runner["MAE"] - w["MAE"]) / runner["MAE"] * 100) if runner is not None else 0.0
        cards.append(kpi_card(
            pretty_name(c), w["model"], "",
            delta=margin, delta_suffix="%",
            delta_caption=f"lower MAE than {runner['model']}" if runner is not None else "",
            accent=model_color(w["model"])))
    render_kpis(cards, per_row=3)

    st.download_button("Download metrics (CSV)", df_to_csv_bytes(view.round(5)),
                       file_name="model_comparison.csv", mime="text/csv",
                       icon=":material/download:")

# ==========================================================================
# Charts
# ==========================================================================
with tab_charts:
    metric = st.radio("Metric", ["MAE", "RMSE", "MAPE_%", "R2", "skill_vs_naive_%"],
                      horizontal=True, key="mc_metric",
                      format_func=lambda m: {"MAPE_%": "MAPE %", "R2": "R²",
                                             "skill_vs_naive_%": "Skill vs naive %"}.get(m, m))
    st.plotly_chart(charts.metric_bars(comp, metric, dark=dark), **STRETCH)

    st.divider()
    commodity = commodity_picker("Commodity for diagnostics", key="mc_commodity")

    c1, c2 = st.columns([1, 1.3], gap="large")
    with c1:
        section("Skill profile")
        st.plotly_chart(charts.radar_chart(comp, commodity, dark=dark),
                        **STRETCH)
        st.caption("Each axis is normalised across the models shown, with better always "
                   "further out. A larger enclosed area means a model that is good on every "
                   "measure rather than only one.")
    with c2:
        preds = D.load_test_predictions()
        if not preds.empty:
            sub = preds[(preds["commodity"] == commodity)
                        & (preds["model"] != "Seasonal Naive")]
            if not sub.empty:
                section("Actual versus predicted")
                st.plotly_chart(charts.actual_vs_predicted(sub, dark=dark),
                                **STRETCH)

    preds = D.load_test_predictions()
    if not preds.empty:
        sub = preds[(preds["commodity"] == commodity) & (preds["model"] != "Seasonal Naive")]
        if not sub.empty:
            d1, d2 = st.columns(2, gap="large")
            with d1:
                section("Error distribution")
                st.plotly_chart(charts.error_distribution(sub, dark=dark),
                                **STRETCH)
                st.caption("A box centred on zero means an unbiased model. A box sitting above "
                           "zero means the model systematically under-forecasts.")
            with d2:
                section("Calibration")
                st.plotly_chart(charts.calibration_scatter(sub, dark=dark),
                                **STRETCH)
                st.caption("Points on the dashed line are perfect predictions. Systematic "
                           "curvature away from it reveals where a model breaks down.")

# ==========================================================================
# Summary
# ==========================================================================
with tab_summary:
    section("Performance summary")
    reg = D.load_registry()

    for c in D.commodities():
        sub = comp[comp["commodity"] == c]
        if sub.empty:
            continue
        ranked = sub[sub["model"] != "Seasonal Naive"].sort_values("MAE")
        if ranked.empty:
            continue
        w = ranked.iloc[0]
        naive = sub[sub["model"] == "Seasonal Naive"]
        naive_mae = float(naive["MAE"].iloc[0]) if not naive.empty else np.nan

        st.markdown(f"##### {pretty_name(c)}")
        order = " → ".join(f"{r['model']} ({r['MAE']:.3f})" for _, r in ranked.iterrows())
        lines = [
            f"**Ranking by MAE:** {order}.",
            f"**Selected model:** {w['model']}, with MAE {w['MAE']:.3f} BDT, "
            f"RMSE {w['RMSE']:.3f}, MAPE {w['MAPE_%']:.2f}% and R² {w['R2']:.3f}.",
        ]
        if not np.isnan(naive_mae):
            lines.append(
                f"**Against the baseline:** the seasonal naive rule scores {naive_mae:.3f} BDT, "
                f"so {w['model']} reduces error by {w['skill_vs_naive_%']:.1f}%."
                if w["skill_vs_naive_%"] > 0 else
                f"**Against the baseline:** {w['model']} does *not* beat the seasonal naive "
                f"rule ({naive_mae:.3f} BDT). Treat forecasts for this commodity with caution.")

        if w["R2"] < 0:
            lines.append("**Caution:** a negative R² means the model explains less variance "
                         "than simply predicting the average. The MAE may still be low if the "
                         "series is stable, but the model is adding little.")
        spread = ranked["MAE"].max() - ranked["MAE"].min()
        rel = spread / ranked["MAE"].min() * 100 if ranked["MAE"].min() else 0
        if rel < 5:
            lines.append(f"**Note:** all three models fall within {rel:.1f}% of each other. "
                         "The choice between them is not statistically meaningful here, so "
                         "prefer the simpler model — SARIMA — for its interpretable intervals.")
        for line in lines:
            st.markdown("- " + line)
        st.markdown("")

    note("These metrics come from one-step-ahead prediction, where every model sees the true "
         "recent history. Multi-step forecasts on the Forecast page are materially less "
         "accurate because each day is built on the previous day's prediction. Quote the "
         "one-step figures as model quality, and the widening intervals as forecast quality.")

    section("Model specifications")
    rows = []
    for c, meta in reg.get("commodities", {}).items():
        rows.append({
            "Commodity": pretty_name(c),
            "SARIMA order": f"{tuple(meta.get('sarima', {}).get('order', []))}"
                            f"×{tuple(meta.get('sarima', {}).get('seasonal_order', []))}",
            "SARIMA AIC": round(meta.get("sarima", {}).get("aic", float("nan")), 1),
            "LSTM lookback": meta.get("lstm", {}).get("lookback", "-"),
            "LSTM best epoch": meta.get("lstm", {}).get("best_epoch", "-"),
            "Observations": meta.get("n_observations", "-"),
        })
    if rows:
        st.dataframe(rows, **STRETCH, hide_index=True)
