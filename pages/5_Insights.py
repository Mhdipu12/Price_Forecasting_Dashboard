"""Insights — the numbers turned into statements someone can act on."""
import html

import streamlit as st

from app import data as D, insights as I
from app.config import PALETTE, pretty_name, style_for, unit_for
from app.report import build_html_report
from app.theme import kpi_card, note, page_header, render_kpis, section, setup_page
from app.ui import sidebar_controls

setup_page("Insights")
D.require_artifacts()
state = sidebar_controls(show_horizon=True)
horizon = state["horizon"]

page_header(
    "Insights",
    "What the numbers mean",
    "Generated automatically from the current data and forecasts using documented thresholds, "
    "so the same inputs always produce the same reading.",
)

TONE_COLOR = {"good": PALETTE["sage"], "bad": PALETTE["alert"], "neutral": PALETTE["muted"]}
ICON = {"trend": "Trend direction", "extremes": "Highest and lowest",
        "inflation": "Expected inflation", "volatility": "Volatility",
        "consumer": "For consumers", "policy": "For policymakers"}


def insight_block(item) -> str:
    color = TONE_COLOR.get(item.tone, PALETTE["muted"])
    return (
        f'<div class="bd-insight" style="--tone:{color}">'
        f'<div class="bd-insight-kind">{html.escape(ICON.get(item.kind, item.kind))}</div>'
        f'<div class="bd-insight-head">{html.escape(item.headline)}</div>'
        f'<div class="bd-insight-body">{html.escape(item.detail)}</div></div>')


# --------------------------------------------------------------------------
# Market-wide summary
# --------------------------------------------------------------------------
section("Market summary")
st.markdown(
    f'<div class="bd-summary">{html.escape(I.market_overview(horizon))}</div>',
    unsafe_allow_html=True)

st.markdown("")
cards = []
for c in D.commodities():
    snap = D.latest_snapshot(c)
    if not snap:
        continue
    cards.append(kpi_card(
        pretty_name(c), f"{snap['price']:,.2f}", unit_for(c),
        delta=snap["change_30d"], delta_caption="30 days",
        accent=style_for(c)["color"],
        ribbon=(snap["low_52w"], snap["high_52w"], snap["price"])))
render_kpis(cards, per_row=3)

# --------------------------------------------------------------------------
# Per commodity
# --------------------------------------------------------------------------
st.divider()
tabs = st.tabs([f":material/nutrition: {pretty_name(c)}" for c in D.commodities()])
for tab, commodity in zip(tabs, D.commodities()):
    with tab:
        ins = I.build(commodity, horizon)
        if not ins.snapshot:
            st.info("No data for this commodity.")
            continue

        st.markdown(
            f'<div class="bd-note" style="border-left-color:{style_for(commodity)["color"]}">'
            f"<strong>{html.escape(pretty_name(commodity))}.</strong> "
            f"{html.escape(ins.summary)}</div>", unsafe_allow_html=True)


        section("Market reading")
        left, right = st.columns(2, gap="large")
        market_kinds = ["trend", "extremes", "volatility", "inflation"]
        market_items = [i for i in ins.items if i.kind in market_kinds]
        for idx, item in enumerate(market_items):
            (left if idx % 2 == 0 else right).markdown(insight_block(item),
                                                       unsafe_allow_html=True)

        section("Recommendations")
        rec_left, rec_right = st.columns(2, gap="large")
        consumer = ins.of_kind("consumer")
        policy = ins.of_kind("policy")
        if consumer:
            rec_left.markdown(insight_block(consumer[0]), unsafe_allow_html=True)
        if policy:
            rec_right.markdown(insight_block(policy[0]), unsafe_allow_html=True)

# --------------------------------------------------------------------------
# How these are produced
# --------------------------------------------------------------------------
st.divider()
with st.expander("How these insights are generated", icon=":material/rule:"):
    st.markdown(f"""
Nothing here is hand-written for a particular reading. Each statement is produced by comparing
the current figures against fixed, documented thresholds:

| Reading | Rule |
|---|---|
| Broadly stable | 30-day change smaller than ±{I.TREND_FLAT_PCT:.0f}% |
| Rising or falling sharply | 30-day change of at least ±{I.TREND_STRONG_PCT:.0f}% |
| Low volatility | 30-day return standard deviation below {I.VOL_LOW:.0f}% |
| High volatility | 30-day return standard deviation above {I.VOL_HIGH:.0f}% |
| Little change expected | projected inflation within ±{I.INFL_MILD:.0f}% |
| Steep increase or decline | projected inflation of at least ±{I.INFL_HIGH:.0f}% |
| Near 52-week high or low | current price in the top or bottom 20% of the 52-week range |

Consumer guidance combines the projected inflation band with where the price already sits in
its range — advising an early purchase is less useful when the price is already near its peak.
Policy guidance additionally escalates when volatility is high, because a disrupted market
usually calls for supply-side measures and transparent stock reporting rather than price
controls.

Thresholds live in `app/insights.py` and can be changed in one place.
""")

st.download_button(
    "Download this analysis as a report (HTML)",
    build_html_report(horizon).encode("utf-8"),
    file_name=f"market_insights_{horizon}d.html", mime="text/html",
    icon=":material/description:")

note("These readings describe model output and historical prices. They do not account for "
     "policy announcements, import decisions or weather events that have no precedent in the "
     "training data, and they are not financial advice.")
