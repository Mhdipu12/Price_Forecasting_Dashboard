"""Plotly chart builders.

All figures share one layout function so the dashboard reads as a single
publication rather than a pile of default charts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import PALETTE, model_color, pretty_name, style_for, surface, unit_for

FONT = "Inter, system-ui, -apple-system, Segoe UI, sans-serif"
MONO = "JetBrains Mono, ui-monospace, SFMono-Regular, monospace"


def _template(dark: bool) -> str:
    return "plotly_dark" if dark else "plotly_white"


def base_layout(fig: go.Figure, dark: bool = False, height: int = 420,
                title: str = "", ylab: str = "", xlab: str = "",
                legend: bool = True) -> go.Figure:
    """The single layout every figure passes through.

    Keeping one function means the whole dashboard reads as one publication:
    the same grid weight, the same tick typography, the same hover card.
    """
    s = surface(dark)
    grid, axis, text, muted = s["grid"], s["axis"], s["text"], s["muted"]
    fig.update_layout(
        template=_template(dark),
        height=height,
        title=dict(text=title, x=0, xanchor="left", y=0.97, yanchor="top",
                   font=dict(family=FONT, size=14.5, color=text)),
        font=dict(family=FONT, size=12, color=text),
        margin=dict(l=6, r=10, t=52 if title else (34 if legend else 14), b=6),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[PALETTE["slate"], PALETTE["sage"], PALETTE["onion"],
                  PALETTE["oil"], PALETTE["potato"]],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=11.5, color=muted), itemsizing="constant",
                    itemwidth=30, bgcolor="rgba(0,0,0,0)",
                    traceorder="normal") if legend else dict(visible=False),
        showlegend=legend,
        hoverlabel=dict(
            bgcolor=s["hover_bg"], bordercolor=s["border_bold"],
            font=dict(family=MONO, size=11.5, color=text), align="left",
        ),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=muted, activecolor=s["accent"]),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=axis,
        ticks="outside", ticklen=4, tickcolor=axis, tickfont=dict(family=MONO, size=10.5,
                                                                 color=muted),
        title_text=xlab, title_font=dict(family=FONT, size=11.5, color=muted),
        title_standoff=10, showspikes=False,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=grid, gridwidth=1, zeroline=False, showline=False,
        ticks="", tickfont=dict(family=MONO, size=10.5, color=muted),
        title_text=ylab, title_font=dict(family=FONT, size=11.5, color=muted),
        title_standoff=12, automargin=True,
    )
    return fig


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# --------------------------------------------------------------------------
# Historical
# --------------------------------------------------------------------------
def price_history(series_map: dict[str, pd.Series], dark=False, height=430,
                  normalise=False) -> go.Figure:
    fig = go.Figure()
    for name, s in series_map.items():
        vals = (s / s.iloc[0] * 100) if (normalise and len(s) and s.iloc[0]) else s
        fig.add_trace(go.Scatter(
            x=s.index, y=vals, name=pretty_name(name), mode="lines",
            line=dict(color=style_for(name)["color"], width=1.9, shape="linear"),
            hovertemplate="%{y:,.2f}<extra>" + pretty_name(name) + "</extra>",
        ))
    ylab = "Index (start = 100)" if normalise else "Price (BDT)"
    fig = base_layout(fig, dark, height, ylab=ylab)
    tone = surface(dark)
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.07,
                                      bgcolor=tone["surface_alt"],
                                      bordercolor=tone["border"], borderwidth=1))
    return fig


def trend_chart(s: pd.Series, commodity: str, windows=(30, 90, 365),
                dark=False, height=430) -> go.Figure:
    accent = style_for(commodity)["color"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s.index, y=s, name="Daily price", mode="lines",
                             line=dict(color=_rgba(accent, 0.30), width=1.1),
                             hovertemplate="%{y:,.2f}<extra>Daily price</extra>"))
    shades = [PALETTE["sage"], PALETTE["slate"], PALETTE["alert"]]
    for w, col in zip(windows, shades):
        if len(s) > w:
            fig.add_trace(go.Scatter(x=s.index, y=s.rolling(w).mean(),
                                     name=f"{w}-day average", mode="lines",
                                     line=dict(color=col, width=2.1),
                                     hovertemplate="%{y:,.2f}<extra>"
                                                   f"{w}-day average</extra>"))
    return base_layout(fig, dark, height, ylab=f"Price ({unit_for(commodity)})")


def inflation_chart(df: pd.DataFrame, column: str, commodity: str,
                    dark=False, height=360, title="") -> go.Figure:
    d = df[column].dropna()
    up = d.clip(lower=0)
    down = d.clip(upper=0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d.index, y=up, name="Rising", mode="lines",
                             line=dict(width=0.8, color=_rgba(PALETTE["alert"], 0.9)),
                             fill="tozeroy", fillcolor=_rgba(PALETTE["alert"], 0.42),
                             hovertemplate="%{y:+,.2f}%<extra>Rising</extra>"))
    fig.add_trace(go.Scatter(x=d.index, y=down, name="Falling", mode="lines",
                             line=dict(width=0.8, color=_rgba(PALETTE["sage"], 0.9)),
                             fill="tozeroy", fillcolor=_rgba(PALETTE["sage"], 0.42),
                             hovertemplate="%{y:+,.2f}%<extra>Falling</extra>"))
    fig.add_hline(y=0, line_width=1, line_color=surface(dark)["axis"])
    return base_layout(fig, dark, height, title=title, ylab="% change")


def distribution_chart(s: pd.Series, commodity: str, dark=False, height=340) -> go.Figure:
    accent = style_for(commodity)["color"]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=s, nbinsx=48, name="Price",
                               marker=dict(color=_rgba(accent, 0.55),
                                           line=dict(color=accent, width=0.8)),
                               hovertemplate="%{x:,.2f} · %{y} days<extra></extra>"))
    fig.add_vline(x=float(s.mean()), line_dash="dash", line_width=1.4,
                  line_color=PALETTE["alert"],
                  annotation_text="mean", annotation_position="top",
                  annotation_font=dict(family=FONT, size=10.5, color=PALETTE["alert"]))
    fig.add_vline(x=float(s.median()), line_dash="dot", line_width=1.4,
                  line_color=PALETTE["sage"],
                  annotation_text="median", annotation_position="bottom",
                  annotation_font=dict(family=FONT, size=10.5, color=PALETTE["sage"]))
    fig = base_layout(fig, dark, height, ylab="Days", xlab=f"Price ({unit_for(commodity)})",
                      legend=False)
    fig.update_layout(bargap=0.04, hovermode="closest")
    return fig


def monthly_heatmap(s: pd.Series, dark=False, height=360) -> go.Figure:
    d = pd.DataFrame({"price": s})
    d["year"] = d.index.year
    d["month"] = d.index.month
    piv = d.pivot_table(index="year", columns="month", values="price", aggfunc="mean")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    tone = surface(dark)
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[months[m - 1] for m in piv.columns], y=piv.index.astype(str),
        colorscale=[[0.0, PALETTE["sage"]], [0.5, tone["surface_alt"]],
                    [1.0, PALETTE["alert"]]],
        xgap=2, ygap=2,
        hovertemplate="%{y} %{x}: %{z:,.1f}<extra></extra>",
        colorbar=dict(title=dict(text="BDT", font=dict(family=FONT, size=11,
                                                      color=tone["muted"])),
                      thickness=10, outlinewidth=0, len=0.86,
                      tickfont=dict(family=MONO, size=10, color=tone["muted"])),
    ))
    fig = base_layout(fig, dark, height, legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(showline=False, ticks="")
    return fig


def seasonality_chart(s: pd.Series, commodity: str, dark=False, height=340) -> go.Figure:
    """De-trended monthly seasonal index — 1.0 means 'on trend'."""
    trend = s.rolling(365, center=True, min_periods=60).mean()
    detr = (s / trend).dropna()
    idx = detr.groupby(detr.index.month).mean().reindex(range(1, 13))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    colors = [PALETTE["alert"] if v and v > 1 else PALETTE["sage"] for v in idx.values]
    fig = go.Figure(go.Bar(x=months, y=idx.values - 1,
                           marker=dict(color=[_rgba(c, 0.85) for c in colors],
                                       line=dict(width=0)),
                           hovertemplate="%{x}: %{y:+.1%} vs trend<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=surface(dark)["axis"])
    fig = base_layout(fig, dark, height, ylab="Deviation from trend", legend=False)
    fig.update_layout(bargap=0.42)
    fig.update_yaxes(tickformat=".0%")
    return fig


# --------------------------------------------------------------------------
# Forecast
# --------------------------------------------------------------------------
def forecast_chart(history: pd.Series, forecasts: dict[str, pd.DataFrame],
                   commodity: str, show_ci=True, highlight: str | None = None,
                   lookback=180, dark=False, height=470) -> go.Figure:
    hist = history.iloc[-lookback:]
    tone = surface(dark)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist.values, name="Observed", mode="lines",
        line=dict(color=tone["text"], width=2.0),
        hovertemplate="%{y:,.2f}<extra>Observed</extra>"))

    for model, df in forecasts.items():
        if df.empty:
            continue
        col = model_color(model)
        is_hl = (highlight is None) or (model == highlight)
        if show_ci and is_hl and {"lower", "upper"}.issubset(df.columns):
            fig.add_trace(go.Scatter(
                x=list(df["date"]) + list(df["date"][::-1]),
                y=list(df["upper"]) + list(df["lower"][::-1]),
                fill="toself", fillcolor=_rgba(col, 0.13), line=dict(width=0),
                name=f"{model} 95% interval", hoverinfo="skip"))
        # join the forecast to the last observed point so the line is continuous
        x = [hist.index[-1]] + list(df["date"])
        y = [float(hist.iloc[-1])] + list(df["forecast"])
        fig.add_trace(go.Scatter(
            x=x, y=y, name=model, mode="lines",
            line=dict(color=col, width=2.5 if is_hl else 1.4,
                      dash="solid" if is_hl else "dot"),
            hovertemplate="%{y:,.2f}<extra>" + model + "</extra>"))

    fig.add_vline(x=hist.index[-1], line_width=1, line_dash="dash",
                  line_color=tone["axis"])
    return base_layout(fig, dark, height, ylab=f"Price ({unit_for(commodity)})")


def horizon_uncertainty(df: pd.DataFrame, commodity: str, dark=False,
                        height=280) -> go.Figure:
    """How wide the 95% interval becomes as the horizon lengthens."""
    if df.empty or not {"lower", "upper"}.issubset(df.columns):
        return base_layout(go.Figure(), dark, height, legend=False)
    width = (df["upper"] - df["lower"]).values
    accent = style_for(commodity)["color"]
    fig = go.Figure(go.Scatter(
        x=df["horizon_day"], y=width, mode="lines", fill="tozeroy",
        line=dict(color=accent, width=2.1, shape="spline", smoothing=0.6),
        fillcolor=_rgba(accent, 0.14),
        hovertemplate="Day %{x}: ±%{y:,.2f} BDT wide<extra></extra>"))
    return base_layout(fig, dark, height, ylab="Interval width (BDT)",
                       xlab="Days ahead", legend=False)


# --------------------------------------------------------------------------
# Model comparison
# --------------------------------------------------------------------------
def metric_bars(comp: pd.DataFrame, metric: str, dark=False, height=360) -> go.Figure:
    fig = go.Figure()
    for model in comp["model"].unique():
        sub = comp[comp["model"] == model]
        fig.add_trace(go.Bar(
            x=[pretty_name(c) for c in sub["commodity"]], y=sub[metric],
            name=model,
            marker=dict(color=_rgba(model_color(model), 0.88), line=dict(width=0)),
            hovertemplate="%{x}: %{y:,.3f}<extra>" + model + "</extra>"))
    fig = base_layout(fig, dark, height, title=metric.replace("_", " "), ylab=metric)
    fig.update_layout(barmode="group", bargap=0.34, bargroupgap=0.08)
    fig.update_xaxes(showline=False, ticks="")
    return fig


def radar_chart(comp: pd.DataFrame, commodity: str, dark=False, height=400) -> go.Figure:
    """Normalised skill profile — larger area is better on every axis."""
    sub = comp[(comp["commodity"] == commodity) & (comp["model"] != "Seasonal Naive")]
    if sub.empty:
        return base_layout(go.Figure(), dark, height, legend=False)
    axes = [("MAE", True), ("RMSE", True), ("MAPE_%", True), ("R2", False)]
    fig = go.Figure()
    for _, row in sub.iterrows():
        vals = []
        for metric, lower_better in axes:
            col = sub[metric]
            lo, hi = float(col.min()), float(col.max())
            span = hi - lo if hi > lo else 1.0
            v = (float(row[metric]) - lo) / span
            vals.append(1 - v if lower_better else v)
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=[a[0].replace("_%", " %") for a in axes] + [axes[0][0]],
            fill="toself", name=row["model"],
            line=dict(color=model_color(row["model"]), width=2),
            fillcolor=_rgba(model_color(row["model"]), 0.13)))
    tone = surface(dark)
    fig.update_layout(
        template=_template(dark), height=height,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=False,
                            gridcolor=tone["grid"], linecolor=tone["grid"]),
            angularaxis=dict(gridcolor=tone["grid"], linecolor=tone["axis"],
                             tickfont=dict(family=FONT, size=11, color=tone["muted"])),
        ),
        margin=dict(l=46, r=46, t=34, b=34),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=11.5,
                                                             color=tone["muted"]),
                    itemsizing="constant", bgcolor="rgba(0,0,0,0)"),
        font=dict(family=FONT, size=11.5, color=tone["text"]),
        hoverlabel=dict(bgcolor=tone["hover_bg"], bordercolor=tone["border_bold"],
                        font=dict(family=MONO, size=11.5, color=tone["text"])),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=tone["muted"],
                     activecolor=tone["accent"]),
    )
    return fig


def actual_vs_predicted(df: pd.DataFrame, dark=False, height=400) -> go.Figure:
    fig = go.Figure()
    ref = df[df["model"] == df["model"].iloc[0]]
    fig.add_trace(go.Scatter(x=ref["date"], y=ref["actual"], name="Actual", mode="lines",
                             line=dict(color=surface(dark)["text"], width=2.2),
                             hovertemplate="%{y:,.2f}<extra>Actual</extra>"))
    for model in df["model"].unique():
        sub = df[df["model"] == model]
        fig.add_trace(go.Scatter(x=sub["date"], y=sub["pred"], name=model, mode="lines",
                                 line=dict(color=model_color(model), width=1.5),
                                 hovertemplate="%{y:,.2f}<extra>" + model + "</extra>"))
    return base_layout(fig, dark, height, ylab="Price (BDT)")


def error_distribution(df: pd.DataFrame, dark=False, height=360) -> go.Figure:
    fig = go.Figure()
    for model in df["model"].unique():
        sub = df[df["model"] == model]
        col = model_color(model)
        fig.add_trace(go.Violin(y=sub["actual"] - sub["pred"], name=model,
                                line_color=col, fillcolor=_rgba(col, 0.22),
                                box_visible=True, meanline_visible=True,
                                opacity=0.9, points=False,
                                width=0.72))
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color=surface(dark)["axis"])
    fig = base_layout(fig, dark, height, ylab="Actual − predicted (BDT)", legend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(showline=False, ticks="",
                     tickfont=dict(family=FONT, size=11.5, color=surface(dark)["muted"]))
    return fig


def calibration_scatter(df: pd.DataFrame, dark=False, height=400) -> go.Figure:
    fig = go.Figure()
    for model in df["model"].unique():
        sub = df[df["model"] == model]
        col = model_color(model)
        fig.add_trace(go.Scatter(
            x=sub["actual"], y=sub["pred"], mode="markers", name=model,
            marker=dict(color=_rgba(col, 0.5), size=6.5,
                        line=dict(color=_rgba(col, 0.9), width=0.8)),
            hovertemplate="actual %{x:,.2f} · predicted %{y:,.2f}"
                          "<extra>" + model + "</extra>"))
    lo = float(df["actual"].min()) * 0.97
    hi = float(df["actual"].max()) * 1.03
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Perfect",
                             line=dict(color=surface(dark)["axis"], dash="dash",
                                       width=1.4),
                             hoverinfo="skip"))
    fig = base_layout(fig, dark, height, xlab="Actual (BDT)", ylab="Predicted (BDT)")
    fig.update_layout(hovermode="closest")
    return fig


def inflation_bars(df: pd.DataFrame, value_col="inflation_%", dark=False,
                   height=360, lower_col=None, upper_col=None) -> go.Figure:
    tone = surface(dark)
    labels = [pretty_name(c) for c in df["commodity"]]
    vals = df[value_col].values
    colors = [PALETTE["alert"] if v > 0 else PALETTE["sage"] for v in vals]
    err = None
    if lower_col and upper_col and lower_col in df and upper_col in df:
        err = dict(type="data", symmetric=False,
                   array=np.clip(df[upper_col].values - vals, 0, None),
                   arrayminus=np.clip(vals - df[lower_col].values, 0, None),
                   color=tone["muted"], thickness=1.2, width=6)
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=[_rgba(c, 0.85) for c in colors], line=dict(width=0)),
        error_y=err, cliponaxis=False,
        text=[f"{v:+.2f}%" for v in vals], textposition="outside",
        textfont=dict(family=FONT, size=11.5, color=tone["text_soft"]),
        hovertemplate="%{x}: %{y:+.2f}%<extra></extra>"))
    fig.add_hline(y=0, line_width=1.2, line_color=tone["axis"])
    fig = base_layout(fig, dark, height, ylab="Projected inflation (%)", legend=False)
    fig.update_layout(bargap=0.5, hovermode="closest")
    fig.update_xaxes(showline=False, ticks="",
                     tickfont=dict(family=FONT, size=11.5, color=tone["text_soft"]))
    return fig
