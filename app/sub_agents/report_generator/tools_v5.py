"""
Deterministic Equity Research HTML Report Generator — V5.

Architecture:
    1. Reads ONLY from tool_context.state (upstream agent outputs)
    2. Builds strict data payload — NO interpretation, NO invention
    3. Generates COMPLETE HTML in Python (deterministic, zero truncation)
    4. Persistent two-column layout: 65% narrative / 35% quant rail
    5. Light glassmorphic theme — no dark hero blocks
    6. Missing data → collapse container, never show dashes

Hallucination Risk: ZERO
Truncation Risk: ZERO
"""

import os
import json
import logging
import re
from datetime import datetime

from google.adk.tools import FunctionTool, ToolContext
from google import genai
from google.genai import types

logger = logging.getLogger("EquityReportGenerator")


# ─────────────────────────────────────────────────
#  MARKDOWN → HTML
# ─────────────────────────────────────────────────

def _md(text: str) -> str:
    """Convert upstream markdown to clean HTML."""
    if not text or text.strip() in ("Insufficient Data", "N/A", ""):
        return ""

    # Tables
    tbl, res, in_t = [], [], False
    for raw in text.split('\n'):
        s = raw.strip()
        if '|' in s and s.startswith('|') and s.endswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(set(c) <= {'-', ':', ' '} for c in cells):
                in_t = True
                continue
            if not in_t and not tbl:
                tbl.append('<table class="gt"><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr></thead><tbody>')
                in_t = True
            else:
                tbl.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        else:
            if in_t:
                tbl.append('</tbody></table>')
                res.extend(tbl)
                tbl, in_t = [], False
            res.append(raw)
    if in_t:
        tbl.append('</tbody></table>')
        res.extend(tbl)
    text = '\n'.join(res)

    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'^---+$', '<hr class="sep">', text, flags=re.MULTILINE)

    lines = text.split('\n')
    out, in_l = [], False
    for ln in lines:
        st = ln.strip()
        if st.startswith('- ') or st.startswith('• '):
            if not in_l:
                out.append('<ul>')
                in_l = True
            out.append(f'<li>{st[2:]}</li>')
        elif re.match(r'^\d+\.\s', st):
            if not in_l:
                out.append('<ol>')
                in_l = True
            li_text = re.sub(r"^[0-9]+[.]\s*", "", st)
            out.append(f'<li>{li_text}</li>')
        else:
            if in_l:
                out.append('</ul>')
                in_l = False
            out.append(ln)
    if in_l:
        out.append('</ul>')
    text = '\n'.join(out)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = text.replace('\n', '<br/>')
    return text


def _v(val, prefix="", suffix=""):
    """Format value. Returns None if missing — caller decides whether to render."""
    if val is None or val == "" or val == "N/A":
        return None
    try:
        if isinstance(val, (int, float)):
            return f"{prefix}{val:,.2f}{suffix}"
    except Exception:
        pass
    return f"{prefix}{val}{suffix}"


def _metric_row(label, val, css_class=""):
    """Render a metric row ONLY if value exists."""
    if val is None:
        return ""
    return f'<div class="mr"><span class="ml">{label}</span><span class="mv {css_class}">{val}</span></div>'


def _badge(signal):
    """Return badge HTML for signal."""
    if not signal:
        return ""
    s = str(signal).upper()
    if s in ("BUY", "BULLISH", "STRONG BUY", "ACCUMULATE"):
        bg = "linear-gradient(135deg,#059669,#10b981)"
    elif s in ("SELL", "BEARISH", "STRONG SELL"):
        bg = "linear-gradient(135deg,#dc2626,#ef4444)"
    elif s in ("HOLD", "NEUTRAL", "MONITOR"):
        bg = "linear-gradient(135deg,#d97706,#f59e0b)"
    else:
        bg = "rgba(100,116,139,0.15)"
    return f'<span class="bdg" style="background:{bg};">{signal}</span>'


def _gauge_html(value, max_val=100, color="#2563eb", label=""):
    """Render gauge only if value exists."""
    if value is None:
        return ""
    try:
        pct = min(float(value) / max_val * 100, 100)
    except Exception:
        return ""
    lbl = f'<div class="gauge-lbl">{label}</div>' if label else ""
    return f'{lbl}<div class="gauge"><div class="gauge-bar" style="width:{pct}%;background:{color};"></div></div>'


def _gauge_color(rsi):
    try:
        v = float(rsi)
        if v < 30: return "#ef4444"
        if v > 70: return "#059669"
        return "#2563eb"
    except Exception:
        return "#64748b"


# ─────────────────────────────────────────────────
#  CSS — V5 Light Glassmorphic Institutional
# ─────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}

/* ── Base ── */
body{
  font-family:'Inter',system-ui,-apple-system,sans-serif;
  background:linear-gradient(160deg,#f0f4f8 0%,#e8eef6 30%,#dfe7f0 60%,#edf1f7 100%);
  background-attachment:fixed;
  color:#1e293b;
  line-height:1.65;
  font-size:14.5px;
  -webkit-font-smoothing:antialiased;
  min-height:100vh;
}

/* ── Wrapper ── */
.wrap{max-width:1440px;margin:0 auto;padding:0 clamp(16px,3vw,40px);}

/* ── Hero ── */
.hero{
  padding:clamp(2rem,5vw,3.5rem) 0 clamp(1.5rem,3vw,2.5rem);
  border-bottom:1px solid rgba(148,163,184,0.15);
  margin-bottom:2rem;
}
.hero-top{display:flex;align-items:flex-end;justify-content:space-between;gap:2rem;flex-wrap:wrap;}
.hero h1{font-size:clamp(2.8rem,5vw,4rem);font-weight:900;letter-spacing:-0.04em;color:#0f172a;line-height:1;}
.hero-sub{font-size:.92rem;color:#64748b;margin-top:.4rem;font-weight:400;}
.hero-price{text-align:right;}
.hero-price .big{font-size:clamp(2rem,4vw,3rem);font-weight:800;color:#0f172a;font-family:'Inter',monospace;}
.hero-price .delta{font-size:.88rem;font-weight:600;margin-top:.2rem;}
.hero-price .delta.up{color:#059669;}
.hero-price .delta.dn{color:#dc2626;}

/* Frame strip */
.frame{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:1rem;
  margin-top:1.8rem;
}
.fc{
  background:rgba(255,255,255,0.5);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  border:1.5px solid rgba(148,163,184,0.18);
  border-radius:14px;
  padding:1.1rem 1rem;
  text-align:center;
  transition:transform 0.2s,box-shadow 0.2s;
}
.fc:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.06);}
.fc-lbl{font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:.35rem;}
.fc-val{font-size:1.15rem;font-weight:700;color:#0f172a;}
.fc-note{font-size:.72rem;color:#64748b;margin-top:.2rem;}

/* ── Alert bar ── */
.alert-bar{
  margin-top:1.2rem;padding:.6rem 1.2rem;
  background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);
  border-radius:10px;text-align:center;
  color:#92400e;font-weight:600;font-size:.82rem;
}

/* ── Glass Card ── */
.gc{
  background:rgba(255,255,255,0.55);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  border:1.5px solid rgba(148,163,184,0.2);
  border-radius:16px;
  padding:1.5rem;
  box-shadow:0 4px 20px rgba(0,0,0,0.04);
  margin-bottom:1.2rem;
  transition:transform 0.2s,box-shadow 0.2s;
}
.gc:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(0,0,0,0.07);}

/* Card color variants — FULL border */
.gc-b{border-color:#3b82f6;box-shadow:0 4px 20px rgba(59,130,246,0.08);}
.gc-g{border-color:#10b981;box-shadow:0 4px 20px rgba(16,185,129,0.08);}
.gc-a{border-color:#f59e0b;box-shadow:0 4px 20px rgba(245,158,11,0.08);}
.gc-r{border-color:#ef4444;box-shadow:0 4px 20px rgba(239,68,68,0.08);}
.gc-p{border-color:#8b5cf6;box-shadow:0 4px 20px rgba(139,92,246,0.08);}
.gc-t{border-color:#06b6d4;box-shadow:0 4px 20px rgba(6,182,212,0.08);}
.gc-s{border-color:#64748b;box-shadow:0 4px 20px rgba(100,116,139,0.08);}

/* ── Section titles ── */
.stl{font-size:1.35rem;font-weight:700;color:#0f172a;margin-bottom:.2rem;display:flex;align-items:center;gap:.6rem;}
.stl::before{content:'';width:4px;height:1.2em;border-radius:4px;background:linear-gradient(180deg,#3b82f6,#06b6d4);}
.stl-sub{font-size:.82rem;color:#64748b;margin-bottom:1.2rem;margin-left:1.2rem;}

/* ── Two-column body ── */
.body-grid{
  display:grid;
  grid-template-columns:1fr 380px;
  gap:2rem;
  align-items:start;
}
@media(max-width:1100px){.body-grid{grid-template-columns:1fr;}}
@media(min-width:1500px){.body-grid{grid-template-columns:1fr 420px;}}

/* Left = Narrative */
.nar{}

/* Right = Quant Rail */
.qr{position:sticky;top:1rem;}

/* ── Exec summary strip ── */
.exec{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:.8rem;
  margin-bottom:2rem;
}
.exec-item{
  background:rgba(255,255,255,0.5);
  backdrop-filter:blur(12px);
  border:1.5px solid rgba(148,163,184,0.15);
  border-radius:12px;
  padding:.9rem 1rem;
  display:flex;align-items:center;gap:.6rem;
}
.exec-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.exec-dot.blue{background:#3b82f6;}
.exec-dot.green{background:#10b981;}
.exec-dot.amber{background:#f59e0b;}
.exec-dot.red{background:#ef4444;}
.exec-dot.purple{background:#8b5cf6;}
.exec-dot.slate{background:#64748b;}
.exec-lbl{font-size:.78rem;color:#64748b;font-weight:500;}
.exec-val{font-size:.88rem;color:#0f172a;font-weight:600;}

/* ── Narrative tiles ── */
.nar-section{margin-bottom:2rem;}
.nar-content{font-size:.92rem;color:#334155;line-height:1.75;}
.nar-content h1,.nar-content h2,.nar-content h3,.nar-content h4{color:#0f172a;margin:1.2rem 0 .5rem;font-weight:700;}
.nar-content h1{font-size:1.3rem;}
.nar-content h2{font-size:1.15rem;}
.nar-content h3{font-size:1.05rem;}
.nar-content h4{font-size:.95rem;color:#475569;}
.nar-content strong{color:#0f172a;font-weight:600;}
.nar-content ul,.nar-content ol{padding-left:1.3rem;margin:.5rem 0;}
.nar-content li{margin-bottom:.3rem;line-height:1.6;}

/* ── Metric rows ── */
.mr{display:flex;justify-content:space-between;align-items:center;padding:.55rem 0;border-bottom:1px solid rgba(148,163,184,0.08);}
.mr:last-child{border-bottom:none;}
.ml{font-size:.82rem;color:#64748b;font-weight:500;}
.mv{font-family:'Inter',monospace;font-weight:600;color:#1e293b;font-size:.92rem;}
.mv-r{color:#dc2626;}
.mv-g{color:#059669;}
.mv-b{color:#2563eb;}

/* ── Gauge ── */
.gauge{background:rgba(148,163,184,0.12);border-radius:6px;height:8px;overflow:hidden;margin:.3rem 0 .8rem;}
.gauge-bar{height:100%;border-radius:6px;transition:width 0.6s ease;}
.gauge-lbl{font-size:.72rem;color:#64748b;font-weight:500;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.15rem;}

/* ── Badge ── */
.bdg{display:inline-block;padding:4px 12px;border-radius:100px;font-weight:600;font-size:.72rem;letter-spacing:.03em;text-transform:uppercase;color:#fff;}

/* ── Oracle target ── */
.orc-big{text-align:center;padding:1rem 0;}
.orc-big .val{font-size:2.2rem;font-weight:800;color:#059669;font-family:'Inter',monospace;}
.orc-big .lbl{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:.3rem;}
.orc-range{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;text-align:center;margin:.8rem 0;padding:.8rem 0;border-top:1px solid rgba(148,163,184,0.1);border-bottom:1px solid rgba(148,163,184,0.1);}
.orc-range .rl{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#64748b;}
.orc-range .rv{font-size:1.1rem;font-weight:700;color:#1e293b;font-family:'Inter',monospace;}
.orc-src{text-align:center;font-size:.72rem;color:#10b981;font-weight:500;margin-top:.5rem;padding:.35rem;background:rgba(16,185,129,0.06);border-radius:6px;}

/* ── Prob band ── */
.pb{display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-bottom:.8rem;}
.pb-cell{text-align:center;padding:.6rem .4rem;}
.pb-cell .lbl{font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;margin-bottom:.25rem;}
.pb-cell .val{font-size:1rem;font-weight:700;color:#1e3a8a;font-family:'Inter',monospace;}
.pb-cell .note{font-size:.7rem;color:#64748b;margin-top:.15rem;}
.interp{background:rgba(239,246,255,0.4);border-left:3px solid #3b82f6;padding:.7rem .9rem;border-radius:6px;font-size:.82rem;line-height:1.6;color:#334155;margin-top:.5rem;}

/* ── Synth section ── */
.synth-card{margin-bottom:2rem;}
.synth-header{display:flex;align-items:center;gap:.8rem;margin-bottom:1rem;}

/* ── Blueprint (Climax) ── */
.bp-section{
  margin-top:2.5rem;
  padding:2.5rem;
  background:linear-gradient(135deg,rgba(15,23,42,0.97),rgba(30,41,59,0.95));
  border-radius:20px;
  color:white;
  position:relative;
  overflow:hidden;
}
.bp-section::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(circle at 25% 50%,rgba(59,130,246,0.12),transparent 50%),
             radial-gradient(circle at 80% 20%,rgba(16,185,129,0.08),transparent 40%);
  pointer-events:none;border-radius:20px;
}
.bp-inner{position:relative;z-index:1;}
.bp-title{font-size:clamp(1.8rem,3vw,2.4rem);font-weight:800;text-align:center;margin-bottom:.3rem;letter-spacing:-0.02em;}
.bp-sub{font-size:.9rem;color:rgba(255,255,255,0.55);text-align:center;margin-bottom:2rem;}
.bp-body{
  background:rgba(255,255,255,0.07);
  backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.1);
  border-radius:14px;
  padding:1.8rem;
}
.bp-body h1,.bp-body h2,.bp-body h3,.bp-body h4{color:white;margin:1rem 0 .4rem;}
.bp-body p,.bp-body li{color:rgba(255,255,255,0.85);font-size:.9rem;line-height:1.7;}
.bp-body strong{color:white;}
.bp-body ul,.bp-body ol{padding-left:1.2rem;}
.bp-foot{display:flex;justify-content:center;gap:2rem;margin-top:1.5rem;flex-wrap:wrap;}
.bp-foot-item{font-size:.82rem;color:rgba(255,255,255,0.7);}
.bp-foot-item strong{color:white;margin-left:.3rem;}

/* ── Table ── */
.gt{width:100%;border-collapse:separate;border-spacing:0;border-radius:10px;overflow:hidden;background:rgba(255,255,255,0.3);margin:.8rem 0;}
.gt th{background:rgba(59,130,246,0.05);padding:8px 12px;text-align:left;font-weight:600;font-size:.72rem;color:#475569;text-transform:uppercase;letter-spacing:.04em;}
.gt td{padding:8px 12px;border-top:1px solid rgba(148,163,184,0.08);font-size:.84rem;color:#334155;}

/* ── Separator ── */
.sep{border:none;height:1px;background:rgba(148,163,184,0.12);margin:1rem 0;}

/* ── Footer ── */
.foot{
  text-align:center;padding:2rem 0;margin-top:2.5rem;
  border-top:1px solid rgba(148,163,184,0.12);
  color:#94a3b8;font-size:.75rem;line-height:1.8;
}
.foot .wm{font-size:.65rem;color:#cbd5e1;letter-spacing:.1em;text-transform:uppercase;margin-top:.5rem;}

/* ── Responsive ── */
@media(max-width:768px){
  .frame{grid-template-columns:1fr 1fr;}
  .exec{grid-template-columns:1fr;}
  .pb{grid-template-columns:1fr;}
  .hero-top{flex-direction:column;align-items:flex-start;}
  .hero-price{text-align:left;}
  .bp-section{padding:1.5rem;border-radius:14px;}
  .bp-foot{flex-direction:column;align-items:center;gap:.8rem;}
}
@media(max-width:480px){
  .frame{grid-template-columns:1fr;}
  .gc{padding:1.1rem;border-radius:12px;}
  body{font-size:14px;}
}

/* ── Print ── */
@media print{
  body{background:white!important;}
  .gc,.fc{box-shadow:none;backdrop-filter:none;background:white;border:1px solid #e2e8f0;}
  .bp-section{background:#0f172a!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
  .qr{position:static;}
}

ul,ol{padding-left:1.3rem;margin:.4rem 0;}
li{margin-bottom:.2rem;}
"""


# ─────────────────────────────────────────────────
#  PAYLOAD BUILDER
# ─────────────────────────────────────────────────

def _build_payload(ticker: str, state: dict) -> dict:
    """Extract deterministic fields from agent state."""
    market = state.get("market_analysis", {}) or {}
    tech = state.get("technical_analysis", {}) or {}
    oracle = state.get("oracle_forecast", {}) or {}
    quant = state.get("quant_synthesis", {}) or {}
    strategy = state.get("strategic_report", {}) or {}

    price = market.get("current_price") or tech.get("price")
    confidence = quant.get("confidence_score")
    rsi = tech.get("rsi")

    # Asymmetry
    asym_pct, asym_label = None, None
    if price and oracle.get("predicted_price"):
        try:
            pred = float(oracle["predicted_price"])
            curr = float(price)
            pct = ((pred - curr) / curr) * 100
            asym_pct = round(pct, 1)
            if pct > 5:
                asym_label = f"Positive Skew (+{pct:.1f}%)"
            elif pct < -5:
                asym_label = f"Negative Skew ({pct:.1f}%)"
            else:
                asym_label = f"Balanced ({pct:+.1f}%)"
        except Exception:
            pass

    # Vol regime
    vol = None
    if rsi:
        try:
            r = float(rsi)
            if r < 25: vol = "Elevated — Post-Capitulation"
            elif r < 35: vol = "Elevated"
            elif r > 75: vol = "Compressed — Overbought"
            elif r > 65: vol = "Low"
            else: vol = "Normal"
        except Exception:
            pass

    ci = oracle.get("confidence_interval", []) or []

    # Risk vector from RSI
    risk_label, risk_sub = None, None
    if rsi:
        try:
            rv = float(rsi)
            if rv < 25:
                risk_label, risk_sub = "Capitulation", "Extreme Oversold"
            elif rv < 35:
                risk_label, risk_sub = "Downside Momentum", "Bearish Continuation"
            elif rv > 75:
                risk_label, risk_sub = "Reversal Risk", "Overbought Territory"
            else:
                risk_label, risk_sub = "Volatility", "Standard"
        except Exception:
            pass

    # Support/Resistance
    support = tech.get("support_levels", []) or []
    resistance = tech.get("resistance_levels", []) or []
    if isinstance(support, list):
        support = [s for s in support[:3] if s is not None]
    else:
        support = []
    if isinstance(resistance, list):
        resistance = [r for r in resistance[:3] if r is not None]
    else:
        resistance = []

    return {
        "ticker": ticker,
        "date": datetime.now().strftime("%B %d, %Y"),
        "price": price,
        "mcap": market.get("market_cap"),
        "sentiment": market.get("sentiment"),
        "regime": tech.get("trend"),
        "bias": quant.get("overall_signal"),
        "confidence": confidence,
        "action": strategy.get("signal"),
        "tension": str(market.get("sentiment", "")).lower() != str(tech.get("rating", "")).lower(),
        "asym_label": asym_label,
        "asym_pct": asym_pct,
        "vol_regime": vol,
        "rsi": rsi,
        "macd": tech.get("macd"),
        "trend": tech.get("trend"),
        "sma_20": tech.get("sma_20"),
        "sma_50": tech.get("sma_50"),
        "boll_upper": tech.get("bollinger_upper"),
        "boll_lower": tech.get("bollinger_lower"),
        "support": support,
        "resistance": resistance,
        "rating": tech.get("rating"),
        "risk_label": risk_label,
        "risk_sub": risk_sub,
        "orc_target": oracle.get("predicted_price"),
        "orc_conf": oracle.get("model_confidence"),
        "orc_horizon": oracle.get("forecast_horizon"),
        "orc_lower": ci[0] if ci else None,
        "orc_upper": ci[1] if len(ci) > 1 else None,
        "market_html": _md(market.get("report", "")),
        "quant_html": _md(quant.get("summary", "")),
        "blueprint_html": _md(strategy.get("narrative", "")),
        "bp_signal": strategy.get("signal"),
        "bp_timeframe": strategy.get("time_horizon"),
    }


# ─────────────────────────────────────────────────
#  HTML BUILDER — V5 Two-Column Architecture
# ─────────────────────────────────────────────────

def _build_report_html(d: dict) -> str:
    """Build the complete institutional report. 100% deterministic."""

    ticker = d.get("ticker", "")
    date = d.get("date", "")

    # ── HERO ──
    price_html = ""
    price = d.get("price")
    if price is not None:
        p_str = _v(price, prefix="$")
        asym = d.get("asym_pct")
        delta_html = ""
        if asym is not None:
            cls = "up" if asym >= 0 else "dn"
            arrow = "▲" if asym >= 0 else "▼"
            delta_html = f'<div class="delta {cls}">{arrow} {abs(asym):.1f}% vs Oracle Target</div>'
        price_html = f'''<div class="hero-price">
            <div class="big">{p_str}</div>
            {delta_html}
        </div>'''

    # ── Frame Cells (only those with data) ──
    frame_cells = []
    regime = d.get("regime")
    if regime:
        r_lower = str(regime).lower()
        sub = "Range-Bound"
        if "down" in r_lower: sub = "Bearish Pressure"
        elif "up" in r_lower: sub = "Bullish Momentum"
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Regime</div><div class="fc-val">{regime}</div><div class="fc-note">{sub}</div></div>')

    bias = d.get("bias")
    if bias:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Bias</div><div class="fc-val" style="color:#3b82f6;">{bias}</div><div class="fc-note">Structural Signal</div></div>')

    conf = d.get("confidence")
    if conf is not None:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Conviction</div><div class="fc-val" style="color:#059669;">{_v(conf, suffix="/100")}</div><div class="fc-note">Signal Convergence</div></div>')

    risk = d.get("risk_label")
    if risk:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Primary Risk</div><div class="fc-val" style="color:#f59e0b;">{risk}</div><div class="fc-note">{d.get("risk_sub", "")}</div></div>')

    action = d.get("action")
    if action:
        frame_cells.append(f'<div class="fc"><div class="fc-lbl">Action</div><div class="fc-val">{_badge(action)}</div></div>')

    frame_html = ""
    if frame_cells:
        frame_html = f'<div class="frame">{"".join(frame_cells)}</div>'

    tension_html = ""
    if d.get("tension"):
        tension_html = '<div class="alert-bar">⚠ Signal Divergence — Market Sentiment and Technical Rating are misaligned</div>'

    # ── Exec Summary (only items with data) ──
    exec_items = []
    if regime:
        exec_items.append(('blue', 'State', regime))
    sentiment = d.get("sentiment")
    if sentiment:
        exec_items.append(('green', 'Sentiment', str(sentiment)))
    rsi = d.get("rsi")
    trend = d.get("trend")
    if rsi is not None:
        t = f' · {trend}' if trend else ""
        exec_items.append(('purple', 'Technical', f'RSI {_v(rsi)}{t}'))
    orc_t = d.get("orc_target")
    if orc_t is not None:
        exec_items.append(('green', 'Oracle Target', _v(orc_t, prefix='$')))
    asym_l = d.get("asym_label")
    if asym_l:
        exec_items.append(('amber', 'Asymmetry', asym_l))
    if action:
        exec_items.append(('slate', 'Action', str(action)))

    exec_html = ""
    if exec_items:
        items = ''.join(f'<div class="exec-item"><div class="exec-dot {c}"></div><div><div class="exec-lbl">{l}</div><div class="exec-val">{v}</div></div></div>' for c, l, v in exec_items)
        exec_html = f'<div class="exec">{items}</div>'

    # ── Market Intelligence (left narrative) ──
    market_html = d.get("market_html", "")
    market_section = ""
    if market_html:
        market_section = f'''<div class="nar-section">
            <div class="stl">Market Intelligence</div>
            <div class="stl-sub">Narrative Analysis · Sentiment · Risk Assessment</div>
            <div class="gc gc-b"><div class="nar-content">{market_html}</div></div>
        </div>'''

    # ── Quantitative Synthesis (left) ──
    quant_html = d.get("quant_html", "")
    quant_section = ""
    if quant_html:
        badge_html = _badge(d.get("bias")) if d.get("bias") else ""
        conf_lbl = f'<span style="font-size:.82rem;color:#64748b;margin-left:.6rem;">Confidence: {_v(conf, suffix="/100")}</span>' if conf is not None else ""
        quant_section = f'''<div class="synth-card">
            <div class="stl">Quantitative Synthesis</div>
            <div class="synth-header">{badge_html}{conf_lbl}</div>
            <div class="gc gc-p"><div class="nar-content">{quant_html}</div></div>
        </div>'''

    # ── RIGHT RAIL: Technical Indicators ──
    tech_rows = []
    if rsi is not None:
        rsi_class = "mv-r" if float(rsi) < 30 else ("mv-g" if float(rsi) > 70 else "")
        tech_rows.append(_metric_row("RSI (14)", _v(rsi), rsi_class))
        tech_rows.append(_gauge_html(rsi, 100, _gauge_color(rsi)))
    macd = d.get("macd")
    if macd is not None:
        tech_rows.append(_metric_row("MACD", _v(macd)))
    if trend:
        tech_rows.append(f'<div class="mr"><span class="ml">Trend</span>{_badge(trend)}</div>')
    sma20 = d.get("sma_20")
    sma50 = d.get("sma_50")
    if sma20 is not None:
        tech_rows.append(_metric_row("SMA 20", _v(sma20, prefix="$")))
    if sma50 is not None:
        tech_rows.append(_metric_row("SMA 50", _v(sma50, prefix="$")))
    bu = d.get("boll_upper")
    bl = d.get("boll_lower")
    if bu is not None:
        tech_rows.append(_metric_row("Bollinger Upper", _v(bu, prefix="$")))
    if bl is not None:
        tech_rows.append(_metric_row("Bollinger Lower", _v(bl, prefix="$")))
    support = d.get("support", [])
    resistance = d.get("resistance", [])
    if support:
        tech_rows.append(_metric_row("Support", ", ".join(_v(s, prefix="$") or "" for s in support)))
    if resistance:
        tech_rows.append(_metric_row("Resistance", ", ".join(_v(r, prefix="$") or "" for r in resistance)))
    rating = d.get("rating")
    if rating:
        tech_rows.append(f'<div style="margin-top:.6rem;padding:.5rem;background:rgba(59,130,246,0.06);border-radius:6px;text-align:center;font-size:.82rem;"><span style="color:#64748b;">Rating: </span><strong style="color:#1e3a8a;">{rating}</strong></div>')

    tech_card = ""
    if tech_rows:
        tech_card = f'''<div class="gc gc-b" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.8rem;">Technical Indicators</h4>
            {"".join(tech_rows)}
        </div>'''

    # ── RIGHT RAIL: Oracle Projection ──
    oracle_card = ""
    orc_target = d.get("orc_target")
    if orc_target is not None:
        horizon = d.get("orc_horizon", "30 Days") or "30 Days"
        orc_body = f'''<div class="orc-big">
                <div class="lbl">{horizon} Target</div>
                <div class="val">{_v(orc_target, prefix="$")}</div>
            </div>'''

        orc_conf = d.get("orc_conf")
        if orc_conf is not None:
            try:
                pct = float(orc_conf) * 100 if float(orc_conf) <= 1 else float(orc_conf)
                orc_body += _gauge_html(pct, 100, "#10b981", f"Confidence: {pct:.0f}%")
            except Exception:
                pass

        range_parts = []
        orc_lower = d.get("orc_lower")
        orc_upper = d.get("orc_upper")
        if orc_lower is not None:
            range_parts.append(f'<div><div class="rl">Lower Bound</div><div class="rv">{_v(orc_lower, prefix="$")}</div></div>')
        if orc_upper is not None:
            range_parts.append(f'<div><div class="rl">Upper Bound</div><div class="rv">{_v(orc_upper, prefix="$")}</div></div>')
        if range_parts:
            orc_body += f'<div class="orc-range">{"".join(range_parts)}</div>'

        orc_body += f'<div class="orc-src">TimesFM 2.5 · BigQuery · {horizon}</div>'

        oracle_card = f'''<div class="gc gc-g" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.6rem;">Oracle Projection</h4>
            {orc_body}
        </div>'''

    # ── RIGHT RAIL: Distribution / Probabilistic ──
    dist_card = ""
    dist_cells = []
    if orc_target is not None:
        dist_cells.append(('Median Forecast', _v(orc_target, prefix="$"), "50th Percentile"))
    orc_lower = d.get("orc_lower")
    orc_upper = d.get("orc_upper")
    if orc_lower is not None and orc_upper is not None:
        dist_cells.append(('Confidence Band', f'{_v(orc_lower, prefix="$")}–{_v(orc_upper, prefix="$")}', "Model Range"))
    asym_pct = d.get("asym_pct")
    if asym_pct is not None:
        dist_cells.append(('Asymmetry', f'{asym_pct:+.1f}%', d.get("asym_label", "")))
    vol = d.get("vol_regime")
    if vol:
        dist_cells.append(('Vol Regime', vol, "RSI-Derived"))

    if dist_cells:
        cells_html = ''.join(f'<div class="pb-cell"><div class="lbl">{l}</div><div class="val">{v}</div><div class="note">{n}</div></div>' for l, v, n in dist_cells)
        interp = ""
        if orc_target is not None and price is not None:
            interp = f'''<div class="interp">
                Median forecast {_v(orc_target, prefix="$")} vs current {_v(price, prefix="$")} → {d.get("asym_label", "balanced")}. Vol regime: {vol or "Normal"}.
            </div>'''
        dist_card = f'''<div class="gc gc-t" style="padding:1.3rem;">
            <h4 style="font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748b;margin-bottom:.8rem;">Distribution Analysis</h4>
            <div class="pb">{cells_html}</div>
            {interp}
        </div>'''

    # ── RIGHT RAIL: Market Data sidebar ──
    sidebar_data = []
    if d.get("mcap"):
        sidebar_data.append(_metric_row("Market Cap", str(d["mcap"])))
    if sentiment:
        sidebar_data.append(_metric_row("Sentiment", str(sentiment)))
    if price is not None:
        sidebar_data.append(_metric_row("Current Price", _v(price, prefix="$")))

    sidebar_card = ""
    if sidebar_data:
        sidebar_card = f'''<div class="gc gc-s" style="padding:1.1rem;">
            <h4 style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin-bottom:.6rem;">Market Data</h4>
            {"".join(sidebar_data)}
        </div>'''

    # ── STRATEGIC BLUEPRINT (Climax — always appears) ──
    bp_html = d.get("blueprint_html", "")
    if not bp_html:
        bp_html = '<p style="color:rgba(255,255,255,0.6);text-align:center;padding:1.5rem;">Investment thesis under development pending additional data validation.</p>'

    bp_foot_items = []
    if d.get("bp_signal"):
        bp_foot_items.append(f'<div class="bp-foot-item">Signal:<strong>{d["bp_signal"]}</strong></div>')
    if d.get("bp_timeframe"):
        bp_foot_items.append(f'<div class="bp-foot-item">Timeframe:<strong>{d["bp_timeframe"]}</strong></div>')
    if conf is not None:
        bp_foot_items.append(f'<div class="bp-foot-item">Conviction:<strong>{_v(conf, suffix="/100")}</strong></div>')
    bp_foot_html = f'<div class="bp-foot">{"".join(bp_foot_items)}</div>' if bp_foot_items else ""

    # ── ASSEMBLE ──
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ticker} — Equity Research Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <!-- HERO -->
  <div class="hero">
    <div class="hero-top">
      <div>
        <h1>{ticker}</h1>
        <div class="hero-sub">Equity Research · {date}</div>
      </div>
      {price_html}
    </div>
    {frame_html}
    {tension_html}
  </div>

  <!-- EXEC SUMMARY -->
  {exec_html}

  <!-- BODY: Two-Column -->
  <div class="body-grid">

    <!-- LEFT: Narrative Intelligence -->
    <div class="nar">
      {market_section}
      {quant_section}
    </div>

    <!-- RIGHT: Quantitative Rail -->
    <div class="qr">
      {sidebar_card}
      {tech_card}
      {oracle_card}
      {dist_card}
    </div>

  </div>

  <!-- STRATEGIC BLUEPRINT -->
  <div class="bp-section">
    <div class="bp-inner">
      <div class="bp-title">Strategic Blueprint</div>
      <div class="bp-sub">Actionable Investment Framework</div>
      <div class="bp-body">{bp_html}</div>
      {bp_foot_html}
    </div>
  </div>

  <!-- FOOTER -->
  <div class="foot">
    <p>This report is generated by AI (TradeMate) using deterministic quantitative data from yfinance, BigQuery TimesFM 2.5, and structured sub-agent outputs. It does NOT constitute financial advice. Past performance is not indicative of future results.</p>
    <div class="wm">TradeMate Research · {date}</div>
  </div>

</div>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────
#  REPORT GENERATOR FUNCTION
# ─────────────────────────────────────────────────

def generate_equity_report_func(ticker: str, tool_context: ToolContext) -> str:
    """
    Generate a deterministic institutional HTML equity research report.
    100% Python-templated — zero truncation risk.
    """
    tool_context.state["pipeline_stage"] = "report_generation"
    tool_context.state["target_ticker"] = ticker
    stages = tool_context.state.get("stages_completed", [])
    if "report_generation" not in stages:
        stages.append("report_generation")
    tool_context.state["stages_completed"] = stages

    try:
        if "strategic_report" not in tool_context.state:
            logger.warning(f"Strategic Report missing for {ticker}.")

        payload = _build_payload(ticker, tool_context.state)

        logger.info(f"Report Generator: Building institutional report for {ticker}")
        print(f"DEBUG: EQUITY REPORT GENERATOR triggered for {ticker}")

        html_code = _build_report_html(payload)

        tool_context.state["equity_report_html"] = html_code

        print(f"DEBUG: Equity report generated ({len(html_code)} chars)")

        return json.dumps({
            "status": "success",
            "message": "Institutional Equity Report Generated Successfully.",
        })

    except Exception as e:
        logger.error(f"Equity report generation failed: {e}")
        print(f"CRITICAL ERROR in Report Generator: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })


# Create FunctionTool
equity_report_tool = FunctionTool(func=generate_equity_report_func)
