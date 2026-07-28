"""Visual identity: design tokens, page furniture and KPI cards.

The dashboard wears an *aurora* canvas under *glassmorphic* panels. Three
slow-drifting light sources — violet, cyan and magenta — are painted behind the
whole page, and every surface above them (KPI card, chart frame, callout,
sidebar) is a frosted pane that lets that light through. The effect is carried
by the tokens in `_tokens` and the stylesheet in `_CSS`; nothing in the page
code has to know about it.

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
    light = mode == "light"
    shadow = (
        "0 10px 30px -14px rgba(23,29,80,.20), 0 2px 6px rgba(23,29,80,.05)"
        if light else
        "0 16px 40px -18px rgba(0,0,0,.80), 0 2px 8px rgba(0,0,0,.40)"
    )
    lift = (
        "0 22px 46px -18px rgba(23,29,80,.28), 0 4px 12px rgba(23,29,80,.08)"
        if light else
        "0 28px 60px -22px rgba(0,0,0,.90), 0 4px 14px rgba(0,0,0,.50)"
    )
    return f"""
  --bd-canvas:       {s['canvas']};
  --bd-surface:      {s['surface']};
  --bd-surface-alt:  {s['surface_alt']};
  --bd-border:       {s['border']};
  --bd-border-bold:  {s['border_bold']};
  --bd-text:         {s['text']};
  --bd-text-soft:    {s['text_soft']};
  --bd-muted:        {s['muted']};
  --bd-accent:       {s['accent']};
  --bd-accent-tint:  {_tint(s['accent'], 0.12)};
  --bd-accent-line:  {_tint(s['accent'], 0.30)};
  --bd-accent-glow:  {_tint(s['accent'], 0.55 if light else 0.40)};
  --bd-pos:          {s['positive']};
  --bd-neg:          {s['negative']};
  --bd-pos-tint:     {_tint(s['positive'], 0.14)};
  --bd-neg-tint:     {_tint(s['negative'], 0.14)};
  --bd-pos-soft:     {_tint(s['positive'], 0.55)};
  --bd-neg-soft:     {_tint(s['negative'], 0.55)};
  --bd-flat-tint:    {_tint(s['muted'], 0.14)};

  /* ---- aurora light sources ---- */
  --bd-aur-1:        {s['aurora_1']};
  --bd-aur-2:        {s['aurora_2']};
  --bd-aur-3:        {s['aurora_3']};
  --bd-violet:       {PALETTE['violet']};
  --bd-cyan:         {PALETTE['cyan']};
  --bd-magenta:      {PALETTE['magenta']};
  --bd-grain:        {s['grain']};

  /* ---- frosted glass ---- */
  --bd-glass:        {s['glass']};
  --bd-glass-strong: {s['glass_strong']};
  --bd-glass-border: {s['glass_border']};
  --bd-hairline:     {s['hairline']};
  --bd-blur:         blur(20px) saturate(165%);
  --bd-blur-soft:    blur(12px) saturate(140%);

  --bd-shadow:       {shadow};
  --bd-shadow-lift:  {lift};
  --bd-radius:       16px;
  --bd-radius-sm:    11px;
  --bd-ease:         cubic-bezier(.22,.68,.3,1);
"""


_TOKEN_SLOT = "/* @tokens */"

_GRAIN = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E"
    "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' "
    "numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' "
    "height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")"
)

_CSS = """
<style>
:root { /* @tokens */ }

/* ==================================================================== */
/*  AURORA CANVAS                                                       */
/*  Three slow-drifting light sources sit behind the whole page; a fine  */
/*  grain film on top keeps the gradients from banding. Everything else  */
/*  in the app floats above them on frosted glass.                       */
/* ==================================================================== */
[data-testid="stApp"] {
  background: var(--bd-canvas);
  position: relative;
}
[data-testid="stApp"]::before {
  content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(36% 42% at 16% 12%, var(--bd-aur-1) 0%, transparent 62%),
    radial-gradient(32% 38% at 84% 6%,  var(--bd-aur-2) 0%, transparent 60%),
    radial-gradient(40% 46% at 74% 74%, var(--bd-aur-3) 0%, transparent 64%),
    radial-gradient(34% 36% at 24% 86%, var(--bd-aur-2) 0%, transparent 60%);
  filter: blur(36px);
  animation: bd-aurora 38s var(--bd-ease) infinite alternate;
  will-change: transform;
}
[data-testid="stApp"]::after {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: BD_GRAIN;
  opacity: var(--bd-grain);
  mix-blend-mode: overlay;
}
@keyframes bd-aurora {
  0%   { transform: translate3d(0, 0, 0) scale(1); }
  50%  { transform: translate3d(-2.5%, 2%, 0) scale(1.09); }
  100% { transform: translate3d(2.5%, -2%, 0) scale(1.04); }
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"],
[data-testid="stSidebar"] { position: relative; z-index: 1; }
[data-testid="stMain"] { background: transparent; }
[data-testid="stHeader"] {
  background: transparent;
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
}

/* ================= layout rhythm ==================================== */
[data-testid="stMainBlockContainer"] {
  padding-top: 2.6rem;
  padding-bottom: 4.5rem;
  max-width: 1500px;
}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 { letter-spacing: -0.02em; }
[data-testid="stMain"] h5 {
  letter-spacing: -0.005em;
  margin-bottom: 0.35rem;
}
[data-testid="stMain"] hr {
  border: none; height: 1px; margin: 2.2rem 0 1.7rem;
  background: linear-gradient(90deg, transparent, var(--bd-border) 22%,
              var(--bd-border) 78%, transparent);
}
[data-testid="stMarkdownContainer"] p { line-height: 1.64; }
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] { color: var(--bd-muted); line-height: 1.55; }
[data-testid="stElementToolbarButton"] { opacity: 0.55; }

/* ================= page header ====================================== */
.bd-header {
  position: relative;
  margin: 0 0 1.7rem 0;
  padding-bottom: 1.15rem;
}
.bd-header::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px;
  background: linear-gradient(90deg, var(--bd-accent-line) 0%,
              var(--bd-border) 42%, transparent 100%);
}
.bd-eyebrow {
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-size: 0.67rem; font-weight: 600; letter-spacing: 0.13em;
  text-transform: uppercase; color: var(--bd-accent);
  background: var(--bd-accent-tint);
  border: 1px solid var(--bd-accent-line);
  padding: 0.26rem 0.7rem; border-radius: 999px;
  margin-bottom: 0.8rem;
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
  box-shadow: 0 0 22px -8px var(--bd-accent-glow);
}
.bd-eyebrow::before {
  content: ""; width: 6px; height: 6px; border-radius: 50%;
  background: var(--bd-accent);
  box-shadow: 0 0 0 3px var(--bd-accent-tint);
  animation: bd-pulse 2.6s ease-in-out infinite;
}
@keyframes bd-pulse {
  0%, 100% { opacity: 1;   transform: scale(1); }
  50%      { opacity: .45; transform: scale(.82); }
}
.bd-title {
  font-size: clamp(2rem, 1.4vw + 1.5rem, 2.35rem);
  font-weight: 700; line-height: 1.1;
  margin: 0; letter-spacing: -0.032em;
  background: linear-gradient(96deg, var(--bd-text) 4%, var(--bd-accent) 62%,
              var(--bd-cyan) 100%);
  -webkit-background-clip: text; background-clip: text;
  color: transparent; -webkit-text-fill-color: transparent;
}
.bd-lede {
  font-size: 0.94rem; color: var(--bd-muted); margin: 0.6rem 0 0 0;
  max-width: 74ch; line-height: 1.62;
}

/* ================= section rule ===================================== */
.bd-section {
  display: flex; align-items: center; gap: 0.8rem;
  margin: 2.1rem 0 0.65rem 0;
}
.bd-section-text {
  position: relative;
  font-size: 1.04rem; font-weight: 600; color: var(--bd-text);
  letter-spacing: -0.014em; white-space: nowrap;
  padding-left: 0.75rem;
}
.bd-section-text::before {
  content: ""; position: absolute; left: 0; top: 0.18em; bottom: 0.18em;
  width: 3px; border-radius: 999px;
  background: linear-gradient(180deg, var(--bd-violet), var(--bd-cyan));
}
.bd-section-rule {
  flex: 1; height: 1px;
  background: linear-gradient(90deg, var(--bd-border), transparent);
}

/* ================= glass panels ===================================== */
/* Bordered containers, charts and tables all become the same frosted
   pane, so a page reads as one sheet of glass rather than a pile of
   unrelated boxes. */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"],
[data-testid="stPlotlyChart"],
[data-testid="stExpander"] details {
  background: var(--bd-glass) !important;
  border: 1px solid var(--bd-glass-border) !important;
  border-radius: var(--bd-radius) !important;
  backdrop-filter: var(--bd-blur);
  -webkit-backdrop-filter: var(--bd-blur);
  box-shadow: var(--bd-shadow), inset 0 1px 0 var(--bd-hairline);
  transition: box-shadow .25s var(--bd-ease), border-color .25s var(--bd-ease);
}
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]:hover,
[data-testid="stPlotlyChart"]:hover {
  box-shadow: var(--bd-shadow-lift), inset 0 1px 0 var(--bd-hairline);
}
[data-testid="stPlotlyChart"] { padding: 0.6rem 0.7rem 0.4rem; overflow: hidden; }

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
  position: relative; overflow: hidden; isolation: isolate;
  display: flex; flex-direction: column;
  background: var(--bd-glass);
  border: 1px solid var(--bd-glass-border);
  border-radius: var(--bd-radius);
  backdrop-filter: var(--bd-blur);
  -webkit-backdrop-filter: var(--bd-blur);
  padding: 1.05rem 1.15rem 1rem;
  height: 100%; min-height: 156px;
  box-shadow: var(--bd-shadow), inset 0 1px 0 var(--bd-hairline);
  transition: box-shadow .28s var(--bd-ease), border-color .28s var(--bd-ease),
              transform .28s var(--bd-ease);
}
/* the accent light bleeding in from the top-right corner */
.bd-kpi::before {
  content: ""; position: absolute; z-index: -1;
  top: -70px; right: -60px; width: 190px; height: 190px; border-radius: 50%;
  background: radial-gradient(circle, var(--accent, var(--bd-accent)) 0%,
              transparent 68%);
  opacity: .20; transition: opacity .28s var(--bd-ease);
}
/* a hairline of accent along the top edge */
.bd-kpi::after {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent, var(--bd-accent)) 30%,
              var(--accent, var(--bd-accent)) 62%, transparent);
  opacity: .85;
}
.bd-kpi:hover {
  box-shadow: var(--bd-shadow-lift), inset 0 1px 0 var(--bd-hairline);
  transform: translateY(-3px);
}
.bd-kpi:hover::before { opacity: .34; }
.bd-kpi-head {
  display: flex; align-items: flex-start; gap: 0.45rem;
  min-height: 1.95rem;  /* two label lines, so every value in a row aligns */
}
.bd-kpi-dot {
  width: 7px; height: 7px; border-radius: 50%; flex: 0 0 auto;
  margin-top: 0.3rem;
  background: var(--accent, var(--bd-accent));
  box-shadow: 0 0 10px 1px var(--accent, var(--bd-accent));
}
.bd-kpi-label {
  font-size: 0.67rem; font-weight: 600; letter-spacing: 0.1em;
  line-height: 1.35; text-transform: uppercase; color: var(--bd-muted);
}
.bd-kpi-value {
  font-size: clamp(1.38rem, 1.2vw + 0.74rem, 1.8rem);
  font-weight: 650; color: var(--bd-text);
  line-height: 1.14; margin: 0.2rem 0 0 0;
  letter-spacing: -0.03em; font-variant-numeric: tabular-nums;
}
.bd-kpi-unit {
  font-size: 0.74rem; font-weight: 500; color: var(--bd-muted);
  margin-left: 0.32rem; letter-spacing: 0; white-space: nowrap;
}
.bd-kpi-foot {
  display: flex; align-items: center; flex-wrap: wrap; gap: 0.45rem;
  margin-top: 0.55rem;
}
.bd-kpi-delta {
  display: inline-flex; align-items: center; gap: 0.24rem;
  font-size: 0.76rem; font-weight: 600; font-variant-numeric: tabular-nums;
  padding: 0.18rem 0.55rem; border-radius: 999px; line-height: 1.35;
  border: 1px solid transparent;
}
.bd-up   { color: var(--bd-neg); background: var(--bd-neg-tint);
           border-color: var(--bd-neg-tint); }
.bd-down { color: var(--bd-pos); background: var(--bd-pos-tint);
           border-color: var(--bd-pos-tint); }
.bd-flat { color: var(--bd-muted); background: var(--bd-flat-tint); }
.bd-kpi-caption { font-size: 0.74rem; color: var(--bd-muted); }

/* ---- price ribbon: position within the 52-week range --------------- */
.bd-ribbon-wrap { margin-top: auto; padding-top: 0.9rem; }
.bd-ribbon-legend {
  font-size: 0.6rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--bd-muted);
  margin-bottom: 0.45rem; white-space: nowrap;
}
.bd-ribbon {
  position: relative; height: 6px; border-radius: 999px;
  background: linear-gradient(90deg,
              var(--bd-pos-soft) 0%,
              var(--bd-border-bold) 50%,
              var(--bd-neg-soft) 100%);
  box-shadow: inset 0 0 0 1px var(--bd-glass-border);
}
.bd-ribbon-mark {
  position: absolute; top: 50%; width: 12px; height: 12px; border-radius: 50%;
  transform: translate(-50%, -50%);
  background: var(--accent, var(--bd-accent));
  border: 2px solid var(--bd-canvas);
  box-shadow: 0 0 0 1px var(--accent, var(--bd-accent)),
              0 0 12px 1px var(--accent, var(--bd-accent));
}
.bd-ribbon-scale {
  display: flex; justify-content: space-between; gap: 0.6rem;
  margin-top: 0.45rem; font-size: 0.66rem; color: var(--bd-muted);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}

/* ================= note callout ===================================== */
.bd-note {
  position: relative; overflow: hidden;
  background: var(--bd-glass);
  border: 1px solid var(--bd-glass-border);
  border-radius: var(--bd-radius-sm);
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
  padding: 0.9rem 1.1rem 0.9rem 1.25rem;
  color: var(--bd-text-soft);
  font-size: 0.87rem; line-height: 1.64;
  margin: 0.6rem 0 1.2rem 0;
  box-shadow: var(--bd-shadow);
}
.bd-note::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--bd-violet), var(--bd-cyan));
}
.bd-note strong { color: var(--bd-text); font-weight: 600; }

/* ================= insight cards ==================================== */
.bd-insight {
  position: relative; overflow: hidden;
  background: var(--bd-glass);
  border: 1px solid var(--bd-glass-border);
  border-radius: var(--bd-radius);
  backdrop-filter: var(--bd-blur);
  -webkit-backdrop-filter: var(--bd-blur);
  padding: 1rem 1.15rem 1rem 1.3rem;
  margin-bottom: 0.8rem;
  box-shadow: var(--bd-shadow), inset 0 1px 0 var(--bd-hairline);
  transition: box-shadow .25s var(--bd-ease), transform .25s var(--bd-ease);
}
.bd-insight::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--tone, var(--bd-accent));
  box-shadow: 0 0 16px 0 var(--tone, var(--bd-accent));
}
.bd-insight:hover {
  box-shadow: var(--bd-shadow-lift), inset 0 1px 0 var(--bd-hairline);
  transform: translateX(2px);
}
.bd-insight-kind {
  font-size: 0.64rem; font-weight: 700; letter-spacing: 0.11em;
  text-transform: uppercase; color: var(--tone, var(--bd-muted));
}
.bd-insight-head {
  font-size: 0.98rem; font-weight: 600; color: var(--bd-text);
  margin: 0.32rem 0 0.34rem; line-height: 1.38; letter-spacing: -0.014em;
}
.bd-insight-body {
  font-size: 0.87rem; line-height: 1.64; color: var(--bd-text-soft);
}
.bd-summary {
  position: relative; overflow: hidden;
  background: var(--bd-glass-strong);
  border: 1px solid var(--bd-glass-border);
  border-radius: var(--bd-radius);
  backdrop-filter: var(--bd-blur);
  -webkit-backdrop-filter: var(--bd-blur);
  padding: 1.2rem 1.35rem;
  font-size: 0.96rem; line-height: 1.68; color: var(--bd-text-soft);
  box-shadow: var(--bd-shadow), inset 0 1px 0 var(--bd-hairline);
}
.bd-summary::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--bd-violet), var(--bd-magenta) 45%,
              var(--bd-cyan));
}

/* ================= inline meta text ================================= */
.bd-meta { color: var(--bd-muted); font-size: 0.85rem; line-height: 1.5; }
.bd-meta-num {
  color: var(--bd-muted); font-size: 0.82rem; font-weight: 500;
  font-variant-numeric: tabular-nums;
}

/* ================= tag ============================================== */
.bd-tag {
  display: inline-block; font-size: 0.65rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  padding: 0.18rem 0.55rem; border-radius: 999px;
  border: 1px solid var(--bd-glass-border); background: var(--bd-glass);
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
  color: var(--bd-muted); margin-right: 0.35rem;
}

/* ================= sidebar ========================================== */
[data-testid="stSidebar"] {
  background: var(--bd-glass-strong) !important;
  backdrop-filter: blur(26px) saturate(170%);
  -webkit-backdrop-filter: blur(26px) saturate(170%);
  border-right: 1px solid var(--bd-glass-border) !important;
}
[data-testid="stSidebarContent"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarUserContent"] { background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.6rem; }
[data-testid="stSidebarNav"] { padding-top: 0.4rem; }
[data-testid="stSidebarNav"]::before {
  content: "Pages";
  display: block; padding: 0 0.75rem 0.4rem;
  font-size: 0.63rem; font-weight: 600; letter-spacing: 0.15em;
  text-transform: uppercase; color: var(--bd-muted);
}
[data-testid="stSidebarNavLink"] {
  border-radius: var(--bd-radius-sm);
  transition: background .2s var(--bd-ease), color .2s var(--bd-ease);
}
[data-testid="stSidebarNavLink"]:hover { background: var(--bd-accent-tint); }
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: var(--bd-accent-tint);
  box-shadow: inset 0 0 0 1px var(--bd-accent-line);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font-size: 0.98rem; }
.bd-side-label {
  font-size: 0.63rem; font-weight: 600; letter-spacing: 0.15em;
  text-transform: uppercase; color: var(--bd-muted);
  margin: 0.25rem 0 0.4rem 0;
}
.bd-brand {
  display: flex; align-items: center; gap: 0.7rem;
  padding: 0.15rem 0 1rem 0; margin-bottom: 0.9rem;
  border-bottom: 1px solid var(--bd-glass-border);
}
.bd-brand-mark {
  position: relative; flex: 0 0 auto; width: 38px; height: 38px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--bd-violet), var(--bd-magenta) 52%,
              var(--bd-cyan));
  color: #fff; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.02em;
  box-shadow: 0 6px 20px -6px var(--bd-violet),
              inset 0 1px 0 rgba(255,255,255,.45);
}
.bd-brand-name {
  font-size: 0.92rem; font-weight: 600; line-height: 1.26;
  color: var(--bd-text); letter-spacing: -0.014em;
}
.bd-brand-kicker {
  font-size: 0.62rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--bd-muted); margin-top: 0.16rem;
}
.bd-side-meta {
  display: flex; align-items: flex-start; gap: 0.5rem;
  margin-top: 1.4rem; padding-top: 0.9rem;
  border-top: 1px solid var(--bd-glass-border);
  font-size: 0.72rem; color: var(--bd-muted); line-height: 1.5;
}
.bd-side-meta .bd-dot {
  width: 6px; height: 6px; border-radius: 50%; margin-top: 0.36rem;
  background: var(--bd-pos); flex: 0 0 auto;
  box-shadow: 0 0 0 3px var(--bd-pos-tint), 0 0 10px 0 var(--bd-pos);
  animation: bd-pulse 2.6s ease-in-out infinite;
}

/* ================= data display ===================================== */
[data-testid="stDataFrame"] {
  font-variant-numeric: tabular-nums;
  border-radius: var(--bd-radius) !important;
  overflow: hidden;
  box-shadow: var(--bd-shadow);
}
[data-testid="stMetric"] { font-variant-numeric: tabular-nums; }

/* ================= tabs, expanders, controls ======================== */
[data-testid="stTabs"] [role="tablist"] {
  gap: 0.35rem; border-bottom: 1px solid var(--bd-glass-border);
  padding-bottom: 0.15rem;
}
[data-testid="stTab"] {
  color: var(--bd-muted); border-radius: var(--bd-radius-sm);
  padding-left: 0.75rem; padding-right: 0.75rem;
  transition: color .2s var(--bd-ease), background .2s var(--bd-ease);
}
[data-testid="stTab"]:hover { color: var(--bd-text); background: var(--bd-glass); }
[data-testid="stTab"][aria-selected="true"] {
  font-weight: 600; color: var(--bd-text); background: var(--bd-accent-tint);
}
[data-testid="stTabPanel"] { padding-top: 0.7rem; }
[data-testid="stExpander"] summary { font-weight: 500; }

/* buttons — the primary action carries the aurora gradient */
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"] {
  font-weight: 500;
  background: var(--bd-glass) !important;
  border: 1px solid var(--bd-glass-border) !important;
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
  transition: transform .2s var(--bd-ease), box-shadow .2s var(--bd-ease),
              border-color .2s var(--bd-ease);
}
[data-testid="stDownloadButton"] button:hover,
[data-testid="stBaseButton-secondary"]:hover {
  transform: translateY(-1px);
  border-color: var(--bd-accent-line) !important;
  box-shadow: 0 8px 24px -10px var(--bd-accent-glow);
}
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, var(--bd-violet), var(--bd-accent) 55%,
              var(--bd-cyan)) !important;
  border: none !important; color: #fff !important; font-weight: 600;
  box-shadow: 0 8px 24px -10px var(--bd-violet);
  transition: transform .2s var(--bd-ease), box-shadow .2s var(--bd-ease);
}
[data-testid="stBaseButton-primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 30px -10px var(--bd-violet);
}

/* inputs pick up the same frosted treatment */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stDateInput"] div[data-baseweb="input"],
[data-testid="stTextInput"] div[data-baseweb="input"] {
  background: var(--bd-glass) !important;
  border-color: var(--bd-glass-border) !important;
  backdrop-filter: var(--bd-blur-soft);
  -webkit-backdrop-filter: var(--bd-blur-soft);
}
[data-testid="stWidgetLabel"] p {
  font-size: 0.8rem; font-weight: 500; color: var(--bd-text-soft);
}

/* scrollbars, tuned to the canvas rather than the OS */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--bd-glass-border); border-radius: 999px;
  border: 2px solid transparent; background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: var(--bd-border-bold); }

/* respect a stated preference for stillness */
@media (prefers-reduced-motion: reduce) {
  [data-testid="stApp"]::before,
  .bd-eyebrow::before,
  .bd-side-meta .bd-dot { animation: none; }
  .bd-kpi, .bd-insight, [data-testid="stBaseButton-primary"],
  [data-testid="stBaseButton-secondary"] { transition: none; }
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
    css = _CSS.replace(_TOKEN_SLOT, _tokens(appearance())).replace("BD_GRAIN", _GRAIN)
    st.markdown(css, unsafe_allow_html=True)


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
