"""Automatic insight generation.

Turns the numbers into plain statements a reader can act on. Every threshold is
named and defined here rather than buried in a page, so the rules can be
defended in a viva and adjusted in one place.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import data as D
from .config import pretty_name, unit_for

# ---- classification thresholds (documented, not magic) -------------------
TREND_FLAT_PCT = 2.0        # |30-day change| below this is "broadly stable"
TREND_STRONG_PCT = 8.0      # above this is "sharply"
VOL_LOW = 1.0               # 30-day daily-return std, %
VOL_HIGH = 3.0
INFL_MILD = 2.0             # |projected inflation| below this is "little change"
INFL_HIGH = 8.0


@dataclass
class Insight:
    kind: str          # trend | extremes | inflation | volatility | consumer | policy
    headline: str
    detail: str
    tone: str = "neutral"   # good | bad | neutral


@dataclass
class CommodityInsights:
    commodity: str
    snapshot: dict
    items: list[Insight] = field(default_factory=list)
    summary: str = ""

    def of_kind(self, kind: str) -> list[Insight]:
        return [i for i in self.items if i.kind == kind]


# --------------------------------------------------------------------------
# Classifiers
# --------------------------------------------------------------------------
def classify_trend(change_30d: float) -> tuple[str, str]:
    if np.isnan(change_30d):
        return "unclear", "neutral"
    if abs(change_30d) < TREND_FLAT_PCT:
        return "broadly stable", "neutral"
    direction = "rising" if change_30d > 0 else "falling"
    strength = "sharply " if abs(change_30d) >= TREND_STRONG_PCT else ""
    tone = ("bad" if change_30d > 0 else "good")
    return f"{strength}{direction}", tone


def classify_volatility(vol: float) -> tuple[str, str]:
    if np.isnan(vol):
        return "unknown", "neutral"
    if vol < VOL_LOW:
        return "low", "good"
    if vol < VOL_HIGH:
        return "moderate", "neutral"
    return "high", "bad"


def classify_inflation(pct: float) -> tuple[str, str]:
    if np.isnan(pct):
        return "unclear", "neutral"
    if abs(pct) < INFL_MILD:
        return "little change", "neutral"
    if pct >= INFL_HIGH:
        return "steep increase", "bad"
    if pct > 0:
        return "moderate increase", "bad"
    if pct <= -INFL_HIGH:
        return "steep decline", "good"
    return "moderate decline", "good"


def position_in_range(cur: float, low: float, high: float) -> tuple[float, str]:
    span = max(high - low, 1e-9)
    pct = (cur - low) / span * 100
    if pct >= 80:
        return pct, "near its 52-week high"
    if pct <= 20:
        return pct, "near its 52-week low"
    if pct >= 60:
        return pct, "in the upper part of its 52-week range"
    if pct <= 40:
        return pct, "in the lower part of its 52-week range"
    return pct, "around the middle of its 52-week range"


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------
def build(commodity: str, horizon: int = 30) -> CommodityInsights:
    snap = D.latest_snapshot(commodity)
    name = pretty_name(commodity)
    unit = unit_for(commodity)
    items: list[Insight] = []

    if not snap:
        return CommodityInsights(commodity, {}, [], "No price data available.")

    cur = snap["price"]
    trend_word, trend_tone = classify_trend(snap["change_30d"])
    vol_word, vol_tone = classify_volatility(snap["volatility_30d"])
    pos_pct, pos_word = position_in_range(cur, snap["low_52w"], snap["high_52w"])

    # ---- trend -----------------------------------------------------------
    items.append(Insight(
        "trend",
        f"Prices are {trend_word}",
        f"{name} last traded at {cur:,.2f} {unit} on "
        f"{snap['date'].date().isoformat()}. Over the past 30 days the price moved "
        f"{snap['change_30d']:+.2f}%, over 7 days {snap['change_7d']:+.2f}%, and over "
        f"12 months {snap['change_365d']:+.2f}%.",
        trend_tone))

    # ---- extremes --------------------------------------------------------
    items.append(Insight(
        "extremes",
        f"Trading {pos_word}",
        f"The 52-week range runs from {snap['low_52w']:,.2f} to {snap['high_52w']:,.2f} {unit}, "
        f"with a mean of {snap['mean_52w']:,.2f}. Today's price sits at the "
        f"{pos_pct:.0f}th percentile of that range.",
        "bad" if pos_pct >= 80 else ("good" if pos_pct <= 20 else "neutral")))

    # ---- volatility ------------------------------------------------------
    items.append(Insight(
        "volatility",
        f"Volatility is {vol_word}",
        f"Daily price movements over the last 30 days have a standard deviation of "
        f"{snap['volatility_30d']:.2f}%. Readings below {VOL_LOW:.0f}% indicate a calm market; "
        f"above {VOL_HIGH:.0f}% indicates a disrupted one where forecasts should be "
        f"treated with more caution.",
        vol_tone))

    # ---- forecast inflation ---------------------------------------------
    infl = D.load_inflation()
    proj = np.nan
    model_used = D.best_model(commodity)
    if not infl.empty:
        row = infl[(infl["commodity"] == commodity) & (infl["horizon_days"] == horizon)
                   & (infl["is_best_model"] if "is_best_model" in infl else True)]
        if row.empty:
            row = infl[(infl["commodity"] == commodity) & (infl["horizon_days"] == horizon)]
        if not row.empty:
            r = row.iloc[0]
            proj = float(r["inflation_%"])
            model_used = r["model"]
            infl_word, infl_tone = classify_inflation(proj)
            lo = float(r.get("inflation_lower_%", np.nan))
            hi = float(r.get("inflation_upper_%", np.nan))
            band = (f" The 95% interval spans {lo:+.2f}% to {hi:+.2f}%."
                    if not (np.isnan(lo) or np.isnan(hi)) else "")
            items.append(Insight(
                "inflation",
                f"{horizon}-day outlook: {infl_word}",
                f"The {model_used} model projects {name} at "
                f"{float(r['forecast_price_end']):,.2f} {unit} in {horizon} days, a change of "
                f"{proj:+.2f}% from today.{band} On an annualised basis that is "
                f"{float(r.get('annualised_inflation_%', np.nan)):+.1f}%.",
                infl_tone))

    # ---- consumer recommendation ----------------------------------------
    items.append(Insight("consumer", *_consumer_advice(name, proj, pos_pct, vol_word, horizon)))

    # ---- policy recommendation ------------------------------------------
    items.append(Insight("policy", *_policy_advice(name, proj, pos_pct, vol_word, horizon)))

    summary = _market_summary(name, unit, cur, trend_word, pos_word, vol_word, proj, horizon)
    return CommodityInsights(commodity, snap, items, summary)


def _consumer_advice(name, proj, pos_pct, vol_word, horizon) -> tuple[str, str, str]:
    if np.isnan(proj):
        return ("Buy as normal",
                f"No forecast is available for {name}, so there is no reason to change "
                "normal purchasing behaviour.", "neutral")
    if proj >= INFL_HIGH:
        return ("Consider buying earlier",
                f"{name} is projected to cost {proj:+.1f}% more within {horizon} days. "
                f"Households that can store the product may benefit from purchasing sooner. "
                f"{'Prices are already near their 52-week high, so the saving is smaller than it looks. ' if pos_pct >= 80 else ''}"
                f"Bulk buying is only worthwhile where storage is practical and waste is low.",
                "bad")
    if proj <= -INFL_HIGH:
        return ("Consider waiting",
                f"{name} is projected to fall {abs(proj):.1f}% within {horizon} days. "
                "Delaying non-urgent purchases is likely to be cheaper. Buy only what is "
                "needed in the short term.", "good")
    if proj > INFL_MILD:
        return ("Buy as normal, monitor weekly",
                f"A modest rise of {proj:+.1f}% is expected over {horizon} days — not enough "
                "to justify stockpiling, but worth reviewing again next week.", "neutral")
    if proj < -INFL_MILD:
        return ("Buy as normal, small savings ahead",
                f"A modest decline of {proj:.1f}% is expected over {horizon} days. "
                "Flexible purchases can be deferred, but the saving is small.", "good")
    return ("Buy as normal",
            f"Prices are expected to stay within {INFL_MILD:.0f}% of today's level over the "
            f"next {horizon} days. There is no timing advantage either way.", "neutral")


def _policy_advice(name, proj, pos_pct, vol_word, horizon) -> tuple[str, str, str]:
    parts = []
    tone = "neutral"
    if not np.isnan(proj) and proj >= INFL_HIGH:
        tone = "bad"
        parts.append(
            f"A projected {proj:+.1f}% rise in {name} over {horizon} days warrants early "
            "action: verify buffer stock levels, review import and duty settings, and "
            "prepare open-market sales in the districts with the thinnest supply.")
    elif not np.isnan(proj) and proj <= -INFL_HIGH:
        tone = "good"
        parts.append(
            f"A projected {abs(proj):.1f}% fall in {name} over {horizon} days relieves "
            "consumer pressure but squeezes farmgate margins. Procurement and storage "
            "support can stabilise producer income before the next planting decision.")
    else:
        parts.append(
            f"No unusual price pressure is projected for {name} over the next {horizon} days. "
            "Routine monitoring is sufficient.")

    if pos_pct >= 80:
        parts.append("Prices are already near their 52-week high, so any further increase "
                     "compounds an existing burden on low-income households.")
    if vol_word == "high":
        tone = "bad"
        parts.append("Volatility is elevated, which usually signals supply disruption or "
                     "speculative holding. Market inspection and transparent stock reporting "
                     "are more effective than price ceilings in this state.")
    return ("Policy watch" if tone != "neutral" else "Routine monitoring",
            " ".join(parts), tone)


def _market_summary(name, unit, cur, trend_word, pos_word, vol_word, proj, horizon) -> str:
    proj_txt = (f" Looking ahead {horizon} days, the model projects a change of {proj:+.2f}%."
                if not np.isnan(proj) else "")
    return (f"{name} is trading at {cur:,.2f} {unit}, {pos_word}, with prices {trend_word} "
            f"over the past month and {vol_word} volatility.{proj_txt}")


def build_all(horizon: int = 30) -> dict[str, CommodityInsights]:
    return {c: build(c, horizon) for c in D.commodities()}


def market_overview(horizon: int = 30) -> str:
    """One paragraph covering all commodities together."""
    all_ins = build_all(horizon)
    if not all_ins:
        return "No data available."
    infl = D.load_inflation()
    rising, falling = [], []
    for c, ins in all_ins.items():
        row = infl[(infl["commodity"] == c) & (infl["horizon_days"] == horizon)] \
            if not infl.empty else pd.DataFrame()
        if row.empty:
            continue
        best = row[row["is_best_model"]] if "is_best_model" in row else row
        v = float((best if not best.empty else row).iloc[0]["inflation_%"])
        (rising if v > INFL_MILD else falling if v < -INFL_MILD else []).append(
            (pretty_name(c), v))

    bits = []
    if rising:
        bits.append("expected to rise: " + ", ".join(f"{n} ({v:+.1f}%)" for n, v in rising))
    if falling:
        bits.append("expected to ease: " + ", ".join(f"{n} ({v:+.1f}%)" for n, v in falling))
    if not bits:
        return (f"Across all tracked commodities, prices are projected to stay within "
                f"{INFL_MILD:.0f}% of current levels over the next {horizon} days. "
                "No commodity requires intervention on current evidence.")
    comp = D.load_composite()
    comp_txt = ""
    if not comp.empty:
        row = comp[comp["horizon_days"] == horizon]
        if not row.empty:
            comp_txt = (f" The weighted essential-goods index implies "
                        f"{float(row.iloc[0]['composite_inflation_%']):+.2f}% overall inflation "
                        f"over the same window.")
    return (f"Over the next {horizon} days, " + "; ".join(bits) + "." + comp_txt)
