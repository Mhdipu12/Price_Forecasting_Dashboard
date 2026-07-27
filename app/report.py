"""Export helpers: CSV bundles, chart files, and a self-contained HTML report.

The report deliberately uses no external assets, so a single downloaded file
opens correctly offline and prints cleanly to PDF from a browser.
"""
from __future__ import annotations

import html
import io
import zipfile
from datetime import datetime

import pandas as pd

from . import data as D
from . import insights as I
from .config import APP_TITLE, pretty_name, unit_for


# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def fig_to_html_bytes(fig) -> bytes:
    return fig.to_html(include_plotlyjs="cdn", full_html=True).encode("utf-8")


def fig_to_png_bytes(fig, scale: int = 2) -> bytes | None:
    """PNG export needs kaleido; returns None when it is unavailable."""
    try:
        return fig.to_image(format="png", scale=scale)
    except Exception:
        return None


def build_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in files.items():
            z.writestr(name, payload)
    return buf.getvalue()


# --------------------------------------------------------------------------
# HTML report
# --------------------------------------------------------------------------
_REPORT_CSS = """
:root { --ink:#0F172A; --soft:#475569; --muted:#64748B; --rule:#E4E8EE;
        --surface:#F8FAFC; --accent:#2563EB; --sage:#047857; --alert:#C2261E; }
* { box-sizing: border-box; }
body { font-family: Inter, -apple-system, Segoe UI, sans-serif; color: var(--ink);
       max-width: 960px; margin: 0 auto; padding: 48px 30px 84px; line-height: 1.62;
       background: #fff; font-size: 15px; }
h1 { font-size: 2rem; font-weight: 700; letter-spacing:-0.026em; margin: 0 0 .2rem; }
h2 { font-size: 1.16rem; font-weight: 600; letter-spacing:-0.014em;
     margin: 2.5rem 0 .7rem; padding-bottom: .45rem;
     border-bottom: 1px solid var(--rule); }
h3 { font-size: 1rem; font-weight: 600; margin: 1.6rem 0 .4rem; }
.eyebrow { display:inline-block; font-size:.68rem; font-weight:600;
           letter-spacing:.11em; text-transform:uppercase; color: var(--accent);
           background:rgba(37,99,235,.10); border:1px solid rgba(37,99,235,.26);
           padding:.2rem .55rem; border-radius:999px; margin-bottom:.7rem; }
.lede { color: var(--muted); font-size:.94rem; margin:.45rem 0 0; }
table { border-collapse: collapse; width: 100%; margin: .85rem 0 1.3rem; font-size:.86rem; }
th, td { text-align: left; padding: .52rem .65rem; border-bottom: 1px solid var(--rule); }
thead th { background: var(--surface); }
th { font-size:.66rem; letter-spacing:.07em; text-transform: uppercase;
     color: var(--muted); font-weight:600; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.card { border:1px solid var(--rule); border-radius:12px; padding:.95rem 1.1rem;
        margin:.65rem 0; background:#fff; }
.card.good { border-left:3px solid var(--sage); }
.card.bad  { border-left:3px solid var(--alert); }
.card.neutral { border-left:3px solid var(--rule); }
.card h4 { margin:0 0 .28rem; font-size:.96rem; font-weight:600; }
.card p { margin:0; color:var(--soft); font-size:.88rem; }
.kpis { display:flex; flex-wrap:wrap; gap:14px; margin:1.1rem 0 1.5rem; }
.kpi { flex:1 1 190px; border:1px solid var(--rule); border-left:3px solid var(--accent);
       border-radius:12px; padding:.85rem .95rem; background:#fff; }
.kpi .l { font-size:.66rem; font-weight:600; letter-spacing:.085em;
          text-transform:uppercase; color:var(--muted); }
.kpi .v { font-size:1.5rem; font-weight:600; margin-top:.3rem;
          letter-spacing:-0.028em; font-variant-numeric: tabular-nums; }
.up { color: var(--alert); } .down { color: var(--sage); }
footer { margin-top:3.2rem; padding-top:1.1rem; border-top:1px solid var(--rule);
         color:var(--muted); font-size:.78rem; }
@media print { body { padding: 0; } h2 { page-break-after: avoid; } .card { page-break-inside: avoid; } }
"""


def _table(df: pd.DataFrame, num_cols: list[str] | None = None, floatfmt="{:,.3f}") -> str:
    if df is None or df.empty:
        return "<p class='lede'>No data available.</p>"
    num_cols = num_cols or [c for c in df.columns
                            if pd.api.types.is_numeric_dtype(df[c])]
    head = "".join(
        f'<th class="{"num" if c in num_cols else ""}">{html.escape(str(c))}</th>'
        for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in df.columns:
            v = r[c]
            if c in num_cols and pd.notna(v) and isinstance(v, (int, float)):
                cells.append(f'<td class="num">{floatfmt.format(v)}</td>')
            else:
                cells.append(f"<td>{html.escape(str(v))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def build_html_report(horizon: int = 30, commodities: list[str] | None = None) -> str:
    commodities = commodities or D.commodities()
    reg = D.load_registry()
    comp = D.load_comparison()
    infl = D.load_inflation()
    composite = D.load_composite()
    generated = datetime.now().strftime("%d %B %Y, %H:%M")

    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>{html.escape(APP_TITLE)} — summary report</title>",
        f"<style>{_REPORT_CSS}</style></head><body>",
        "<div class='eyebrow'>Forecast summary report</div>",
        f"<h1>{html.escape(APP_TITLE)}</h1>",
        f"<p class='lede'>Generated {html.escape(generated)} · "
        f"{horizon}-day outlook · models: SARIMA, XGBoost, LSTM</p>",
    ]

    # ---- market overview -------------------------------------------------
    parts.append("<h2>Market overview</h2>")
    parts.append(f"<p>{html.escape(I.market_overview(horizon))}</p>")

    if not composite.empty:
        row = composite[composite["horizon_days"] == horizon]
        if not row.empty:
            v = float(row.iloc[0]["composite_inflation_%"])
            cls = "up" if v > 0 else "down"
            parts.append(
                "<div class='kpis'><div class='kpi'>"
                "<div class='l'>Composite essential-goods inflation</div>"
                f"<div class='v {cls}'>{v:+.2f}%</div></div></div>")

    # ---- per commodity ---------------------------------------------------
    for c in commodities:
        ins = I.build(c, horizon)
        if not ins.snapshot:
            continue
        snap = ins.snapshot
        unit = unit_for(c)
        parts.append(f"<h2>{html.escape(pretty_name(c))}</h2>")
        parts.append(f"<p>{html.escape(ins.summary)}</p>")

        def kpi(label, value, cls=""):
            return (f"<div class='kpi'><div class='l'>{html.escape(label)}</div>"
                    f"<div class='v {cls}'>{value}</div></div>")

        parts.append(
            "<div class='kpis'>"
            + kpi("Latest price", f"{snap['price']:,.2f}")
            + kpi("30-day change", f"{snap['change_30d']:+.2f}%",
                  "up" if snap["change_30d"] > 0 else "down")
            + kpi("52-week low", f"{snap['low_52w']:,.2f}")
            + kpi("52-week high", f"{snap['high_52w']:,.2f}")
            + kpi("30-day volatility", f"{snap['volatility_30d']:.2f}%")
            + "</div>")

        for item in ins.items:
            parts.append(
                f"<div class='card {item.tone}'><h4>{html.escape(item.headline)}</h4>"
                f"<p>{html.escape(item.detail)}</p></div>")

        if not infl.empty:
            sub = infl[infl["commodity"] == c][
                ["model", "horizon_days", "forecast_price_end", "inflation_%",
                 "annualised_inflation_%"]]
            parts.append("<h3>Projected prices and inflation</h3>")
            parts.append(_table(sub.round(3)))

        if not comp.empty:
            sub = comp[comp["commodity"] == c][
                ["model", "MAE", "RMSE", "MAPE_%", "R2", "skill_vs_naive_%"]]
            parts.append("<h3>Model accuracy on the held-out test set</h3>")
            parts.append(_table(sub.round(4)))
            best = reg.get("commodities", {}).get(c, {}).get("best_model", "")
            if best:
                parts.append(f"<p class='lede'>Recommended model: <strong>"
                             f"{html.escape(best)}</strong>. Lower MAE, RMSE and MAPE are "
                             f"better; higher R² and skill are better.</p>")

    # ---- methodology -----------------------------------------------------
    parts.append("<h2>Method and limitations</h2>")
    parts.append(
        "<p>Prices were cleaned to a complete daily calendar, with short gaps interpolated "
        "and local outliers winsorized rather than deleted so that genuine supply shocks are "
        "preserved. Models were trained on a chronological split with the final period held "
        "out entirely, and compared one-step-ahead against a seasonal naive baseline. "
        "Multi-step forecasts are produced recursively, so uncertainty widens with the "
        "horizon; intervals shown are 95% and assume the error distribution observed in "
        "training continues to hold. Forecasts do not account for policy announcements, "
        "import bans, or other shocks that have no precedent in the training data.</p>")

    parts.append(
        f"<footer>{html.escape(APP_TITLE)} · generated automatically from "
        f"registry.json and the precomputed forecast tables. "
        f"Figures are model output, not official statistics.</footer></body></html>")
    return "".join(parts)


def build_full_bundle(horizon: int = 30) -> bytes:
    """Everything a reader might want, in one zip."""
    files: dict[str, bytes] = {}
    fc = D.load_forecasts()
    if not fc.empty:
        files["forecasts/future_forecasts.csv"] = df_to_csv_bytes(fc)
        best = fc[fc["is_best_model"]] if "is_best_model" in fc else fc
        files["forecasts/best_model_forecasts.csv"] = df_to_csv_bytes(best)
    for name, loader in [("inflation/future_inflation.csv", D.load_inflation),
                         ("inflation/composite_inflation.csv", D.load_composite),
                         ("evaluation/model_comparison.csv", D.load_comparison),
                         ("evaluation/test_predictions.csv", D.load_test_predictions),
                         ("data/price_history.csv", D.load_prices)]:
        df = loader()
        if not df.empty:
            files[name] = df_to_csv_bytes(df)
    files["summary_report.html"] = build_html_report(horizon).encode("utf-8")
    files["registry.json"] = pd.Series(D.load_registry()).to_json(indent=2).encode("utf-8")
    return build_zip(files)
