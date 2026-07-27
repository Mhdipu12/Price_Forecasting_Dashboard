"""Visual identity: design tokens, page furniture and KPI cards.

Colour, typography and radii are configured natively in `.streamlit/config.toml`.
What lives here is the small set of composite components Streamlit has no
primitive for — the page header, the section rule, the note callout and the KPI
card — plus the design tokens they share.

The signature component is `kpi_card`, whose *price ribbon* shows where today's
price sits inside its own 52-week range — a genuinely informative device rather
than a decorative one.
"""
from __future__ import annotations

import html

import streamlit as st

from .config import APP_TITLE, PAGE_ICON, PALETTE, SURFACE


# --------------------------------------------------------------------------
# Appearance
# --------------------------------------------------------------------------
def appearance() -> str:
    """The active Streamlit appearance, "light" or "dark".

    Falls back to light when the browser has not reported a theme yet, which
    happens on the very first paint and in the headless test harness.
    """
    try:
        kind = getattr(getattr(st, "context", None), "theme", None)
        kind = getattr(kind, "type", None)
    except Exception:
        kind = None
    return "dark" if kind == "dark" else "light"


def _tint(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _tokens(mode: str) -> str:
    """The design tokens for one appearance, as CSS custom properties."""
    s = SURFACE[mode]
    shadow = (
        "0 1px 2px rgba(15,23,42,.05), 0 1px 3px rgba(15,23,42,.05)"
        if mode == "light" else
        "0 1px 2px rgba(0,0,0,.30), 0 1px 3px rgba(0,0,0,.24)"
    )
    lift = (
        "0 6px 16px rgba(15,23,42,.09), 0 2px 5px rgba(15,23,42,.06)"
        if mode == "light" else
        "0 8px 22px rgba(0,0,0,.42), 0 2px 6px rgba(0,0,0,.32)"
    )
    return f"""
  --bd-surface:      {s['surface']};
  --bd-surface-alt:  {s['surface_alt']};
  --bd-border:       {s['border']};
  --bd-border-bold:  {s['border_bold']};
  --bd-text:         {s['text']};
  --bd-text-soft:    {s['text_soft']};
  --bd-muted:        {s['muted']};
  --bd-accent:       {s['accent']};
  --bd-accent-tint:  {_tint(s['accent'], 0.10)};
  --bd-accent-line:  {_tint(s['accent'], 0.26)};
  --bd-pos:          {s['positive']};
  --bd-neg:          {s['negative']};
  --bd-pos-tint:     {_tint(s['positive'], 0.12)};
  --bd-neg-tint:     {_tint(s['negative'], 0.12)};
  --bd-pos-soft:     {_tint(s['positive'], 0.55)};
  --bd-neg-soft:     {_tint(s['negative'], 0.55)};
  --bd-flat-tint:    {_tint(s['muted'], 0.12)};
  --bd-shadow:       {shadow};
  --bd-shadow-lift:  {lift};
  --bd-radius:       12px;
  --bd-radius-sm:    8px;
"""


_TOKEN_SLOT = "/* @tokens */"

_CSS = """
<style>
:root { /* @tokens */ }

/* ================= layout rhythm ==================================== */
[data-testid="stMainBlockContainer"] {
  padding-top: 2.4rem;
  padding-bottom: 4rem;
  max-width: 1500px;
}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 { letter-spacing: -0.018em; }
[data-testid="stMain"] h5 {
  letter-spacing: -0.005em;
  margin-bottom: 0.35rem;
}
[data-testid="stMain"] hr { border-color: var(--bd-border); margin: 2rem 0 1.6rem; }
[data-testid="stMarkdownContainer"] p { line-height: 1.62; }
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] { color: var(--bd-muted); line-height: 1.55; }
[data-testid="stElementToolbarButton"] { opacity: 0.55; }

/* ================= page header ====================================== */
.bd-header {
  margin: 0 0 1.55rem 0;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--bd-border);
}
.bd-eyebrow {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--bd-accent);
  background: var(--bd-accent-tint);
  border: 1px solid var(--bd-accent-line);
  padding: 0.2rem 0.55rem; border-radius: 999px;
  margin-bottom: 0.7rem;
}
.bd-title {
  font-size: 2rem; font-weight: 700; line-height: 1.12;
  color: var(--bd-text); margin: 0; letter-spacing: -0.026em;
}
.bd-lede {
  font-size: 0.94rem; color: var(--bd-muted); margin: 0.5rem 0 0 0;
  max-width: 74ch; line-height: 1.6;
}

/* ================= section rule ===================================== */
.bd-section {
  display: flex; align-items: center; gap: 0.7rem;
  margin: 1.9rem 0 0.55rem 0;
}
.bd-section-text {
  font-size: 1.03rem; font-weight: 600; color: var(--bd-text);
  letter-spacing: -0.012em; white-space: nowrap;
}
.bd-section-rule {
  flex: 1; height: 1px; background: var(--bd-border);
}

/* ================= KPI card ========================================= */
/* Stretch only the columns that hold a KPI card, so every card in a row
   ends at the same baseline whether or not it carries a price ribbon. */
[data-testid="stColumn"]:has(.bd-kpi) [data-testid="stVerticalBlock"],
[data-testid="stColumn"]:has(.bd-kpi) [data-testid="stElementContainer"],
[data-testid="stColumn"]:has(.bd-kpi) [data-testid="stMarkdown"],
[data-testid="stColumn"]:has(.bd-kpi) [data-testid="stMarkdown"] > div,
[data-testid="stColumn"]:has(.bd-kpi) [data-testid="stMarkdownContainer"] {
  height: 100%; align-items: stretch;
}
.bd-kpi {
  position: relative; overflow: hidden;
  display: flex; flex-direction: column;
  background: var(--bd-surface);
  border: 1px solid var(--bd-border);
  border-radius: var(--bd-radius);
  padding: 0.95rem 1.05rem 0.9rem 1.15rem;
  height: 100%; min-height: 148px;
  box-shadow: var(--bd-shadow);
  transition: box-shadow .18s ease, border-color .18s ease, transform .18s ease;
}
.bd-kpi::before {
  content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 3px;
  background: var(--accent, var(--bd-accent));
}
.bd-kpi:hover {
  box-shadow: var(--bd-shadow-lift);
  border-color: var(--bd-border-bold);
  transform: translateY(-1px);
}
.bd-kpi-head {
  display: flex; align-items: flex-start; gap: 0.42rem;
  min-height: 1.95rem;  /* two label lines, so every value in a row aligns */
}
.bd-kpi-dot {
  width: 7px; height: 7px; border-radius: 50%; flex: 0 0 auto;
  margin-top: 0.28rem;
  background: var(--accent, var(--bd-accent));
}
.bd-kpi-label {
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.085em;
  line-height: 1.35; text-transform: uppercase; color: var(--bd-muted);
}
.bd-kpi-value {
  font-size: clamp(1.34rem, 1.15vw + 0.72rem, 1.72rem);
  font-weight: 600; color: var(--bd-text);
  line-height: 1.15; margin: 0.15rem 0 0 0;
  letter-spacing: -0.028em; font-variant-numeric: tabular-nums;
}
.bd-kpi-unit {
  font-size: 0.74rem; font-weight: 500; color: var(--bd-muted);
  margin-left: 0.3rem; letter-spacing: 0; white-space: nowrap;
}
.bd-kpi-foot {
  display: flex; align-items: center; flex-wrap: wrap; gap: 0.45rem;
  margin-top: 0.5rem;
}
.bd-kpi-delta {
  display: inline-flex; align-items: center; gap: 0.22rem;
  font-size: 0.76rem; font-weight: 600; font-variant-numeric: tabular-nums;
  padding: 0.14rem 0.46rem; border-radius: 999px; line-height: 1.35;
}
.bd-up   { color: var(--bd-neg); background: var(--bd-neg-tint); }
.bd-down { color: var(--bd-pos); background: var(--bd-pos-tint); }
.bd-flat { color: var(--bd-muted); background: var(--bd-flat-tint); }
.bd-kpi-caption { font-size: 0.74rem; color: var(--bd-muted); }

/* ---- price ribbon: position within the 52-week range --------------- */
.bd-ribbon-wrap { margin-top: auto; padding-top: 0.85rem; }
.bd-ribbon-legend {
  font-size: 0.6rem; font-weight: 600; letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--bd-muted);
  margin-bottom: 0.4rem; white-space: nowrap;
}
.bd-ribbon {
  position: relative; height: 5px; border-radius: 999px;
  background: linear-gradient(90deg,
              var(--bd-pos-soft) 0%,
              var(--bd-border-bold) 50%,
              var(--bd-neg-soft) 100%);
}
.bd-ribbon-mark {
  position: absolute; top: 50%; width: 11px; height: 11px; border-radius: 50%;
  transform: translate(-50%, -50%);
  background: var(--accent, var(--bd-accent));
  border: 2px solid var(--bd-surface);
  box-shadow: 0 0 0 1px var(--accent, var(--bd-accent));
}
.bd-ribbon-scale {
  display: flex; justify-content: space-between; gap: 0.6rem;
  margin-top: 0.42rem; font-size: 0.66rem; color: var(--bd-muted);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}

/* ================= note callout ===================================== */
.bd-note {
  background: var(--bd-surface-alt);
  border: 1px solid var(--bd-border);
  border-left: 3px solid var(--bd-accent);
  border-radius: var(--bd-radius-sm);
  padding: 0.8rem 1rem;
  color: var(--bd-text-soft);
  font-size: 0.87rem; line-height: 1.62;
  margin: 0.55rem 0 1.1rem 0;
}
.bd-note strong { color: var(--bd-text); font-weight: 600; }

/* ================= insight cards ==================================== */
.bd-insight {
  background: var(--bd-surface);
  border: 1px solid var(--bd-border);
  border-left: 3px solid var(--tone, var(--bd-accent));
  border-radius: var(--bd-radius);
  padding: 0.9rem 1.05rem;
  margin-bottom: 0.75rem;
  box-shadow: var(--bd-shadow);
  transition: box-shadow .18s ease, border-color .18s ease;
}
.bd-insight:hover {
  box-shadow: var(--bd-shadow-lift);
  border-color: var(--bd-border-bold);
  border-left-color: var(--tone, var(--bd-accent));
}
.bd-insight-kind {
  font-size: 0.65rem; font-weight: 600; letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--tone, var(--bd-muted));
}
.bd-insight-head {
  font-size: 0.97rem; font-weight: 600; color: var(--bd-text);
  margin: 0.3rem 0 0.32rem; line-height: 1.38; letter-spacing: -0.012em;
}
.bd-insight-body {
  font-size: 0.87rem; line-height: 1.62; color: var(--bd-text-soft);
}
.bd-summary {
  background: var(--bd-surface);
  border: 1px solid var(--bd-border);
  border-top: 3px solid var(--bd-accent);
  border-radius: var(--bd-radius);
  padding: 1.05rem 1.25rem;
  font-size: 0.96rem; line-height: 1.66; color: var(--bd-text-soft);
  box-shadow: var(--bd-shadow);
}

/* ================= inline meta text ================================= */
.bd-meta { color: var(--bd-muted); font-size: 0.85rem; line-height: 1.5; }
.bd-meta-num {
  color: var(--bd-muted); font-size: 0.82rem; font-weight: 500;
  font-variant-numeric: tabular-nums;
}

/* ================= tag ============================================== */
.bd-tag {
  display: inline-block; font-size: 0.66rem; font-weight: 600;
  letter-spacing: 0.07em; text-transform: uppercase;
  padding: 0.16rem 0.5rem; border-radius: 999px;
  border: 1px solid var(--bd-border); background: var(--bd-surface-alt);
  color: var(--bd-muted); margin-right: 0.35rem;
}

/* ================= sidebar ========================================== */
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.6rem; }
[data-testid="stSidebarNav"] { padding-top: 0.4rem; }
[data-testid="stSidebarNav"]::before {
  content: "Pages";
  display: block; padding: 0 0.75rem 0.35rem;
  font-size: 0.64rem; font-weight: 600; letter-spacing: 0.13em;
  text-transform: uppercase; color: var(--bd-muted);
}
[data-testid="stSidebarNavLink"] { border-radius: var(--bd-radius-sm); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size: 0.98rem; }
.bd-side-label {
  font-size: 0.64rem; font-weight: 600; letter-spacing: 0.13em;
  text-transform: uppercase; color: var(--bd-muted);
  margin: 0.2rem 0 0.35rem 0;
}
.bd-brand {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.15rem 0 0.9rem 0; margin-bottom: 0.85rem;
  border-bottom: 1px solid var(--bd-border);
}
.bd-brand-mark {
  flex: 0 0 auto; width: 34px; height: 34px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bd-accent); color: #fff;
  font-size: 0.82rem; font-weight: 700; letter-spacing: 0.02em;
}
.bd-brand-name {
  font-size: 0.92rem; font-weight: 600; line-height: 1.24;
  color: var(--bd-text); letter-spacing: -0.012em;
}
.bd-brand-kicker {
  font-size: 0.63rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--bd-muted); margin-top: 0.12rem;
}
.bd-side-meta {
  display: flex; align-items: flex-start; gap: 0.45rem;
  margin-top: 1.3rem; padding-top: 0.85rem;
  border-top: 1px solid var(--bd-border);
  font-size: 0.72rem; color: var(--bd-muted); line-height: 1.5;
}
.bd-side-meta .bd-dot {
  width: 6px; height: 6px; border-radius: 50%; margin-top: 0.36rem;
  background: var(--bd-pos); flex: 0 0 auto;
}

/* ================= data display ===================================== */
[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }
[data-testid="stMetric"] { font-variant-numeric: tabular-nums; }
[data-testid="stPlotlyChart"] {
  border: 1px solid var(--bd-border);
  border-radius: var(--bd-radius);
  background: var(--bd-surface);
  padding: 0.55rem 0.6rem 0.35rem;
}

/* ================= tabs, expanders, controls ======================== */
[data-testid="stTabs"] [role="tablist"] { gap: 1.35rem; }
[data-testid="stTab"] { color: var(--bd-muted); transition: color .15s ease; }
[data-testid="stTab"]:hover { color: var(--bd-text); }
[data-testid="stTab"][aria-selected="true"] { font-weight: 600; }
[data-testid="stTabPanel"] { padding-top: 0.5rem; }
[data-testid="stExpander"] details {
  border-radius: var(--bd-radius-sm); border-color: var(--bd-border);
}
[data-testid="stExpander"] summary { font-weight: 500; }
[data-testid="stDownloadButton"] button, [data-testid="stBaseButton-secondary"] {
  font-weight: 500;
}
</style>
"""


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
def setup_page(page_title: str, layout: str = "wide") -> None:
    """Call once at the top of every page."""
    st.set_page_config(
        page_title=f"{page_title} · {APP_TITLE}",
        page_icon=PAGE_ICON,
        layout=layout,
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS.replace(_TOKEN_SLOT, _tokens(appearance())), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Page furniture
# --------------------------------------------------------------------------
def page_header(eyebrow: str, title: str, lede: str = "") -> None:
    lede_html = f'<p class="bd-lede">{html.escape(lede)}</p>' if lede else ""
    st.markdown(
        f'<div class="bd-header">'
        f'<span class="bd-eyebrow">{html.escape(eyebrow)}</span>'
        f'<h1 class="bd-title">{html.escape(title)}</h1>'
        f"{lede_html}</div>",
        unsafe_allow_html=True,
    )


def section(text: str) -> None:
    """A section heading with a hairline rule running to the right margin."""
    st.markdown(
        f'<div class="bd-section"><span class="bd-section-text">{html.escape(text)}</span>'
        f'<span class="bd-section-rule"></span></div>',
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    st.markdown(f'<div class="bd-note">{text}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# KPI cards
# --------------------------------------------------------------------------
def kpi_card(
    label: str,
    value: str,
    unit: str = "",
    delta: float | None = None,
    delta_suffix: str = "%",
    delta_caption: str = "",
    accent: str = PALETTE["ink"],
    ribbon: tuple[float, float, float] | None = None,
) -> str:
    """Return the HTML for one KPI card.

    ribbon: (low, high, current) — draws the 52-week range with a marker at
    the current price, so a glance tells you whether today is cheap or dear.
    """
    foot_parts = []
    if delta is not None:
        cls = "bd-flat" if abs(delta) < 1e-9 else ("bd-up" if delta > 0 else "bd-down")
        arrow = "→" if abs(delta) < 1e-9 else ("↑" if delta > 0 else "↓")
        foot_parts.append(
            f'<span class="bd-kpi-delta {cls}">{arrow} {abs(delta):,.2f}{delta_suffix}</span>')
    if delta_caption:
        foot_parts.append(
            f'<span class="bd-kpi-caption">{html.escape(delta_caption)}</span>')
    foot_html = f'<div class="bd-kpi-foot">{"".join(foot_parts)}</div>' if foot_parts else ""

    ribbon_html = ""
    if ribbon:
        low, high, cur = ribbon
        span = max(high - low, 1e-9)
        pct = min(max((cur - low) / span, 0.0), 1.0) * 100
        ribbon_html = (
            '<div class="bd-ribbon-wrap">'
            '<div class="bd-ribbon-legend">52-week range</div>'
            f'<div class="bd-ribbon"><div class="bd-ribbon-mark" style="left:{pct:.1f}%"></div></div>'
            f'<div class="bd-ribbon-scale"><span>{low:,.0f}</span>'
            f"<span>{high:,.0f}</span></div></div>"
        )

    unit_html = f'<span class="bd-kpi-unit">{html.escape(unit)}</span>' if unit else ""
    return (
        f'<div class="bd-kpi" style="--accent:{accent}">'
        f'<div class="bd-kpi-head"><span class="bd-kpi-dot"></span>'
        f'<span class="bd-kpi-label">{html.escape(label)}</span></div>'
        f'<div class="bd-kpi-value">{value}{unit_html}</div>'
        f"{foot_html}{ribbon_html}</div>"
    )


def render_kpis(cards: list[str], per_row: int = 3) -> None:
    """Lay out KPI cards in an evenly spaced grid.

    Every row is built with `per_row` columns even when the last row is short,
    so cards keep the same width down the whole grid instead of stretching.
    """
    if not cards:
        return
    per_row = max(1, per_row)
    for i in range(0, len(cards), per_row):
        row = cards[i : i + per_row]
        cols = st.columns(per_row, gap="medium")
        for col, card in zip(cols, row):
            col.markdown(card, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def sidebar_brand() -> None:
    st.sidebar.markdown(
        '<div class="bd-brand">'
        '<div class="bd-brand-mark">BD</div>'
        "<div><div class=\"bd-brand-name\">Essential Commodity<br>Price Monitor</div>"
        '<div class="bd-brand-kicker">Thesis dashboard</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )


def sidebar_label(text: str) -> None:
    """A small uppercase group label for the sidebar."""
    st.sidebar.markdown(
        f'<div class="bd-side-label">{html.escape(text)}</div>', unsafe_allow_html=True)
